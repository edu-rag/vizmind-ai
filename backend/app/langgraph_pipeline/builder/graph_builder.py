"""
LangGraph workflow builders for VizMind AI.
This module creates and configures the execution graphs for document processing and RAG workflows.
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.langgraph_pipeline.state import DocumentProcessingState, RAGState
from app.langgraph_pipeline.nodes.document_processing_nodes import (
    extract_content_node,
    extract_outline_node,
    optimize_mind_map_node,
    chunk_content_node,
    embed_and_store_node,
    finalize_processing_node,
)
from app.langgraph_pipeline.nodes.rag_nodes import (
    retrieve_documents_node,
    grade_documents_node,
    generate_answer_node,
    finalize_rag_node,
    should_continue_after_retrieval,
    should_continue_after_grading,
)
from app.core.config import logger


def create_document_processing_graph():
    """
    Creates the document processing workflow graph.

    Flow: extract_content → extract_outline → optimize_mind_map → chunk_content → embed_and_store → finalize
    """
    logger.info("Creating document processing workflow graph")

    # Create the graph
    workflow = StateGraph(DocumentProcessingState)

    # Add nodes
    workflow.add_node("extract_content", extract_content_node)
    workflow.add_node("extract_outline", extract_outline_node)
    workflow.add_node("optimize_mind_map", optimize_mind_map_node)
    workflow.add_node("chunk_content", chunk_content_node)
    workflow.add_node("embed_and_store", embed_and_store_node)
    workflow.add_node("finalize", finalize_processing_node)

    # Set entry point
    workflow.set_entry_point("extract_content")

    # Add edges for linear flow with conditional error handling
    workflow.add_conditional_edges(
        "extract_content",
        _route_document_processing,
        {
            "extract_outline": "extract_outline",
            "failed": END,
        },
    )

    workflow.add_conditional_edges(
        "extract_outline",
        _route_document_processing,
        {
            "optimize_mind_map": "optimize_mind_map",
            "failed": END,
        },
    )

    workflow.add_conditional_edges(
        "optimize_mind_map",
        _route_document_processing,
        {
            "chunk_content": "chunk_content",
            "failed": END,
        },
    )

    workflow.add_conditional_edges(
        "chunk_content",
        _route_document_processing,
        {
            "embed_and_store": "embed_and_store",
            "failed": END,
        },
    )

    workflow.add_conditional_edges(
        "embed_and_store",
        _route_document_processing,
        {
            "finalize": "finalize",
            "failed": END,
        },
    )

    workflow.add_edge("finalize", END)

    # Compile with checkpointer for state persistence
    memory = MemorySaver()
    compiled_graph = workflow.compile(checkpointer=memory)

    logger.info("Document processing workflow graph created successfully")
    return compiled_graph


def create_rag_graph():
    """
    Creates the RAG workflow graph.

    Flow: retrieve_documents → grade_documents → generate_answer → finalize
    """
    logger.info("Creating RAG workflow graph")

    # Create the graph
    workflow = StateGraph(RAGState)

    # Add nodes
    workflow.add_node("retrieve_documents", retrieve_documents_node)
    workflow.add_node("grade_documents", grade_documents_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("finalize", finalize_rag_node)

    # Set entry point
    workflow.set_entry_point("retrieve_documents")

    # Add conditional edges
    workflow.add_conditional_edges(
        "retrieve_documents",
        _route_after_retrieval,
        {
            "grade_documents": "grade_documents",
            "generate_answer": "generate_answer",
            "failed": END,
        },
    )

    workflow.add_conditional_edges(
        "grade_documents",
        _route_after_grading,
        {
            "generate_answer": "generate_answer",
            "failed": END,
        },
    )

    workflow.add_conditional_edges(
        "generate_answer",
        _route_rag,
        {
            "finalize": "finalize",
            "failed": END,
        },
    )

    workflow.add_edge("finalize", END)

    # Compile with checkpointer
    memory = MemorySaver()
    compiled_graph = workflow.compile(checkpointer=memory)

    logger.info("RAG workflow graph created successfully")
    return compiled_graph


# Router functions
def _route_document_processing(state: DocumentProcessingState) -> str:
    """Route document processing based on current stage and error state."""
    current_stage = state.get("stage", "initialized")
    error_message = state.get("error_message")

    if error_message:
        logger.error(
            f"Document processing failed at stage '{current_stage}': {error_message}"
        )
        return "failed"

    # Route based on current stage
    stage_routing = {
        "content_extracted": "extract_outline",
        "outline_extracted": "optimize_mind_map",
        "mind_map_generated": "chunk_content",
        "content_chunked": "embed_and_store",
        "chunks_embedded": "finalize",
        "completed": END,
    }

    next_stage = stage_routing.get(current_stage)
    if next_stage:
        logger.info(f"Document processing routing: {current_stage} → {next_stage}")
        return next_stage

    logger.warning(f"Unknown stage in document processing: {current_stage}")
    return "failed"


def _route_after_retrieval(state: RAGState) -> str:
    """Route after document retrieval."""
    if state.get("error_message"):
        return "failed"

    return should_continue_after_retrieval(state)


def _route_after_grading(state: RAGState) -> str:
    """Route after document grading."""
    if state.get("error_message"):
        return "failed"

    return should_continue_after_grading(state)


def _route_rag(state: RAGState) -> str:
    """Route RAG workflow based on current stage."""
    current_stage = state.get("stage", "initialized")
    error_message = state.get("error_message")

    if error_message:
        logger.error(f"RAG workflow failed at stage '{current_stage}': {error_message}")
        return "failed"

    # Route based on current stage
    stage_routing = {
        "documents_retrieved": "grade_documents",
        "documents_graded": "generate_answer",
        "answer_generated": "finalize",
        "completed": END,
    }

    next_stage = stage_routing.get(current_stage)
    if next_stage:
        logger.info(f"RAG routing: {current_stage} → {next_stage}")
        return next_stage

    logger.warning(f"Unknown stage in RAG workflow: {current_stage}")
    return "failed"


# Workflow execution helpers
async def execute_document_processing(
    file_path: str,
    user_id: str,
    map_id: str,
    s3_path: str,
    original_filename: str,
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Execute the complete document processing workflow.

    Args:
        file_path: Path to the document file
        user_id: User identifier
        map_id: Concept map identifier
        s3_path: S3 storage path
        original_filename: Original filename
        config: Optional workflow configuration

    Returns:
        Final state of the workflow
    """
    logger.info(f"Starting document processing workflow for {original_filename}")

    # Create initial state
    initial_state = DocumentProcessingState(
        user_id=user_id,
        map_id=map_id,
        file_path=file_path,
        s3_path=s3_path,
        original_filename=original_filename,
        raw_content=None,
        hierarchical_data=None,
        chunks=None,
        stage="initialized",
        error_message=None,
        retry_count=0,
        processing_start_time=None,
        processing_end_time=None,
        chunk_count=None,
        embedding_dimension=None,
    )

    # Create and run the workflow
    graph = create_document_processing_graph()

    try:
        result = await graph.ainvoke(
            initial_state, {"configurable": {"thread_id": f"doc_proc_{map_id}"}}
        )

        logger.info(f"Document processing completed with stage: {result.get('stage')}")
        return result

    except Exception as e:
        logger.error(f"Document processing workflow failed: {e}", exc_info=True)
        return {**initial_state, "stage": "failed", "error_message": str(e)}


