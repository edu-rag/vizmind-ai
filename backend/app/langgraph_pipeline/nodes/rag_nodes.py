# app/rag_pipeline/nodes.py
import asyncio
import json
from typing import List, Dict, Any

from app.core.config import settings, logger
from app.langgraph_pipeline.state import RAGGraphState  # Use the new RAG state

# Langchain components
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.documents import Document

from app.models.cmvs_models import DocumentSufficiencyGrade

# Only call LLM to grade if we have at least this many docs
MIN_DB_DOCS_FOR_LLM_GRADING = 1

# If LLM grade is True, but confidence is low, we might still opt for web search
CONFIDENCE_THRESHOLD_FOR_DB_ONLY = 0.6


class RAGNodes:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=settings.MODEL_NAME_FOR_EMBEDDING
        )
        self.llm = ChatGroq(
            temperature=0.1,
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )

        if settings.TAVILY_API_KEY:
            # Initialize Tavily with include_domains if you want to strictly limit it at the API call level
            # However, modifying the query with site: operators is often more flexible and powerful.
            # You can use both. `include_domains` acts as a filter on Tavily's side.
            self.web_search_tool = TavilySearchResults(
                max_results=5,  # Get a few more results to allow for potential post-filtering if needed
                # include_domains=settings.RAG_VERIFIED_DOMAINS # Option 1: Strict domain inclusion by Tavily
                # search_depth="advanced" # Option 2: Ask Tavily for more in-depth/academic results
            )
            logger.info("Tavily Web Search tool initialized.")
            # If RAG_VERIFIED_DOMAINS is empty, it won't filter by domain unless query is modified
        else:
            self.web_search_tool = None
            logger.warning(
                "TAVILY_API_KEY not set. Web search fallback will be disabled."
            )

        try:
            self.grading_llm = self.llm.with_structured_output(DocumentSufficiencyGrade)
            logger.info(
                "Grading LLM initialized with structured output for DocumentSufficiencyGrade."
            )
        except Exception as e:
            logger.warning(
                f"Failed to initialize LLM with structured output for grading: {e}. Will attempt fallback JSON parsing."
            )
            self.grading_llm = (
                self.llm
            )  # Fallback to regular LLM, will require manual parsing

        try:
            self.vector_store = MongoDBAtlasVectorSearch.from_connection_string(
                connection_string=settings.MONGODB_URI,
                db_name=settings.MONGODB_DATABASE_NAME,
                collection_name=settings.MONGODB_CHUNKS_COLLECTION,
                embedding=self.embedding_model,
                index_name=settings.MONGODB_ATLAS_VECTOR_SEARCH_INDEX_NAME,
                text_key="text",
                embedding_key="embedding",
                namespace=f"{settings.MONGODB_DATABASE_NAME}.{settings.MONGODB_CHUNKS_COLLECTION}",
            )
            logger.info("MongoDB Atlas Vector Store initialized for RAG.")
        except Exception as e:
            logger.error(
                f"Failed to initialize MongoDB Atlas Vector Store: {e}", exc_info=True
            )
            self.vector_store = None
            raise RuntimeError(
                f"RAG Pipeline: MongoDB Atlas Vector Store could not be initialized: {e}"
            )

    async def retrieve_from_mongodb(self, state: RAGGraphState) -> Dict[str, Any]:
        logger.info(
            f"RAG Node: Retrieving documents from MongoDB for question: '{state['question']}'"
        )
        if not self.vector_store:
            return {
                "db_documents": [],
                "error_message": "MongoDB Vector Store not available.",
            }

        try:
            retriever_filter = {
                "user_id": state["user_id"],
                "concept_map_id": state["concept_map_id"],
            }
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": state["top_k_retriever"],
                    "pre_filter": retriever_filter,
                },
            )
            # Retriever's ainvoke/invoke typically takes the query string directly
            db_docs = await retriever.ainvoke(state["question"])
            logger.info(f"Retrieved {len(db_docs)} documents from MongoDB.")
            return {"db_documents": db_docs, "error_message": None}
        except Exception as e:
            logger.error(f"Error retrieving from MongoDB: {e}", exc_info=True)
            return {"db_documents": [], "error_message": f"DB retrieval failed: {e}"}

    def _format_docs_for_llm(self, docs: List[Document], source_type: str) -> str:
        formatted = []
        for i, doc in enumerate(docs):
            metadata_info = ""
            if doc.metadata:
                if source_type == "db_chunk":
                    filename = doc.metadata.get(
                        "original_filename_source_pdf", "Unknown Document"
                    )
                    page = doc.metadata.get("page_number", "N/A")
                    metadata_info = (
                        f"(Source: {filename}, Page: {page}, ID: db_doc_{i})"
                    )
                elif source_type == "web_search":
                    title = doc.metadata.get("title", "Web Page")
                    url = doc.metadata.get(
                        "source", "Unknown URL"
                    )  # Tavily uses 'source' for URL
                    metadata_info = f"(Source: {title} - {url}, ID: web_doc_{i})"

            formatted.append(f"--- Document {metadata_info} ---\n{doc.page_content}")
        return "\n\n".join(formatted)

    async def generate_answer(self, state: RAGGraphState) -> Dict[str, Any]:
        logger.info("RAG Node: Generating answer.")
        question = state["question"]
        db_documents = state.get("db_documents", [])
        web_documents = state.get(
            "web_documents", []
        )  # Will be None if web search wasn't run

        context_parts = []
        all_source_docs_for_citation = []

        if db_documents:
            context_parts.append(self._format_docs_for_llm(db_documents, "db_chunk"))
            all_source_docs_for_citation.extend(db_documents)
        if web_documents:  # Only if web search was performed and yielded results
            context_parts.append(self._format_docs_for_llm(web_documents, "web_search"))
            all_source_docs_for_citation.extend(web_documents)

        if not context_parts:
            logger.warning("No context available (DB or Web) to generate answer.")
            return {
                "answer": "I could not find enough information to answer your question.",
                "cited_sources": [],
            }

        full_context = "\n\n".join(context_parts)

        template = """You are an AI assistant providing detailed explanations based on retrieved documents.
Your task is to answer the following question using ONLY the provided context.
Be comprehensive and clear. If the context is insufficient, clearly state that.
After your answer, list the IDs of the documents you primarily used from the context (e.g., "db_doc_0", "web_doc_1").

Context:
{context}

Question: {question}

Answer:
[Your answer here based ONLY on the context]

Sources Used:
[List document IDs here, e.g., "db_doc_0, web_doc_1"]
"""
        prompt = ChatPromptTemplate.from_template(template)

        chain = prompt | self.llm | StrOutputParser()

        try:
            llm_response_str = await chain.ainvoke(
                {"context": full_context, "question": question}
            )

            # Basic parsing of answer and sources (can be improved with more robust parsing or structured LLM output)
            answer_part = llm_response_str
            cited_ids_str = ""
            if "Sources Used:" in llm_response_str:
                parts = llm_response_str.split("Sources Used:", 1)
                answer_part = parts[0].strip()
                if len(parts) > 1:
                    cited_ids_str = parts[1].strip()

            # Map cited_ids_str back to actual document metadata
            cited_sources_details = []
            raw_cited_ids = [
                item.strip() for item in cited_ids_str.split(",") if item.strip()
            ]

            for doc_idx, doc in enumerate(all_source_docs_for_citation):
                doc_type = "db_chunk" if doc in db_documents else "web_search"
                # Construct the ID format used in _format_docs_for_llm
                # This needs a more reliable way to map. For now, we list all sources if LLM fails to specify.
                # A better way is to re-prompt LLM to pick from a numbered list of sources.
                # For simplicity, if LLM gives IDs, try to match. Otherwise, list all used sources.

                # This simplistic ID matching is prone to errors.
                # For now, let's just list all documents that were part of the context fed to LLM
                # and let the LLM's textual reference to "Sources Used" be the primary guide.
                # A more robust solution would involve a second LLM call to extract citations
                # or prompting the first LLM to output citations in a structured format.

            # Creating CitationSource objects from all_source_docs_for_citation
            for i, doc in enumerate(all_source_docs_for_citation):
                doc_is_from_db = any(
                    db_doc is doc for db_doc in db_documents
                )  # Check identity

                if doc_is_from_db:
                    source_type = "mongodb_chunk"
                    identifier = str(
                        doc.metadata.get("_id", f"db_doc_internal_{i}")
                    )  # Use mongo _id if available
                    title = doc.metadata.get(
                        "original_filename_source_pdf", "MongoDB Document"
                    )
                    page_num = doc.metadata.get("page_number")
                else:  # Assumed from web
                    source_type = "web_search"
                    identifier = doc.metadata.get(
                        "source", f"web_doc_internal_{i}"
                    )  # URL from Tavily
                    title = doc.metadata.get("title", "Web Page")
                    page_num = None

                cited_sources_details.append(
                    {
                        "type": source_type,
                        "identifier": identifier,
                        "title": title,
                        "page_number": page_num,
                        "snippet": doc.page_content[:200] + "...",  # Add a snippet
                    }
                )

            logger.info(f"Generated answer: {answer_part[:100]}...")
            return {"answer": answer_part, "cited_sources": cited_sources_details}

        except Exception as e:
            logger.error(f"Error during LLM answer generation: {e}", exc_info=True)
            return {"answer": "Error generating answer from LLM.", "cited_sources": []}
