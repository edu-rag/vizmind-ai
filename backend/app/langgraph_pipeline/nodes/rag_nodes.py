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

    def _format_docs_for_grading(self, docs: List[Document]) -> str:
        """Formats documents into a simple string for the grading LLM."""
        if not docs:
            return "No documents retrieved."
        return "\n\n---\n\n".join(
            [f"Document Content:\n{doc.page_content[:1000]}" for doc in docs]
        )  # Send snippets

    async def grade_db_retrieval(self, state: RAGGraphState) -> Dict[str, str]:
        logger.info("RAG Node: Grading MongoDB retrieval using LLM.")
        question = state["question"]
        db_documents = state.get("db_documents", [])

        if state.get("error_message"):  # If DB retrieval itself failed
            logger.warning(
                "Grading skipped due to prior DB retrieval error. Forcing web search."
            )
            return {"db_retrieval_status": "perform_web_search"}

        if not db_documents or len(db_documents) < MIN_DB_DOCS_FOR_LLM_GRADING:
            logger.info(
                f"Not enough documents ({len(db_documents)}) from DB for LLM grading or no documents retrieved. Proceeding to web search."
            )
            return {"db_retrieval_status": "perform_web_search"}

        formatted_docs_for_grading = self._format_docs_for_grading(db_documents)

        grading_prompt_template = """You are an expert relevance and sufficiency assessor.
Given the following Question and the retrieved Document Snippets, determine if the snippets ALONE are likely sufficient to provide a comprehensive and accurate answer to the Question.
Focus on whether the core aspects of the question can be addressed by the provided text.

Question: {question}

Document Snippets:
{document_snippets}

Based on this, assess the sufficiency. You MUST respond with ONLY a valid JSON object (no other text) matching this exact schema:
{{
  "is_sufficient": true or false,
  "reasoning": "Brief explanation here",
  "confidence_score": 0.85
}}

Important: Return ONLY the JSON object, nothing else. Do not include any markdown formatting or additional text."""
        prompt = ChatPromptTemplate.from_template(grading_prompt_template)

        try:
            # Use the grading_llm (which might be structured_llm or fallback)
            # Check if we have a structured output LLM by comparing with the base LLM
            if (
                hasattr(self, "grading_llm") and self.grading_llm is not self.llm
            ):  # Check if it's the structured one (different from base LLM)
                grading_chain = prompt | self.grading_llm
                grade_response: DocumentSufficiencyGrade = await grading_chain.ainvoke(
                    {
                        "question": question,
                        "document_snippets": formatted_docs_for_grading,
                    }
                )
                is_sufficient = grade_response.is_sufficient
                confidence = (
                    grade_response.confidence_score
                    if grade_response.confidence_score is not None
                    else 1.0
                )  # Default to high confidence if not provided
                logger.info(
                    f"LLM Grade: Sufficient: {is_sufficient}, Confidence: {confidence}, Reasoning: {grade_response.reasoning}"
                )

            else:  # Fallback to manual JSON parsing if structured output for grading_llm failed to init
                logger.warning(
                    "Using fallback LLM call for grading - attempting manual JSON parsing."
                )
                grading_chain = (
                    prompt | self.llm | StrOutputParser()
                )  # Regular LLM then parse string
                response_str = await grading_chain.ainvoke(
                    {
                        "question": question,
                        "document_snippets": formatted_docs_for_grading,
                    }
                )
                try:
                    # Log the raw response for debugging
                    logger.info(
                        f"Raw LLM response for manual parsing: '{response_str}'"
                    )

                    # Clean the response - remove any markdown formatting
                    cleaned_response = response_str.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = (
                            cleaned_response.replace("```json", "")
                            .replace("```", "")
                            .strip()
                        )
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response.replace("```", "").strip()

                    # Attempt to parse JSON from the cleaned string output
                    grade_data = json.loads(cleaned_response)
                    is_sufficient = grade_data.get("is_sufficient", False)
                    confidence = grade_data.get(
                        "confidence_score", 0.5
                    )  # Default confidence if not parsed
                    logger.info(
                        f"LLM Grade (manual parse): Sufficient: {is_sufficient}, Confidence: {confidence}, Response: {response_str[:100]}"
                    )
                except json.JSONDecodeError as json_e:
                    logger.error(
                        f"Failed to parse JSON grade from LLM: {json_e}. Raw response was: '{response_str}'. Defaulting to insufficient."
                    )
                    is_sufficient = False
                    confidence = 0.0  # Low confidence on parse failure

            # Decision logic
            if is_sufficient and confidence >= CONFIDENCE_THRESHOLD_FOR_DB_ONLY:
                logger.info(
                    "LLM graded DB documents as SUFFICIENT with high confidence."
                )
                return {"db_retrieval_status": "generate_from_db"}
            elif is_sufficient and confidence < CONFIDENCE_THRESHOLD_FOR_DB_ONLY:
                logger.info(
                    f"LLM graded DB documents as SUFFICIENT but with low confidence ({confidence}). Proceeding to web search for augmentation."
                )
                return {"db_retrieval_status": "perform_web_search"}
            else:  # Not sufficient
                logger.info(
                    "LLM graded DB documents as INSUFFICIENT. Proceeding to web search."
                )
                return {"db_retrieval_status": "perform_web_search"}

        except Exception as e:
            logger.error(f"Error during LLM grading: {e}", exc_info=True)
            logger.warning("Defaulting to web search due to grading error.")
            return {"db_retrieval_status": "perform_web_search"}  # Fallback on error

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

    async def perform_web_search(self, state: RAGGraphState) -> Dict[str, Any]:
        original_question = state["question"]
        logger.info(
            f"RAG Node: Performing targeted web search for question: '{original_question}'"
        )

        if not self.web_search_tool:
            logger.warning(
                "Web search tool (Tavily) not available. Skipping web search."
            )
            return {"web_documents": [], "error_message": state.get("error_message")}

        # Construct a query that guides Tavily to preferred domains
        if settings.RAG_VERIFIED_DOMAINS:
            domain_queries = " OR ".join(
                [f"site:{domain}" for domain in settings.RAG_VERIFIED_DOMAINS]
            )
            targeted_query = f"{original_question} ({domain_queries})"
            logger.info(f"Constructed targeted Tavily query: {targeted_query}")
        else:
            targeted_query = original_question
            logger.info(
                "No specific domains configured for web search, using original query."
            )

        web_docs = []
        try:
            # Invoke Tavily with the targeted query
            # If you also used include_domains in __init__, Tavily will try to respect both.
            search_results_list_of_dicts = await self.web_search_tool.ainvoke(
                targeted_query
            )

            if isinstance(search_results_list_of_dicts, list):
                for result in search_results_list_of_dicts:
                    # Optional: Add an explicit post-filtering step here if Tavily still returns unwanted domains
                    # current_url = result.get("url", "")
                    # if settings.RAG_VERIFIED_DOMAINS and not any(domain in current_url for domain in settings.RAG_VERIFIED_DOMAINS):
                    #     logger.debug(f"Post-filtering: Skipping URL not in verified domains: {current_url}")
                    #     continue

                    web_docs.append(
                        Document(
                            page_content=result.get("content", ""),
                            metadata={
                                "title": result.get("title", "Web Search Result"),
                                "source": result.get(
                                    "url", "Unknown URL"
                                ),  # Tavily uses 'url' as key for source URL
                                # Tavily might also provide 'score' or other metadata
                            },
                        )
                    )
            elif isinstance(
                search_results_list_of_dicts, str
            ):  # Fallback for unexpected string output
                web_docs.append(
                    Document(
                        page_content=search_results_list_of_dicts,
                        metadata={
                            "title": "Web Search Result",
                            "source": "Unknown URL",
                        },
                    )
                )

            logger.info(f"Targeted web search yielded {len(web_docs)} documents.")

        except Exception as e:
            logger.error(f"Error during targeted web search: {e}", exc_info=True)
            current_error = state.get("error_message")
            new_error = f"Targeted web search failed: {e}"
            return {
                "web_documents": [],
                "error_message": (
                    f"{current_error}. {new_error}" if current_error else new_error
                ),
            }

        return {"web_documents": web_docs, "error_message": state.get("error_message")}
