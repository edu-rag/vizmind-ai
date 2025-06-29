from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.documents import Document


class EmbeddedChunk(TypedDict):
    text: str
    embedding: List[float]
    source_filename: Optional[str]  # Track which file this chunk came from
    source_s3_path: Optional[str]  # Track the S3 path of the source file


class AttachmentInfo(TypedDict):
    filename: str
    s3_path: Optional[str]
    extracted_text: str


class GraphState(TypedDict):
    # Input states
    original_text: str  # Combined text from all files
    attachments: List[AttachmentInfo]  # Information about all uploaded files
    user_id: Optional[str]  # User's MongoDB ID

    # Intermediate and output states
    text_chunks: List[str]
    embedded_chunks: Optional[List[EmbeddedChunk]]
    raw_triples: List[Dict[str, str]]
    processed_triples: List[Dict[str, str]]
    react_flow_data: Dict[str, Any]

    # DB Interaction results
    mongodb_doc_id: Optional[str]  # ID of the main concept map document
    mongodb_chunk_ids: Optional[List[str]]  # IDs of stored chunk/embedding documents

    # Error handling
    error_message: Optional[str]


class RAGGraphState(TypedDict):
    question: str
    user_id: str
    concept_map_id: str
    top_k_retriever: int

    # Retrieval results
    db_documents: List[Document]
    web_documents: Optional[List[Document]]  # Populated if web search is triggered

    # Generation results
    answer: str
    cited_sources: List[Dict[str, Any]]  # Will be transformed into CitationSource model

    # Control flow
    # Determines if the initial DB retrieval was sufficient
    # Values: "generate_from_db", "perform_web_search"
    db_retrieval_status: str
    error_message: Optional[str]
