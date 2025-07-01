from app.langgraph_pipeline.builder.hierarchical_builder import (
    get_hierarchical_langgraph_app,
)
from app.langgraph_pipeline.state import HierarchicalGraphState
from app.core.config import settings, logger
from app.models.cmvs_models import (
    NodeDetailResponse,
    CitationSource,
    MindMapResponse,
    AttachmentInfo as AttachmentInfoModel,
    HierarchicalNode,
)

import uuid

from typing import List, Optional


# Langchain imports for RAG
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_huggingface import HuggingFaceEmbeddings  # Your chosen embedding model
from langchain_groq import ChatGroq  # Your chosen LLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
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


async def generate_hierarchical_mindmap(
    filename: str, extracted_text: str, s3_path: str, user_id: str
) -> MindMapResponse:
    """
    NEW: Generate hierarchical mind map using two-stage processing.

    Args:
        filename: Original filename of the uploaded document
        extracted_text: Extracted text from the PDF
        s3_path: S3 path where the file is stored
        user_id: ID of the user

    Returns:
        MindMapResponse with hierarchical data structure
    """
    logger.info(
        f"Generating hierarchical mind map for file: {filename}, User: {user_id}"
    )

    try:
        # Prepare initial state for hierarchical processing
        initial_state = HierarchicalGraphState(
            attachment={
                "filename": filename,
                "s3_path": s3_path,
                "extracted_text": extracted_text,
                "pages": [],  # Will be populated by the pipeline
            },
            user_id=user_id,
            page_analyses=[],
            consolidated_markdown="",
            document_title="",
            hierarchical_data={},
            mongodb_doc_id=None,
            error_message=None,
        )

        # Get the hierarchical LangGraph app
        langgraph_app = get_hierarchical_langgraph_app()

        # Generate unique thread ID for this run
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # Run the hierarchical pipeline
        final_state = await langgraph_app.ainvoke(initial_state, config=config)

        if final_state.get("error_message"):
            logger.error(f"Pipeline error: {final_state['error_message']}")
            return MindMapResponse(
                attachment=AttachmentInfoModel(
                    filename=filename,
                    s3_path=s3_path,
                    status="error",
                    error_message=final_state["error_message"],
                ),
                status="error",
                hierarchical_data=None,
                mongodb_doc_id=None,
                error_message=final_state["error_message"],
            )

        # Convert hierarchical data to HierarchicalNode model
        hierarchical_node = HierarchicalNode(**final_state["hierarchical_data"])

        logger.info(f"Successfully generated hierarchical mind map for {filename}")

        return MindMapResponse(
            attachment=AttachmentInfoModel(
                filename=filename, s3_path=s3_path, status="success"
            ),
            status="success",
            hierarchical_data=hierarchical_node,
            mongodb_doc_id=final_state.get("mongodb_doc_id"),
            error_message=None,
        )

    except Exception as e:
        logger.error(f"Error in generate_hierarchical_mindmap: {e}", exc_info=True)
        return MindMapResponse(
            attachment=AttachmentInfoModel(
                filename=filename, s3_path=s3_path, status="error", error_message=str(e)
            ),
            status="error",
            hierarchical_data=None,
            mongodb_doc_id=None,
            error_message=f"Failed to generate mind map: {str(e)}",
        )


# === RAG FUNCTIONS ===


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

        # 2. Create a Retriever with pre-filtering
        # The pre_filter stage in Atlas Vector Search uses MQL (MongoDB Query Language).
        # Ensure 'user_id' and 'concept_map_id' are properly indexed as filter fields in your Atlas Search Index.
        retriever_filter = {"user_id": user_id, "concept_map_id": concept_map_id}

        retriever = vector_store.as_retriever(
            search_type="similarity",  # Or "mmr" for max marginal relevance
            search_kwargs={
                "k": top_k_retriever,
                "pre_filter": retriever_filter,  # Apply pre-filter
                # "post_filter_pipeline": [{"$match": retriever_filter_mql}] # Alternative for post-filtering
            },
            verbose=True,
        )
        logger.info(
            f"RAG: Retriever created with k={top_k_retriever} and filter for user/map."
        )

        # 3. Define Prompt Template
        template = """You are an intelligent assistant that provides detailed explanations about concept map nodes based on retrieved document context.

Your task is to provide a comprehensive and detailed explanation about the concept or topic being asked about using proper markdown formatting.

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

RESPONSE STRUCTURE:
1. Start with a main title using # (the concept name)
2. Provide a clear definition section using ##
3. Include key characteristics or properties using ##
4. Add relationships to other concepts if available using ##
5. Include examples or applications if mentioned using ##
6. If insufficient information, clearly state limitations

Example structure:
# Concept Name

## Definisi / Definition
Clear explanation of what the concept is...

## Karakteristik Utama / Key Characteristics
- **Point 1**: Explanation
- **Point 2**: Explanation

## Hubungan dengan Konsep Lain / Relationships
How this concept relates to others...

## Contoh dan Aplikasi / Examples and Applications
Real-world examples or applications...

Question: {question}

Retrieved Context:
{context}

Detailed Answer with Markdown Formatting:"""
        prompt = ChatPromptTemplate.from_template(template)

        # 4. Helper function to format retrieved documents
        def format_docs(docs: List[Document]) -> str:
            if not docs:
                return "No relevant documents found."

            formatted_chunks = []
            for i, doc in enumerate(docs, 1):
                source_info = ""
                if doc.metadata.get("source_filename"):
                    source_info = f" (Source: {doc.metadata['source_filename']})"

                formatted_chunks.append(
                    f"Document {i}{source_info}:\n{doc.page_content}"
                )

            format = "\n\n" + "=" * 50 + "\n\n".join(formatted_chunks)
            print(format)
            return format

        # 5. Construct RAG Chain using LCEL
        rag_chain_from_docs = (
            RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
            | prompt
            | llm_instance
            | StrOutputParser()
        )

        rag_chain_with_source = RunnableParallel(
            {"context": retriever, "question": RunnablePassthrough()}
        ).assign(answer=rag_chain_from_docs)

        logger.info(f"RAG: Invoking chain for question: '{node_query}'")
        # Invoke the chain asynchronously.
        # Note: Some parts of the chain might involve sync calls if not fully async compatible (e.g. some retrievers)
        # Langchain's ainvoke handles this.
        response_data = await rag_chain_with_source.ainvoke(node_query)

        answer = response_data.get("answer", "No answer generated.")
        source_documents: List[Document] = response_data.get("context", [])

        logger.info(f"RAG: Successfully generated answer for '{node_query}'.")
        return NodeDetailResponse(
            query=node_query,
            answer=answer,
            cited_sources=[
                CitationSource(
                    type="mongodb_chunk",
                    identifier=doc.metadata.get("source_s3_path") or "unknown",
                    title=doc.metadata.get("source_filename") or "Unknown Document",
                    snippet=(
                        doc.page_content[:300] + "..."
                        if len(doc.page_content) > 300
                        else doc.page_content
                    ),
                )
                for doc in source_documents
            ],
            search_performed="document_only",
            message="Successfully retrieved detailed information from uploaded documents.",
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
