"""
Document processing nodes for VizMind AI LangGraph workflow.
Each node handles a specific step in the document processing pipeline.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from app.core.config import settings, logger
from app.services.docling_service import DoclingService
from app.db.mongodb_utils import get_db
from app.langgraph_pipeline.state import (
    DocumentProcessingState,
    transition_stage,
    set_error,
)


async def extract_content_node(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """
    Node to extract content from the uploaded document using Docling.
    """
    logger.info(
        f"[DocumentProcessing] Starting content extraction for {state['original_filename']}"
    )

    try:
        state["processing_start_time"] = datetime.utcnow().isoformat()

        # Initialize Docling service
        docling_service = DoclingService([state["file_path"]])
        raw_content = docling_service.get_markdown_content()

        if not raw_content:
            return set_error(state, "Failed to extract content from document")

        state["raw_content"] = raw_content
        logger.info(
            f"[DocumentProcessing] Content extracted successfully. Length: {len(raw_content)} chars"
        )

        return transition_stage(state, "content_extracted")

    except Exception as e:
        logger.error(
            f"[DocumentProcessing] Content extraction failed: {e}", exc_info=True
        )
        return set_error(state, f"Content extraction failed: {str(e)}")


async def clean_content_node(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node to clean and structure the extracted markdown content using LLM.
    """
    logger.info("[DocumentProcessing] Starting content cleaning")

    try:
        if not state.get("raw_content"):
            return set_error(state, "No raw content available for cleaning")

        # Initialize LLM
        llm = ChatGroq(
            temperature=0.0,
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )

        # Enhanced cleanup prompt for VizMind AI
        cleanup_prompt = ChatPromptTemplate.from_template(
            """
            You are a document structuring expert for VizMind AI, a mind mapping platform.
            
            Transform the following document into a well-structured markdown suitable for mind map generation.

            **Instructions:**
            1. **Create Clear Hierarchy:** Use proper heading levels (#, ##, ###, ####) to show information structure
            2. **Remove Noise:** Delete page numbers, headers, footers, and irrelevant formatting artifacts
            3. **Maintain Core Content:** Preserve all important information while improving organization
            4. **Bullet Points:** Convert long paragraphs into concise, meaningful bullet points
            5. **Logical Flow:** Ensure topics flow logically from general to specific
            6. **Consistent Style:** Use consistent markdown formatting throughout
            7. **Output ONLY the cleaned markdown - no explanations or meta-text**

            **Original Document:**
            ---
            {markdown_text}
            ---
            
            **Structured Markdown:**
            """
        )

        cleanup_chain = cleanup_prompt | llm | StrOutputParser()
        cleaned_content = await cleanup_chain.ainvoke(
            {"markdown_text": state["raw_content"]}
        )

        state["cleaned_markdown"] = cleaned_content
        logger.info(
            f"[DocumentProcessing] Content cleaned successfully. Length: {len(cleaned_content)} chars"
        )

        return transition_stage(state, "content_cleaned")

    except Exception as e:
        logger.error(
            f"[DocumentProcessing] Content cleaning failed: {e}", exc_info=True
        )
        return set_error(state, f"Content cleaning failed: {str(e)}")


