"""
Document processing nodes for VizMind AI LangGraph workflow.
Each node handles a specific step in the document processing pipeline.
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List
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


async def extract_outline_node(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """
    Node to extract a simple hierarchical outline from raw content.
    Uses indented text format - much more reliable than JSON for LLMs.
    Processes content in parallel using different ChatGroq API keys.
    """
    logger.info("[DocumentProcessing] Starting outline extraction")

    try:
        if not state.get("raw_content"):
            return set_error(state, "No raw content available for outline extraction")

        # Split content into manageable sections
        sections = _split_content_by_length(state["raw_content"], max_length=4000)

        if not sections:
            return set_error(state, "No content sections to process")

        logger.info(
            f"[DocumentProcessing] Processing {len(sections)} content sections in parallel"
        )

        # Process sections in parallel using different API keys
        section_outlines = await _process_sections_parallel(sections)

        # Filter out empty outlines
        valid_outlines = [outline for outline in section_outlines if outline.strip()]

        if not valid_outlines:
            return set_error(state, "No valid outline content extracted")

        # Merge section outlines
        merged_outline = "\n".join(valid_outlines)
        state["outline_text"] = merged_outline

        logger.info("[DocumentProcessing] Outline extracted successfully")
        return transition_stage(state, "outline_extracted")

    except Exception as e:
        logger.error(
            f"[DocumentProcessing] Outline extraction failed: {e}", exc_info=True
        )
        return set_error(state, f"Outline extraction failed: {str(e)}")


async def optimize_mind_map_node(
    state: DocumentProcessingState,
) -> DocumentProcessingState:
    """
    Node to optimize the extracted outline for mind mapping best practices.
    Removes duplicates, improves hierarchy, and ensures consistency.
    """
    logger.info("[DocumentProcessing] Starting mind map optimization")

    try:
        if not state.get("outline_text"):
            return set_error(state, "No outline text available for optimization")

        # Optimize the outline structure
        optimized_outline = await _optimize_mind_map_structure(state["outline_text"])
        state["outline_text"] = optimized_outline

        # Convert optimized outline to hierarchy
        hierarchical_data = _parse_outline_to_hierarchy(
            optimized_outline, state.get("original_filename", "Document")
        )
        state["hierarchical_data"] = hierarchical_data

        logger.info(
            "[DocumentProcessing] Mind map optimized and converted successfully"
        )
        return transition_stage(state, "mind_map_generated")

    except Exception as e:
        logger.error(
            f"[DocumentProcessing] Mind map optimization failed: {e}", exc_info=True
        )
        return set_error(state, f"Mind map optimization failed: {str(e)}")


async def _process_sections_parallel(sections: List[str]) -> List[str]:
    """
    Process content sections in parallel using different ChatGroq API keys.
    """
    # Get all available API keys
    api_keys = settings._get_groq_api_keys_list()

    outline_prompt = ChatPromptTemplate.from_template(
        """
        Extract the key concepts and structure from this document section as a simple indented outline.
        
        Processing section {section_index} of {total_sections}
        
        **Rules:**
        1. Use ONLY spaces for indentation (2 spaces per level)
        2. Maximum 4 levels deep
        3. Each line = one concept/topic
        4. Skip metadata, references, page numbers
        5. Focus on substantive content only
        6. Use clear, concise labels
        7. NO bullet points, numbers, or special characters
        8. Output ONLY the outline - no explanations

        **Format Example:**
        Main Topic A
          Subtopic 1
            Key Point 1
            Key Point 2
          Subtopic 2
        Main Topic B
          Important Concept
            Detail 1
            Detail 2

        **Content:**
        {section_content}

        **Outline:**
        """
    )

    # Create tasks for parallel processing
    tasks = []
    for i, section in enumerate(sections):
        # Rotate through available API keys
        api_key = api_keys[i % len(api_keys)]

        # Create LLM instance with specific API key
        llm = ChatGroq(
            temperature=0.0,
            groq_api_key=api_key,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )

        outline_chain = outline_prompt | llm | StrOutputParser()

        # Create async task
        task = _process_single_section(outline_chain, section, i + 1, len(sections))
        tasks.append(task)

    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results and handle exceptions
    section_outlines = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Failed to process section {i + 1}: {result}")
            continue

        # Clean and validate outline
        cleaned_outline = _clean_outline_text(result)
        if cleaned_outline:
            section_outlines.append(cleaned_outline)

    logger.info(
        f"[DocumentProcessing] Successfully processed {len(section_outlines)} sections out of {len(sections)}"
    )
    return section_outlines


async def _process_single_section(
    chain, section_content: str, section_index: int, total_sections: int
) -> str:
    """Process a single content section through the outline extraction chain."""
    try:
        result = await chain.ainvoke(
            {
                "section_content": section_content,
                "section_index": section_index,
                "total_sections": total_sections,
            }
        )
        return result
    except Exception as e:
        logger.warning(f"Section {section_index} processing failed: {e}")
        raise


async def chunk_content_node(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node to chunk the raw content for RAG ingestion.
    """
    logger.info("[DocumentProcessing] Starting content chunking")

    try:
        if not state.get("raw_content"):
            return set_error(state, "No raw content available for chunking")

        # Configure markdown header splitter
        headers_to_split_on = [("#", "H1"), ("##", "H2"), ("###", "H3"), ("####", "H4")]

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on, strip_headers=False
        )

        # Split the content
        chunks = markdown_splitter.split_text(state["raw_content"])

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