async def execute_rag_workflow(
    user_id: str,
    map_id: str,
    query: str,
    top_k: int = 10,
    node_id: str = None,
    node_label: str = None,
    node_children: List[str] = None,
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Execute the complete RAG workflow.

    Args:
        user_id: User identifier
        map_id: Concept map identifier
        query: User question
        top_k: Number of documents to retrieve
        node_id: ID of the clicked mind map node (optional, for context)
        node_label: Label of the clicked mind map node (optional, for context)
        node_children: List of child node labels (optional, for hierarchical context)
        config: Optional workflow configuration

    Returns:
        Final state of the workflow
    """
    logger.info(f"Starting RAG workflow for query: '{query[:100]}...'")
    if node_label:
        logger.info(f"With node context: '{node_label}'")
        if node_children:
            logger.info(f"Node has {len(node_children)} children")

    # Create initial state
    initial_state = RAGState(
        user_id=user_id,
        map_id=map_id,
        query=query,
        top_k=top_k,
        node_id=node_id,
        node_label=node_label,
        node_children=node_children,
        messages=[],
        retrieved_documents=None,
        filtered_documents=None,
        relevance_scores=None,
        generated_answer=None,
        cited_sources=None,
        confidence_score=None,
        stage="initialized",
        error_message=None,
        retry_count=0,
        retrieval_time=None,
        generation_time=None,
        total_documents_found=None,
        relevant_documents_count=None,
    )

    # Create and run the workflow
    graph = create_rag_graph()

    try:
        result = await graph.ainvoke(
            initial_state,
            {"configurable": {"thread_id": f"rag_{user_id}_{map_id}"}},
        )

        logger.info(f"RAG workflow completed with stage: {result.get('stage')}")
        return result

    except Exception as e:
        logger.error(f"RAG workflow failed: {e}", exc_info=True)
        return {**initial_state, "stage": "failed", "error_message": str(e)}
