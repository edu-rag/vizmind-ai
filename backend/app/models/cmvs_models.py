from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# --- VizMind AI Hierarchical Mind Map Models ---
class HierarchicalNode(BaseModel):
    """Represents a single node in the VizMind AI hierarchical mind map."""

    id: str = Field(description="Unique identifier for the node")
    data: Dict[str, str] = Field(description="Node data containing label")
    children: List["HierarchicalNode"] = Field(default=[], description="Child nodes")


# Enable forward references
HierarchicalNode.model_rebuild()


# --- API Response Models ---
class AttachmentInfo(BaseModel):
    """Information about the processed document attachment."""

    filename: str
    s3_path: Optional[str] = None
    status: str  # "success" or "error"
    error_message: Optional[str] = None


class MindMapResponse(BaseModel):
    """Response model for VizMind AI mind map generation."""

    attachment: AttachmentInfo
    status: str
    hierarchical_data: Optional[HierarchicalNode] = None
    mongodb_doc_id: Optional[str] = None
    error_message: Optional[str] = None
    processing_metadata: Optional[Dict[str, Any]] = None


# --- RAG Response Models ---
class CitationSource(BaseModel):
    """Source citation for RAG responses."""

    type: str  # e.g., "mongodb_chunk"
    identifier: str  # e.g., MongoDB document _id, chunk_id
    title: Optional[str] = None  # e.g., original PDF filename
    page_number: Optional[int] = None  # If applicable and available
    snippet: Optional[str] = None  # The actual text content of the chunk/source


class NodeDetailResponse(BaseModel):
    """Response model for node detail queries (RAG)."""

    query: str
    answer: str
    cited_sources: List[CitationSource]
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    message: Optional[str] = None


class WorkflowMetrics(BaseModel):
    """Metrics for completed workflows."""

    processing_time_seconds: Optional[float] = None
    chunk_count: Optional[int] = None
    embedding_dimension: Optional[int] = None
    retrieval_time: Optional[float] = None
    generation_time: Optional[float] = None
    documents_retrieved: Optional[int] = None
    relevant_documents: Optional[int] = None
