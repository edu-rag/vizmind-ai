from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel


# --- LLM Interaction Models ---
class ConceptTripleLLM(BaseModel):  # Renamed to avoid conflict if used elsewhere
    """Represents a single extracted concept triple for LLM output."""

    source: str = Field(description="The source concept or entity.")
    target: str = Field(description="The target concept or entity.")
    relation: str = Field(description="The relationship between the source and target.")


class ExtractedTriplesLLM(BaseModel):  # Renamed
    """Represents a list of extracted concept triples from a text chunk for LLM output."""

    triples: List[ConceptTripleLLM] = Field(description="A list of concept triples.")


# --- API Response Models ---
class CMVSResponse(BaseModel):
    filename: str
    status: str
    s3_path: Optional[str] = None
    mermaid_code: Optional[str] = None
    processed_triples: Optional[List[Dict[str, str]]] = None  # Triples after processing
    mongodb_doc_id: Optional[str] = None  # Main CMVS doc ID
    mongodb_chunk_ids: Optional[List[str]] = None  # IDs of stored chunk/embedding docs
    error_message: Optional[str] = None


# --- Multiple CMVS Response Model ---
class MultipleCMVSResponse(BaseModel):
    results: List[CMVSResponse]
    overall_errors: Optional[List[str]] = None  # For errors not tied to a specific file


class RetrievedChunk(BaseModel):
    text: str
    similarity_score: Optional[float] = None
    s3_path_source_pdf: Optional[str] = None
    original_filename_source_pdf: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


# --- RAG Response Model ---


class CitationSource(BaseModel):
    type: str  # e.g., "mongodb_chunk", "web_search"
    identifier: str  # e.g., MongoDB document _id, S3 path, or URL
    title: Optional[str] = None  # e.g., original PDF filename, web page title
    page_number: Optional[int] = None  # If applicable and available
    snippet: Optional[str] = None  # The actual text content of the chunk/source


class NodeDetailResponse(BaseModel):
    query: str
    answer: str
    cited_sources: List[CitationSource]
    message: Optional[str] = None
    search_performed: Optional[str] = None  # To indicate "db_only" or "db_and_web"


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
