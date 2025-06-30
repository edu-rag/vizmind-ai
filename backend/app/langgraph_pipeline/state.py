from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.documents import Document


class EmbeddedChunk(TypedDict):
    text: str
    embedding: List[float]
    source_filename: Optional[str]  # Track which file this chunk came from
    source_s3_path: Optional[str]  # Track the S3 path of the source file
    hierarchy_level: Optional[
        int
    ]  # Hierarchy level (0=title, 1=chapter, 2=section, etc.)
    page_number: Optional[int]  # Page number where this chunk appears
    chunk_type: Optional[str]  # Type: 'header', 'body', 'conclusion', etc.


class HierarchicalNode(TypedDict):
    """Hierarchical content node with title, text, and children"""

    title: str
    text: str
    children: List["HierarchicalNode"]  # Recursive structure


class AttachmentInfo(TypedDict):
    filename: str
    s3_path: Optional[str]
    extracted_text: str
    structured_content: Optional[HierarchicalNode]  # Hierarchical structure
    metadata: Optional[Dict[str, Any]]  # Document metadata (title, author, etc.)


class HierarchicalChunk(TypedDict):
    text: str
    hierarchy_level: int
    parent_headers: List[str]  # List of parent headers for context
    section_title: Optional[str]  # Title of the section this chunk belongs to
    chunk_index: int  # Position within the document
    source_filename: Optional[str]
    page_number: Optional[int]


class GraphState(TypedDict):
    # Input states
    original_text: str  # Combined text from all files
    attachments: List[AttachmentInfo]  # Information about all uploaded files
    user_id: Optional[str]  # User's MongoDB ID

    # Enhanced chunking states
    hierarchical_chunks: Optional[
        List[HierarchicalChunk]
    ]  # Structured chunks with hierarchy
    embedded_chunks: Optional[List[EmbeddedChunk]]  # Embedded chunks with metadata

    # Concept extraction states
    raw_triples: List[Dict[str, str]]
    processed_triples: List[Dict[str, str]]
    hierarchical_concepts: Optional[Dict[str, Any]]  # Hierarchical concept structure
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

    # Generation results
    answer: str
    cited_sources: List[Dict[str, Any]]  # Will be transformed into CitationSource model

    # Control flow
    error_message: Optional[str]
