from app.langgraph_pipeline.builder.cmvs_builder import get_langgraph_app
from app.langgraph_pipeline.state import GraphState
from app.core.config import settings, logger
from app.models.cmvs_models import (
    NodeDetailResponse,
    CitationSource,
)

import uuid

from typing import List, Optional


# Langchain imports for RAG
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_huggingface import HuggingFaceEmbeddings  # Your chosen embedding model
from langchain_groq import ChatGroq  # Your chosen LLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    RunnableLambda,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document  # For typing source documents


# Initialize embedding model (ensure this is consistent with indexing)
try:
    embedding_model_instance = HuggingFaceEmbeddings(
        model_name=settings.MODEL_NAME_FOR_EMBEDDING,
    )
    logger.info(
        f"Embedding model '{settings.MODEL_NAME_FOR_EMBEDDING}' loaded for RAG in cmvs_service."
    )
except Exception as e:
    logger.error(
        f"Failed to load embedding model in cmvs_service for RAG: {e}", exc_info=True
    )
    embedding_model_instance = None

# Initialize LLM
try:
    llm_instance = ChatGroq(
        temperature=0.1,
        groq_api_key=settings.GROQ_API_KEY,
        model_name=settings.LLM_MODEL_NAME_GROQ,
    )
    logger.info(f"LLM '{settings.LLM_MODEL_NAME_GROQ}' loaded for RAG in cmvs_service.")
except Exception as e:
    logger.error(f"Failed to load LLM in cmvs_service for RAG: {e}", exc_info=True)
    llm_instance = None


async def run_cmvs_pipeline(initial_state: GraphState) -> GraphState:
    logger.info(
        f"Running CMVS pipeline for file: {initial_state.get('current_filename')}, User: {initial_state.get('user_id')}"
    )
    langgraph_app = get_langgraph_app()

    # Ensure a unique thread_id for each run if using MemorySaver or similar checkpointers
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    final_state = await langgraph_app.ainvoke(initial_state, config=config)
    logger.info(
        f"CMVS pipeline finished for file: {initial_state.get('current_filename')}"
    )
    return final_state