def _clean_outline_text(outline_text: str) -> str:
    """Clean and validate outline text format, removing duplicates."""
    lines = outline_text.split("\n")
    cleaned_lines = []
    seen_labels = set()  # Track labels to prevent duplicates

    for line in lines:
        # Skip empty lines and lines that are just explanations
        if not line.strip():
            continue
        if line.strip().startswith(("**", "Here", "The", "This", "Outline:", "Format")):
            continue

        # Count leading spaces for indentation
        stripped = line.lstrip()
        if not stripped:
            continue

        spaces = len(line) - len(stripped)
        # Normalize indentation to multiples of 2
        level = min(spaces // 2, 3)  # Max 4 levels (0-3)

        # Clean the content
        cleaned_content = stripped.strip("- *•").strip()
        if len(cleaned_content) <= 2:  # Skip very short items
            continue

        # Check for duplicates (case-insensitive)
        cleaned_lower = cleaned_content.lower()
        if cleaned_lower in seen_labels:
            continue

        # Add to seen labels and cleaned lines
        seen_labels.add(cleaned_lower)
        cleaned_lines.append("  " * level + cleaned_content)

    return "\n".join(cleaned_lines)


def _parse_outline_to_hierarchy(
    outline_text: str, fallback_name: str = "Document"
) -> Dict[str, Any]:
    """
    Parse indented outline text into hierarchical structure.
    Uses first hierarchy level as root node and prevents duplicates.
    """
    lines = outline_text.split("\n")

    # Filter out empty lines
    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines:
        # Use document name without extension as fallback
        clean_name = (
            fallback_name.replace(".pdf", "").replace(".docx", "").replace(".txt", "")
        )
        return {
            "id": str(uuid.uuid4()),
            "data": {"label": clean_name},
            "children": [],
        }

    # Find first top-level item to use as root
    root_line = None
    for line in non_empty_lines:
        content = line.lstrip()
        if content and (len(line) - len(content)) == 0:  # Top level (no indentation)
            root_line = line
            break

    if not root_line:
        # If no top-level item, use first line as root
        root_line = non_empty_lines[0]

    # Create root node from first top-level item
    root_label = root_line.strip()
    root = {"id": str(uuid.uuid4()), "data": {"label": root_label}, "children": []}

    # Track used labels to prevent duplicates
    used_labels = {root_label.lower()}

    # Stack to track current path in hierarchy
    node_stack = [root]

    # Process remaining lines, skipping the root line
    for line in non_empty_lines:
        if line.strip() == root_label:
            continue  # Skip the root line

        if not line.strip():
            continue

        # Calculate indentation level
        content = line.lstrip()
        if not content:
            continue

        level = (len(line) - len(content)) // 2
        label = content.strip()

        # Skip if this label already exists (case-insensitive)
        if label.lower() in used_labels:
            continue

        # Add to used labels
        used_labels.add(label.lower())

        # Create new node
        node = {
            "id": str(uuid.uuid4()),
            "data": {"label": label},
            "children": [],
        }

        # Adjust stack to correct level (accounting for root being level 0)
        target_stack_size = level + 1
        while len(node_stack) > target_stack_size:
            node_stack.pop()

        # Add node to parent
        if node_stack:
            node_stack[-1]["children"].append(node)
            node_stack.append(node)

    return root


def _split_content_by_length(content: str, max_length: int = 4000) -> List[str]:
    """Split content by length while preserving paragraph boundaries."""
    if len(content) <= max_length:
        return [content]

    paragraphs = content.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for paragraph in paragraphs:
        para_length = len(paragraph)

        # If single paragraph is too long, split it
        if para_length > max_length:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0

            # Split long paragraph by sentences
            sentences = paragraph.split(". ")
            temp_chunk = []
            temp_length = 0

            for sentence in sentences:
                sentence_length = len(sentence) + 2  # +2 for '. '
                if temp_length + sentence_length > max_length and temp_chunk:
                    chunks.append(". ".join(temp_chunk) + ".")
                    temp_chunk = [sentence]
                    temp_length = sentence_length
                else:
                    temp_chunk.append(sentence)
                    temp_length += sentence_length

            if temp_chunk:
                chunks.append(". ".join(temp_chunk))

        elif current_length + para_length > max_length and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_length = para_length
        else:
            current_chunk.append(paragraph)
            current_length += para_length + 2  # +2 for \n\n

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


async def _optimize_mind_map_structure(merged_outline: str) -> str:
    """
    Optimize the merged outline for mind mapping best practices.
    Removes duplicates, improves hierarchy, and ensures consistency.
    """
    logger.info("[DocumentProcessing] Optimizing mind map structure")

    # Initialize LLM for optimization
    llm = ChatGroq(
        temperature=0.1,  # Slightly higher for creative reorganization
        groq_api_key=settings.GROQ_API_KEY,
        model_name=settings.LLM_MODEL_NAME_GROQ,
    )

    optimization_prompt = ChatPromptTemplate.from_template(
        """
        You are a mind mapping expert. Optimize this outline for the best possible mind map experience.

        **Mind Map Best Practices to Apply:**
        1. **Remove Duplicates**: Merge identical or very similar concepts
        2. **Consistent Terminology**: Use the same terms for the same concepts
        3. **Optimal Hierarchy**: Maximum 4 levels, logical parent-child relationships
        4. **Concise Labels**: 1-5 words per concept, keywords not sentences
        5. **Logical Grouping**: Group related concepts together
        6. **Balanced Structure**: Avoid one branch being much larger than others
        7. **Meaningful Categories**: Ensure higher-level concepts meaningfully contain children
        8. **No Redundancy**: Each idea appears once in the most appropriate location

        **Current Outline to Optimize:**
        {outline_content}

        **Instructions:**
        - Maintain the indented format (2 spaces per level)
        - Keep all important information but remove duplicates
        - Reorganize for better logical flow and balance
        - Use clear, concise labels (prefer keywords over phrases)
        - Ensure parent concepts meaningfully contain child concepts
        - Maximum 4 levels of hierarchy
        - Output ONLY the optimized outline - no explanations

        **Optimized Outline:**
        """
    )

    optimization_chain = optimization_prompt | llm | StrOutputParser()

    try:
        optimized_result = await optimization_chain.ainvoke(
            {"outline_content": merged_outline}
        )

        # Clean the optimized outline
        cleaned_optimized = _clean_outline_text(optimized_result)

        if cleaned_optimized:
            logger.info(
                "[DocumentProcessing] Mind map structure optimized successfully"
            )
            return cleaned_optimized
        else:
            logger.warning(
                "[DocumentProcessing] Optimization produced empty result, using original"
            )
            return merged_outline

    except Exception as e:
        logger.warning(
            f"[DocumentProcessing] Mind map optimization failed: {e}, using original outline"
        )
        return merged_outline
