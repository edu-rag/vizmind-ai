from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


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


class MultipleCMVSResponse(BaseModel):
    results: List[CMVSResponse]
    overall_errors: Optional[List[str]] = None  # For errors not tied to a specific file
