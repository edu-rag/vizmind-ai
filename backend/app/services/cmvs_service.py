from app.langgraph_pipeline.builder.cmvs_builder import get_langgraph_app
from app.langgraph_pipeline.state import GraphState
from app.core.config import settings, logger
from app.models.cmvs_models import RetrievedChunk, NodeDetailResponse

from app.langgraph_pipeline.builder.rag_builder import get_rag_app
from app.langgraph_pipeline.state import RAGGraphState
from app.models.cmvs_models import (
    NodeDetailResponse,
    CitationSource,
)  # Use the new response model

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
        temperature=0.1,  # Adjust temperature for desired creativity
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
            source_chunks=[],
        )
    if not llm_instance:
        logger.error("RAG: LLM not available.")
        return NodeDetailResponse(
            query=node_query, answer="Error: LLM not configured.", source_chunks=[]
        )
    if not settings.MONGODB_URI:
        logger.error("RAG: MongoDB URI not configured.")
        return NodeDetailResponse(
            query=node_query, answer="Error: Database not configured.", source_chunks=[]
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
        )
        logger.info(
            f"RAG: Retriever created with k={top_k_retriever} and filter for user/map."
        )

        # 3. Define Prompt Template
        template = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Keep the answer concise and directly related to the question based on the provided context.

Question: {question}

Context:
{context}

Answer:"""
        prompt = ChatPromptTemplate.from_template(template)

        # 4. Helper function to format retrieved documents
        def format_docs(docs: List[Document]) -> str:
            return "\n\n---\n\n".join([f"Chunk: {d.page_content}" for d in docs])

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

        retrieved_chunks_for_response: List[RetrievedChunk] = []
        for doc in source_documents:
            # Extract similarity score if available (depends on retriever and vector store capabilities)
            # MongoDBAtlasVectorSearch retriever documents have `doc.metadata['score']` if search includes it.
            # We need to ensure our $project stage in vectorSearch (if manually defined) or the retriever adds it.
            # For now, we'll assume score might not be directly available unless explicitly projected in Atlas.
            # If you included "$project": {"score": {"$meta": "vectorSearchScore"}} in Atlas index/query
            score = doc.metadata.get("score", None)  # Or 'search_score' etc.

            retrieved_chunks_for_response.append(
                RetrievedChunk(
                    text=doc.page_content,
                    similarity_score=float(score) if score is not None else None,
                    s3_path_source_pdf=doc.metadata.get(
                        "s3_path_source_pdf"
                    ),  # Ensure these are in doc.metadata
                    original_filename_source_pdf=doc.metadata.get(
                        "original_filename_source_pdf"
                    ),
                    metadata=doc.metadata,  # Pass along all metadata
                )
            )

        logger.info(f"RAG: Successfully generated answer for '{node_query}'.")
        return NodeDetailResponse(
            query=node_query, answer=answer, source_chunks=retrieved_chunks_for_response
        )

    except Exception as e:
        logger.error(
            f"RAG: Error during RAG pipeline for node '{node_query}': {e}",
            exc_info=True,
        )
        return NodeDetailResponse(
            query=node_query,
            answer=f"Error processing your request: {str(e)}",
            source_chunks=[],
        )


async def get_node_details_with_rag(  # Renamed function
    concept_map_id: str, node_query: str, user_id: str, top_k_retriever: int = 3
) -> NodeDetailResponse:  # Return new response model

    logger.info(
        f"Service: Initiating RAG pipeline for node '{node_query}', map '{concept_map_id}', user '{user_id}'."
    )
    rag_app = get_rag_app()  # Get the compiled RAG graph

    initial_rag_state = RAGGraphState(
        question=node_query,
        user_id=user_id,
        concept_map_id=concept_map_id,
        top_k_retriever=top_k_retriever,
        db_documents=[],
        web_documents=None,
        answer="",
        cited_sources=[],
        db_retrieval_status="",
        error_message=None,
    )

    try:
        # Run the RAG graph
        # Use a unique config for each invocation if using checkpointers that need it
        # config = {"configurable": {"thread_id": f"rag-{user_id}-{uuid.uuid4()}"}}
        final_state = await rag_app.ainvoke(
            initial_rag_state
        )  # No config needed if not using persistent checkpointer per call

        if final_state.get("error_message"):
            logger.error(
                f"RAG pipeline error for query '{node_query}': {final_state['error_message']}"
            )
            return NodeDetailResponse(
                query=node_query,
                answer=f"An error occurred: {final_state['error_message']}",
                cited_sources=[],
                message=f"Error during processing: {final_state['error_message']}",
            )

        # Transform cited_sources from the graph state (list of dicts) to list of CitationSource Pydantic models
        formatted_citations: List[CitationSource] = []
        for src_dict in final_state.get("cited_sources", []):
            try:
                formatted_citations.append(CitationSource(**src_dict))
            except Exception as e:
                logger.warning(f"Could not format citation: {src_dict}, error: {e}")

        search_type = "db_only"
        if (
            final_state.get("web_documents") is not None
            and len(final_state["web_documents"]) > 0
        ):  # Check if web_documents were populated
            search_type = "db_and_web_search"
        elif final_state.get("db_retrieval_status") == "perform_web_search" and (
            final_state.get("web_documents") is None
            or len(final_state.get("web_documents", [])) == 0
        ):
            search_type = "db_and_web_search_no_web_results"

        return NodeDetailResponse(
            query=node_query,
            answer=final_state.get("answer", "No answer could be generated."),
            cited_sources=formatted_citations,
            search_performed=search_type,
            message=(
                "Successfully retrieved details."
                if final_state.get("answer")
                else "Could not generate a conclusive answer."
            ),
        )

    except Exception as e:
        logger.error(
            f"Service level error running RAG pipeline for node '{node_query}': {e}",
            exc_info=True,
        )
        return NodeDetailResponse(
            query=node_query,
            answer=f"A critical error occurred while processing your request: {str(e)}",
            cited_sources=[],
            message="Critical server error.",
        )