async def get_rag_details_for_node(
    concept_map_id: str,
    node_query: str,
    user_id: str,
    top_k_retriever: int = 3,  # Number of documents to retrieve
) -> Optional[NodeDetailResponse]:

    if not embedding_model_instance:
        logger.error("RAG: Embedding model not available.")
        return NodeDetailResponse(
            query=node_query,
            answer="Error: Embedding model not configured.",
            cited_sources=[],
            search_performed="document_only",
            message="Embedding model configuration error.",
        )
    if not llm_instance:
        logger.error("RAG: LLM not available.")
        return NodeDetailResponse(
            query=node_query,
            answer="Error: LLM not configured.",
            cited_sources=[],
            search_performed="document_only",
            message="LLM configuration error.",
        )
    if not settings.MONGODB_URI:
        logger.error("RAG: MongoDB URI not configured.")
        return NodeDetailResponse(
            query=node_query,
            answer="Error: Database not configured.",
            cited_sources=[],
            search_performed="document_only",
            message="Database configuration error.",
        )

    logger.info(
        f"RAG: Fetching details for node '{node_query}' in map '{concept_map_id}' for user '{user_id}'."
    )

    try:
        # 1. Initialize MongoDB Atlas Vector Search
        # Note: The collection should be the one where chunk embeddings are stored.
        # text_key refers to the field in your MongoDB documents that contains the text of the chunk.
        # embedding_key refers to the field that contains the vector embedding.
        vector_store = MongoDBAtlasVectorSearch.from_connection_string(
            connection_string=settings.MONGODB_URI,
            db_name=settings.MONGODB_DATABASE_NAME,
            collection_name=settings.MONGODB_CHUNKS_COLLECTION,  # Collection with chunk texts & embeddings
            embedding=embedding_model_instance,
            index_name=settings.MONGODB_ATLAS_VECTOR_SEARCH_INDEX_NAME,
            text_key="text",  # Make sure this matches the field name in your 'chunk_embeddings' collection
            embedding_key="embedding",  # Make sure this matches
            namespace=f"{settings.MONGODB_DATABASE_NAME}.{settings.MONGODB_CHUNKS_COLLECTION}",
        )
        logger.info(
            f"RAG: Initialized MongoDBAtlasVectorSearch with index '{settings.MONGODB_ATLAS_VECTOR_SEARCH_INDEX_NAME}'."
        )

        # 2. Create a Retriever with pre-filtering and enhanced search
        # The pre_filter stage in Atlas Vector Search uses MQL (MongoDB Query Language).
        # Ensure 'user_id' and 'concept_map_id' are properly indexed as filter fields in your Atlas Search Index.
        retriever_filter = {"user_id": user_id, "concept_map_id": concept_map_id}

        # First, try to find documents that directly mention the node query
        # This will help with context awareness for specific topics like "Introduction"
        enhanced_query = node_query

        # For specific section names, enhance the query to find relevant content
        if any(
            term in node_query.lower()
            for term in [
                "introduction",
                "overview",
                "conclusion",
                "summary",
                "definition",
            ]
        ):
            # Add variations to help find section-specific content
            enhanced_query = f"{node_query} section content overview"

        retriever = vector_store.as_retriever(
            search_type="mmr",  # Use MMR for more diverse results
            search_kwargs={
                "k": top_k_retriever * 2,  # Get more candidates for better filtering
                "fetch_k": top_k_retriever * 4,  # Fetch even more for MMR diversity
                "lambda_mult": 0.7,  # Balance between relevance and diversity
                "pre_filter": retriever_filter,  # Apply pre-filter
            },
            verbose=True,
        )

        # Also create a secondary retriever for backup if first doesn't find relevant content
        backup_retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": top_k_retriever,
                "pre_filter": retriever_filter,
            },
            verbose=True,
        )

        logger.info(
            f"RAG: Enhanced retriever created with MMR search for query '{enhanced_query}'"
        )

        # 3. Define enhanced prompt template with better context awareness
        template = """You are an intelligent assistant that provides detailed explanations about concept map nodes based on retrieved document context with hierarchical structure awareness.

Your task is to provide a comprehensive and detailed explanation about the concept or topic being asked about using proper markdown formatting. You have access to structured document content with section hierarchies to provide contextually accurate answers.

CRITICAL CONTEXT AWARENESS RULES:
- ALWAYS prioritize content that directly relates to the specific concept or section being asked about
- If the query mentions a specific section (like "Introduction", "Overview", "Conclusion"), focus on content from that section
- Pay attention to document structure indicators (📋 Document Structure) that show where content appears
- Use the section context to provide accurate answers, not generic information
- If multiple sections are available, prioritize the most relevant one to the query

HIERARCHICAL CONTEXT AWARENESS:
- Pay attention to document structure indicators (📋 Document Structure) that show where content appears in the document hierarchy
- Use section context to provide more accurate and contextually relevant explanations
- Reference the document structure when helpful for understanding relationships between concepts
- When asked about a specific section, focus ONLY on content from that section

IMPORTANT LANGUAGE INSTRUCTIONS:
- If the retrieved context is primarily in Bahasa Indonesia, respond in Bahasa Indonesia
- If the retrieved context is primarily in English, respond in English
- Match the language of the context to provide the most natural and accurate response

MARKDOWN FORMATTING REQUIREMENTS:
- Use # for main title (concept name)
- Use ## for main sections (like Definition, Characteristics, Examples, etc.)
- Use ### for subsections if needed
- Use **bold** for important terms or key points
- Use bullet points (-) for lists
- Use numbered lists (1.) when showing steps or ordered information
- Use > for important quotes or key definitions
- Use `code` formatting for technical terms if applicable

RESPONSE STRUCTURE WITH CONTEXT AWARENESS:
1. Start with a main title using # (the concept or section name)
2. If asking about a specific section, focus the answer on that section's content
3. Provide information that directly relates to the query context
4. Include relevant details from the hierarchical structure
5. Reference document sections when providing context using ##
6. If insufficient relevant information, clearly state limitations

Question: {question}

Retrieved Context with Hierarchical Structure:
{context}

Detailed Answer with Context Awareness:"""
        prompt = ChatPromptTemplate.from_template(template)

        # 4. Enhanced helper function to format retrieved documents with better context matching
        def format_docs(docs: List[Document]) -> str:
            if not docs:
                return "No relevant documents found."

            # Score documents by relevance to the query
            scored_docs = []
            query_lower = node_query.lower()

            for doc in docs:
                relevance_score = 0
                content_lower = doc.page_content.lower()

                # Check for direct mentions of the query terms
                for term in query_lower.split():
                    if term in content_lower:
                        relevance_score += 2

                # Check section relevance
                section_title = doc.metadata.get("section_title", "").lower()
                parent_headers = doc.metadata.get("parent_headers", [])

                # Higher score for exact section matches
                if query_lower in section_title:
                    relevance_score += 10

                # Check parent headers
                for header in parent_headers:
                    header_text = header.get("text", "").lower()
                    if query_lower in header_text:
                        relevance_score += 5
                    for term in query_lower.split():
                        if term in header_text:
                            relevance_score += 1

                # Check if this is introduction/overview content
                if any(
                    term in query_lower
                    for term in ["introduction", "overview", "intro"]
                ):
                    if any(
                        term in content_lower
                        for term in [
                            "introduction",
                            "overview",
                            "intro",
                            "pengenalan",
                            "pendahuluan",
                        ]
                    ):
                        relevance_score += 5

                scored_docs.append((doc, relevance_score))

            # Sort by relevance score and take the most relevant
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            docs = [doc for doc, score in scored_docs[:top_k_retriever]]

            formatted_chunks = []
            for i, doc in enumerate(docs, 1):
                source_info = ""
                if doc.metadata.get("source_filename"):
                    source_info = f" (Source: {doc.metadata['source_filename']}"
                    if doc.metadata.get("page_number"):
                        source_info += f", Page {doc.metadata['page_number']}"
                    source_info += ")"

                # Add hierarchical context if available
                content = doc.page_content
                hierarchy_info = ""

                # Extract section and parent headers from metadata
                section_title = doc.metadata.get("section_title", "")
                parent_headers = doc.metadata.get("parent_headers", [])

                if parent_headers or section_title:
                    hierarchy_path = []
                    if parent_headers:
                        hierarchy_path.extend(
                            [h.get("text", str(h)) for h in parent_headers]
                        )
                    if section_title and section_title not in hierarchy_path:
                        hierarchy_path.append(section_title)

                    if hierarchy_path:
                        hierarchy_info = (
                            f"\n📋 Document Structure: {' → '.join(hierarchy_path)}\n"
                        )

                formatted_chunks.append(
                    f"Document {i}{source_info}:{hierarchy_info}\n{content}"
                )

            format = "\n\n" + "=" * 50 + "\n\n".join(formatted_chunks)
            return format

        # 5. Enhanced retrieval function that tries multiple strategies
        async def enhanced_retrieve(query: str) -> List[Document]:
            try:
                # First attempt with enhanced query
                docs = await retriever.ainvoke(enhanced_query)

                # Check if we got relevant results
                if docs:
                    # Filter docs by relevance
                    relevant_docs = []
                    query_terms = set(query.lower().split())

                    for doc in docs:
                        content_lower = doc.page_content.lower()
                        section_title = doc.metadata.get("section_title", "").lower()

                        # Check if document is relevant
                        is_relevant = False

                        # Direct term matches
                        if any(term in content_lower for term in query_terms):
                            is_relevant = True

                        # Section title matches
                        if any(term in section_title for term in query_terms):
                            is_relevant = True

                        # Special handling for section queries
                        if any(
                            term in query.lower()
                            for term in ["introduction", "overview", "conclusion"]
                        ):
                            if any(
                                term in content_lower
                                for term in [
                                    "introduction",
                                    "overview",
                                    "conclusion",
                                    "pengenalan",
                                    "pendahuluan",
                                    "kesimpulan",
                                ]
                            ):
                                is_relevant = True

                        if is_relevant:
                            relevant_docs.append(doc)

                    if relevant_docs:
                        return relevant_docs[:top_k_retriever]

                # If no relevant docs, try backup retriever with original query
                logger.info(
                    "Primary retrieval didn't find relevant docs, trying backup retriever"
                )
                backup_docs = await backup_retriever.ainvoke(query)
                return backup_docs[:top_k_retriever] if backup_docs else []

            except Exception as e:
                logger.error(f"Error in enhanced retrieval: {e}")
                # Final fallback to basic similarity search
                try:
                    return await backup_retriever.ainvoke(query)
                except Exception as e2:
                    logger.error(f"Backup retrieval also failed: {e2}")
                    return []

        # 6. Construct enhanced RAG Chain using LCEL with better retrieval
        rag_chain_from_docs = (
            RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
            | prompt
            | llm_instance
            | StrOutputParser()
        )

        # Use enhanced retrieval instead of basic retriever
        rag_chain_with_source = RunnableParallel(
            {
                "context": RunnableLambda(enhanced_retrieve),
                "question": RunnablePassthrough(),
            }
        ).assign(answer=rag_chain_from_docs)

        logger.info(f"RAG: Invoking enhanced chain for question: '{node_query}'")
        # Invoke the chain asynchronously with enhanced retrieval
        response_data = await rag_chain_with_source.ainvoke(node_query)

        answer = response_data.get("answer", "No answer generated.")
        source_documents: List[Document] = response_data.get("context", [])

        logger.info(
            f"RAG: Successfully generated answer for '{node_query}'. Retrieved {len(source_documents)} documents."
        )

        # Log document relevance for debugging
        for i, doc in enumerate(source_documents[:3]):  # Log first 3 docs
            section_info = doc.metadata.get("section_title", "N/A")
            logger.debug(
                f"Retrieved doc {i+1}: Section='{section_info}', Content preview: {doc.page_content[:100]}..."
            )

        # Helper function to build citation title with hierarchical context
        def build_citation_title(metadata: dict) -> str:
            filename = metadata.get("source_filename", "Unknown Document")
            section_title = metadata.get("section_title", "")
            parent_headers = metadata.get("parent_headers", [])

            title = filename
            if parent_headers or section_title:
                hierarchy_path = []
                if parent_headers:
                    hierarchy_path.extend(
                        [h.get("text", str(h)) for h in parent_headers]
                    )
                if section_title and section_title not in hierarchy_path:
                    hierarchy_path.append(section_title)

                if hierarchy_path:
                    title += f" - {' → '.join(hierarchy_path)}"

            return title

        return NodeDetailResponse(
            query=node_query,
            answer=answer,
            cited_sources=[
                CitationSource(
                    type="mongodb_chunk",
                    identifier=doc.metadata.get("source_s3_path") or "unknown",
                    title=build_citation_title(doc.metadata),
                    snippet=(
                        doc.page_content[:300] + "..."
                        if len(doc.page_content) > 300
                        else doc.page_content
                    ),
                )
                for doc in source_documents
            ],
            search_performed="document_only",
            message="Successfully retrieved detailed information from uploaded documents with hierarchical context.",
        )

    except Exception as e:
        logger.error(
            f"RAG: Error during RAG pipeline for node '{node_query}': {e}",
            exc_info=True,
        )
        return NodeDetailResponse(
            query=node_query,
            answer=f"Error processing your request: {str(e)}",
            cited_sources=[],
            search_performed="document_only",
            message=f"Error occurred while processing: {str(e)}",
        )


