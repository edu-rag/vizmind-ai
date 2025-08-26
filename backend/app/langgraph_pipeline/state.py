"""
State definitions for VizMind AI LangGraph workflows.
This module defines the state schemas used across different workflow stages.
"""

from typing import Dict, List, Optional, Any, Literal
from typing_extensions import TypedDict, Annotated
from langchain_core.documents import Document
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class DocumentProcessingState(TypedDict):
    """State for the document processing workflow."""

    # Input parameters
    user_id: str
    map_id: str
    file_path: str
    s3_path: Optional[str]
    original_filename: str

    # Processing stages
    raw_content: Optional[str]
    cleaned_markdown: Optional[str]
    hierarchical_data: Optional[Dict[str, Any]]
    chunks: Optional[List[Document]]

    # Status tracking
    stage: Literal[
        "initialized",
        "content_extracted",
        "content_cleaned",
        "mind_map_generated",
        "content_chunked",
        "chunks_embedded",
        "completed",
        "failed",
    ]
    error_message: Optional[str]
    retry_count: int

    # Metadata
    processing_start_time: Optional[str]
    processing_end_time: Optional[str]
    chunk_count: Optional[int]
    embedding_dimension: Optional[int]


class RAGState(TypedDict):
    """State for the RAG workflow."""

    # Input parameters
    user_id: str
    map_id: str
    query: str
    top_k: Optional[int]

    # Conversation history
    messages: Annotated[List[BaseMessage], add_messages]

    # Retrieval results
    retrieved_documents: Optional[List[Document]]
    filtered_documents: Optional[List[Document]]
    relevance_scores: Optional[List[float]]

    # Answer generation
    generated_answer: Optional[str]
    cited_sources: Optional[List[Dict[str, Any]]]
    confidence_score: Optional[float]

    # Status tracking
    stage: Literal[
        "initialized",
        "documents_retrieved",
        "documents_graded",
        "answer_generated",
        "completed",
        "failed",
    ]
    error_message: Optional[str]
    retry_count: int

    # Quality metrics
    retrieval_time: Optional[float]
    generation_time: Optional[float]
    total_documents_found: Optional[int]
    relevant_documents_count: Optional[int]


class WorkflowConfig(TypedDict):
    """Configuration for workflow execution."""

    # LLM settings
    llm_model: str
    llm_temperature: float
    max_tokens: Optional[int]

    # Embedding settings
    embedding_model: str
    embedding_dimension: int

    # Retrieval settings
    default_top_k: int
    relevance_threshold: float

    # Processing settings
    max_retries: int
    timeout_seconds: int
    chunk_size: int
    chunk_overlap: int

    # MongoDB settings
    chunks_collection: str
    maps_collection: str
    vector_index_name: str


# Utility functions for state manipulation
def reset_error_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Reset error-related fields in state."""
    state["error_message"] = None
    state["retry_count"] = 0
    return state


def increment_retry(state: Dict[str, Any]) -> Dict[str, Any]:
    """Increment retry count in state."""
    state["retry_count"] = state.get("retry_count", 0) + 1
    return state


def set_error(
    state: Dict[str, Any], error_message: str, stage: str = "failed"
) -> Dict[str, Any]:
    """Set error state with message."""
    state["error_message"] = error_message
    state["stage"] = stage
    return state


def transition_stage(state: Dict[str, Any], new_stage: str) -> Dict[str, Any]:
    """Transition to a new processing stage."""
    state["stage"] = new_stage
    return state
