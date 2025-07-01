from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.documents import Document


class PageAnalysisResult(TypedDict):
    page_number: int
    page_text: str
    page_markdown: str


class AttachmentInfo(TypedDict):
    filename: str
    s3_path: Optional[str]
    extracted_text: str
    pages: List[str]  # Text content split by pages


class HierarchicalGraphState(TypedDict):
    # Input states
    attachment: AttachmentInfo  # Single file processing
    user_id: Optional[str]  # User's MongoDB ID

    # Page-by-page analysis
    page_analyses: List[PageAnalysisResult]

    # Master synthesis
    consolidated_markdown: str
    document_title: str

    # Final hierarchical structure
    hierarchical_data: Dict[str, Any]

    # DB Interaction results
    mongodb_doc_id: Optional[str]  # ID of the mind map document

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