async def get_node_details_with_rag(
    concept_map_id: str, node_query: str, user_id: str, top_k_retriever: int = 3
) -> NodeDetailResponse:
    """
    Retrieves detailed node explanations using RAG (Retrieval Augmented Generation) from stored documents.
    This function searches through uploaded documents stored in MongoDB and uses vector similarity
    to find relevant context for providing comprehensive explanations about concept map nodes.

    The function automatically detects the language of the context (especially Bahasa Indonesia vs English)
    and responds in the same language for better user experience.

    Args:
        concept_map_id: ID of the concept map
        node_query: The question/query about the node requiring detailed explanation
        user_id: ID of the user making the request
        top_k_retriever: Number of top similar documents to retrieve (default: 3)

    Returns:
        NodeDetailResponse with detailed answer and citations from uploaded documents,
        automatically formatted in the appropriate language (Bahasa/English) based on context
    """
    logger.info(
        f"Service: Retrieving node details from documents for '{node_query}', map '{concept_map_id}', user '{user_id}'."
    )

    # Use the existing direct MongoDB vector search function
    result = await get_rag_details_for_node(
        concept_map_id=concept_map_id,
        node_query=node_query,
        user_id=user_id,
        top_k_retriever=top_k_retriever,
    )

    if result is None:
        return NodeDetailResponse(
            query=node_query,
            answer="Tidak ada informasi yang dapat ditemukan dari dokumen yang telah diunggah. / No detailed information could be retrieved from the uploaded documents.",
            cited_sources=[],
            search_performed="document_only",
            message="No relevant information found in uploaded documents for detailed explanation.",
        )

    # The result already contains cited_sources in the correct format
    return result
