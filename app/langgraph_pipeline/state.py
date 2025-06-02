from typing import List, Dict, Any, Optional, TypedDict


class EmbeddedChunk(TypedDict):
    text: str
    embedding: List[float]


class GraphState(TypedDict):
    # Input states
    original_text: str
    current_filename: Optional[str]
    s3_path: Optional[str]
    user_id: Optional[str]  # User's MongoDB ID

    # Intermediate and output states
    text_chunks: List[str]
    embedded_chunks: Optional[List[EmbeddedChunk]]
    raw_triples: List[Dict[str, str]]
    processed_triples: List[Dict[str, str]]
    mermaid_code: str

    # DB Interaction results
    mongodb_doc_id: Optional[str]  # ID of the main concept map document
    mongodb_chunk_ids: Optional[List[str]]  # IDs of stored chunk/embedding documents

    # Error handling
    error_message: Optional[str]