async def generate_mind_map_node(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """
    Node to generate hierarchical mind map structure from cleaned content.
    """
    logger.info("[DocumentProcessing] Starting mind map generation")

    try:
        if not state.get("cleaned_markdown"):
            return set_error(
                state, "No cleaned content available for mind map generation"
            )

        # Parse markdown into hierarchical structure
        hierarchical_data = _parse_markdown_to_hierarchy(state["cleaned_markdown"])

        state["hierarchical_data"] = hierarchical_data
        logger.info("[DocumentProcessing] Mind map generated successfully")

        return transition_stage(state, "mind_map_generated")

    except Exception as e:
        logger.error(
            f"[DocumentProcessing] Mind map generation failed: {e}", exc_info=True
        )
        return set_error(state, f"Mind map generation failed: {str(e)}")


async def chunk_content_node(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node to chunk the cleaned content for RAG ingestion.
    """
    logger.info("[DocumentProcessing] Starting content chunking")

    try:
        if not state.get("cleaned_markdown"):
            return set_error(state, "No cleaned content available for chunking")

        # Configure markdown header splitter
        headers_to_split_on = [("#", "H1"), ("##", "H2"), ("###", "H3"), ("####", "H4")]

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on, strip_headers=False
        )

        # Split the content
        chunks = markdown_splitter.split_text(state["cleaned_markdown"])

        # Add metadata to chunks
        for chunk in chunks:
            chunk.metadata.update(
                {
                    "user_id": state["user_id"],
                    "map_id": state["map_id"],
                    "s3_path": state["s3_path"],
                    "original_filename": state["original_filename"],
                    "chunk_id": str(uuid.uuid4()),
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

        state["chunks"] = chunks
        state["chunk_count"] = len(chunks)
        logger.info(
            f"[DocumentProcessing] Content chunked successfully. Created {len(chunks)} chunks"
        )

        return transition_stage(state, "content_chunked")

    except Exception as e:
        logger.error(
            f"[DocumentProcessing] Content chunking failed: {e}", exc_info=True
        )
        return set_error(state, f"Content chunking failed: {str(e)}")


async def embed_and_store_node(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """
    Node to embed chunks and store them in MongoDB.
    """
    logger.info("[DocumentProcessing] Starting embedding and storage")

    try:
        chunks = state.get("chunks")
        if not chunks:
            return set_error(state, "No chunks available for embedding")

        # Initialize embedding model
        embedding_model = HuggingFaceEmbeddings(
            model_name=settings.MODEL_NAME_FOR_EMBEDDING
        )

        # Prepare texts for embedding
        texts_to_embed = [chunk.page_content for chunk in chunks]

        # Generate embeddings
        logger.info(
            f"[DocumentProcessing] Generating embeddings for {len(texts_to_embed)} chunks"
        )
        embeddings = embedding_model.embed_documents(texts_to_embed)

        # Prepare documents for MongoDB insertion
        db = get_db()
        chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]

        documents_to_insert = []
        for i, chunk in enumerate(chunks):
            doc = {
                "text": chunk.page_content,
                "embedding": embeddings[i],
                **chunk.metadata,
            }
            documents_to_insert.append(doc)

        # Insert into MongoDB
        result = chunks_collection.insert_many(documents_to_insert)

        state["embedding_dimension"] = len(embeddings[0]) if embeddings else None
        logger.info(
            f"[DocumentProcessing] Successfully stored {len(result.inserted_ids)} chunks in MongoDB"
        )

        return transition_stage(state, "chunks_embedded")

    except Exception as e:
        logger.error(
            f"[DocumentProcessing] Embedding and storage failed: {e}", exc_info=True
        )
        return set_error(state, f"Embedding and storage failed: {str(e)}")


async def finalize_processing_node(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """
    Node to finalize the document processing workflow.
    """
    logger.info("[DocumentProcessing] Finalizing processing")

    try:
        state["processing_end_time"] = datetime.utcnow().isoformat()

        # Store mind map document in MongoDB
        if state.get("hierarchical_data"):
            db = get_db()
            maps_collection = db[settings.MONGODB_MAPS_COLLECTION]

            from bson import ObjectId

            map_document = {
                "_id": ObjectId(state["map_id"]),
                "user_id": state["user_id"],
                "title": state["original_filename"].replace(".pdf", ""),
                "original_filename": state["original_filename"],
                "s3_path": state["s3_path"],
                "hierarchical_data": state["hierarchical_data"],
                "processing_metadata": {
                    "chunk_count": state.get("chunk_count"),
                    "embedding_dimension": state.get("embedding_dimension"),
                    "processing_start_time": state.get("processing_start_time"),
                    "processing_end_time": state.get("processing_end_time"),
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            maps_collection.insert_one(map_document)
            logger.info(
                f"[DocumentProcessing] Mind map document stored with ID: {state['map_id']}"
            )

        return transition_stage(state, "completed")

    except Exception as e:
        logger.error(f"[DocumentProcessing] Finalization failed: {e}", exc_info=True)
        return set_error(state, f"Finalization failed: {str(e)}")


def _parse_markdown_to_hierarchy(markdown_content: str) -> Dict[str, Any]:
    """
    Parse markdown content into a hierarchical dictionary structure.
    Enhanced version with better title extraction and structure.
    """
    lines = markdown_content.split("\n")

    # Find the main title
    root_title = "Document"
    for line in lines:
        if line.startswith("# "):
            root_title = line[2:].strip()
            break

    # Initialize root node
    root = {"id": str(uuid.uuid4()), "data": {"label": root_title}, "children": []}

    # Track the path for proper nesting
    path = [root]

    for line in lines:
        stripped_line = line.strip()

        # Handle headers
        if stripped_line.startswith("#"):
            level = 0
            while level < len(stripped_line) and stripped_line[level] == "#":
                level += 1

            title = stripped_line[level:].strip()
            if not title:
                continue

            # Clean title
            cleaned_title = _clean_title(title)
            if not cleaned_title:
                continue

            # Create node
            node = {
                "id": str(uuid.uuid4()),
                "data": {"label": cleaned_title},
                "children": [],
            }

            # Adjust path to correct level
            while len(path) > level:
                path.pop()

            # Add to parent
            if path:
                path[-1]["children"].append(node)
            path.append(node)

        # Handle bullet points
        elif stripped_line.startswith(("-", "*", "+")) and len(stripped_line) > 1:
            title = stripped_line[1:].strip()
            if not title or not path:
                continue

            cleaned_title = _clean_title(title)
            if not cleaned_title:
                continue

            node = {
                "id": str(uuid.uuid4()),
                "data": {"label": cleaned_title},
                "children": [],
            }
            path[-1]["children"].append(node)

    return root


def _clean_title(title: str) -> str:
    """Clean and normalize title text."""
    # Remove special characters and bullets
    cleaned = title.replace("\uf0b7", "").strip()
    if cleaned.startswith("•"):
        cleaned = cleaned[1:].strip()

    # Remove excessive whitespace
    cleaned = " ".join(cleaned.split())

    return cleaned
