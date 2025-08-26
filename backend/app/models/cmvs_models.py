from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# --- Hierarchical Mind Map Models ---
class HierarchicalNode(BaseModel):
    """Represents a single node in the hierarchical mind map."""

    id: str = Field(description="Unique identifier for the node")
    data: Dict[str, str] = Field(description="Node data containing label")
    children: List["HierarchicalNode"] = Field(default=[], description="Child nodes")


# Enable forward references
HierarchicalNode.model_rebuild()


# --- API Response Models ---
class AttachmentInfo(BaseModel):
    filename: str
    s3_path: Optional[str] = None
    status: str  # "success" or "error"
    error_message: Optional[str] = None


class MindMapResponse(BaseModel):
    """Response model for the new hierarchical mind map system."""

    attachment: AttachmentInfo
    status: str
    hierarchical_data: Optional[HierarchicalNode] = None
    mongodb_doc_id: Optional[str] = None
    error_message: Optional[str] = None


# --- RAG Response Model ---
class CitationSource(BaseModel):
    type: str  # e.g., "mongodb_chunk"
    identifier: str  # e.g., MongoDB document _id, S3 path
    title: Optional[str] = None  # e.g., original PDF filename
    page_number: Optional[int] = None  # If applicable and available
    snippet: Optional[str] = None  # The actual text content of the chunk/source


class NodeDetailResponse(BaseModel):
    query: str
    answer: str
    cited_sources: List[CitationSource]
    message: Optional[str] = None
