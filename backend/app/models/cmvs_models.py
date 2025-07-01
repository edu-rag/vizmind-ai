from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

try:
    from pydantic.v1 import BaseModel as LangchainBaseModel
except ImportError:
    from pydantic import BaseModel as LangchainBaseModel


# --- Hierarchical Mind Map Models ---
class HierarchicalNode(BaseModel):
    """Represents a single node in the hierarchical mind map."""

    id: str = Field(description="Unique identifier for the node")
    data: Dict[str, str] = Field(description="Node data containing label")
    children: List["HierarchicalNode"] = Field(default=[], description="Child nodes")


# Enable forward references
HierarchicalNode.model_rebuild()


class PageAnalysisLLM(BaseModel):
    """Represents extracted topics and key points from a single page."""

    page_number: int = Field(description="The page number being analyzed")
    page_markdown: str = Field(
        description="Extracted topics and key points in markdown format"
    )


class MasterSynthesisLLM(BaseModel):
    """Represents the final consolidated hierarchical markdown."""

    title: str = Field(description="The main title/topic of the document")
    hierarchical_markdown: str = Field(
        description="Final consolidated markdown with hierarchical structure"
    )


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


# --- Legacy Models (REMOVED - using only hierarchical mind maps) ---
# Legacy ReactFlow-based models have been removed
# Use MindMapResponse for new hierarchical mind map workflow

# Legacy unified response model also removed - use MindMapResponse directly


class RetrievedChunk(BaseModel):
    text: str
    similarity_score: Optional[float] = None
    s3_path_source_pdf: Optional[str] = None
    original_filename_source_pdf: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


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
    search_performed: Optional[str] = None  # To indicate "document_only"


class DocumentSufficiencyGrade(LangchainBaseModel):
    """
    Pydantic model for the LLM's assessment of document sufficiency.
    """

    is_sufficient: bool = Field(
        description="True if the provided documents are likely sufficient to answer the question, False otherwise."
    )
    reasoning: Optional[str] = Field(
        description="A brief explanation for the sufficiency judgment.", default=None
    )
    confidence_score: Optional[float] = Field(
        description="A score from 0.0 to 1.0 indicating confidence in sufficiency.",
        default=None,
        ge=0.0,
        le=1.0,
    )  # Optional advanced field
