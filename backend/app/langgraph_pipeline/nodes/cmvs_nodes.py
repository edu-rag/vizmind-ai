import asyncio
import numpy as np
import json
import re
import datetime
from typing import List, Dict, Any, Optional

# Langchain & supporting libs
from langchain_groq import ChatGroq
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import (
    HuggingFaceEmbeddings,
)
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# App specific imports
from app.core.config import settings, logger
from app.langgraph_pipeline.state import GraphState, EmbeddedChunk
from app.models.cmvs_models import ConceptTripleLLM, ExtractedTriplesLLM

from app.db.mongodb_utils import get_db
from app.utils.cmvs_helpers import normalize_label, generate_react_flow_data

import datetime
from pymongo import ReturnDocument

try:
    from pymongo.common import UTC
except ImportError:
    import datetime as pydt

    UTC = pydt.timezone.utc


class CMVSNodes:
    def __init__(self, groq_api_key: str, embedding_model_name: str):
        logger.info(
            f"Initializing CMVSNodes with embedding model: {embedding_model_name}"
        )
        self.llm = ChatGroq(
            temperature=0,  # Low temperature for more factual, less creative output
            groq_api_key=groq_api_key,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )
        self.embedding_model_lc = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
        )
        self.text_splitter = SemanticChunker(
            self.embedding_model_lc, breakpoint_threshold_type="percentile"
        )
        self.similarity_embedding_model = SentenceTransformer(embedding_model_name)
        logger.info("CMVSNodes initialized.")

    async def chunk_text(self, state: GraphState) -> Dict[str, Any]:
        attachments = state.get("attachments", [])
        attachment_names = [att.get("filename", "Unknown") for att in attachments]
        logger.info(
            f"--- Node: Hierarchical Chunking Text (Attachments: {', '.join(attachment_names)}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            text = state["original_text"]
            if not text or not text.strip():
                return {
                    "error_message": "Input text is empty.",
                    "hierarchical_chunks": [],
                    "embedded_chunks": [],
                }

            # First, create hierarchical chunks based on document structure
            hierarchical_chunks = await self._create_hierarchical_chunks(attachments)

            # Also create semantic chunks for fallback/comparison
            semantic_chunks = await asyncio.to_thread(
                self.text_splitter.split_text, text
            )

            logger.info(
                f"Created {len(hierarchical_chunks)} hierarchical chunks and {len(semantic_chunks)} semantic chunks from {len(attachments)} attachment(s)."
            )

            return {
                "hierarchical_chunks": hierarchical_chunks,
                "error_message": None,
                "embedded_chunks": state.get("embedded_chunks", []),
            }
        except Exception as e:
            logger.error(f"Error in hierarchical chunk_text: {e}", exc_info=True)
            return {
                "error_message": str(e),
                "hierarchical_chunks": [],
                "embedded_chunks": state.get("embedded_chunks", []),
            }

    async def _create_hierarchical_chunks(
        self, attachments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create hierarchical chunks based on document structure (headers, sections).
        Uses the new hierarchical structured_content format for context-aware chunking.
        """
        from app.langgraph_pipeline.state import HierarchicalChunk

        hierarchical_chunks = []

        for attachment in attachments:
            # Use hierarchical structure
            hierarchical_content = attachment.get("structured_content")
            filename = attachment.get("filename", "Unknown")

            if hierarchical_content:
                # Process hierarchical structure
                chunk_index = 0
                chunks_from_hierarchy = await self._process_hierarchical_node(
                    hierarchical_content, [], filename, chunk_index
                )
                hierarchical_chunks.extend(chunks_from_hierarchy)

            else:
                # Final fallback to plain text chunking
                plain_text = attachment.get("extracted_text", "")
                if plain_text:
                    semantic_chunks = await asyncio.to_thread(
                        self.text_splitter.split_text, plain_text
                    )
                    for i, chunk in enumerate(semantic_chunks):
                        hierarchical_chunks.append(
                            HierarchicalChunk(
                                text=chunk,
                                hierarchy_level=4,  # Body text level
                                parent_headers=[],
                                section_title=None,
                                chunk_index=len(hierarchical_chunks),
                                source_filename=filename,
                                page_number=None,
                            )
                        )

        logger.info(
            f"Created {len(hierarchical_chunks)} hierarchical chunks with structure-aware segmentation"
        )
        return hierarchical_chunks

    async def _process_hierarchical_node(
        self,
        node: Dict[str, Any],
        parent_headers: List[Dict[str, Any]],
        filename: str,
        chunk_index: int,
    ) -> List[Dict[str, Any]]:
        """
        Recursively process a hierarchical node to create chunks with proper context.
        """
        from app.langgraph_pipeline.state import HierarchicalChunk

        chunks = []
        title = node.get("title", "")
        text = node.get("text", "")
        children = node.get("children", [])

        # Create header info for this node
        current_header = {
            "text": title,
            "level": len(parent_headers) + 1 if parent_headers else 1,
        }

        # Add chunk for this node's content if it has substantial text
        if text and len(text.strip()) > 50:
            # Determine appropriate chunk size based on content
            if len(text) > 2000:
                # Split large content into smaller chunks while preserving context
                text_chunks = await asyncio.to_thread(
                    self.text_splitter.split_text, text
                )
                for chunk_text in text_chunks:
                    chunks.append(
                        HierarchicalChunk(
                            text=chunk_text,
                            hierarchy_level=len(parent_headers) + 1,
                            parent_headers=parent_headers.copy(),
                            section_title=title,
                            chunk_index=chunk_index,
                            source_filename=filename,
                            page_number=None,
                        )
                    )
                    chunk_index += 1
            else:
                # Keep as single chunk with hierarchical context
                chunks.append(
                    HierarchicalChunk(
                        text=text,
                        hierarchy_level=len(parent_headers) + 1,
                        parent_headers=parent_headers.copy(),
                        section_title=title,
                        chunk_index=chunk_index,
                        source_filename=filename,
                        page_number=None,
                    )
                )
                chunk_index += 1

        # Process children with updated parent headers
        new_parent_headers = (
            parent_headers + [current_header] if title else parent_headers
        )
        for child in children:
            child_chunks = await self._process_hierarchical_node(
                child, new_parent_headers, filename, chunk_index
            )
            chunks.extend(child_chunks)
            chunk_index += len(child_chunks)

        return chunks

    async def embed_hierarchical_chunks(self, state: GraphState) -> Dict[str, Any]:
        """
        Embeds hierarchical chunks using sentence transformers.
        """
        attachments = state.get("attachments", [])
        attachment_names = [att.get("filename", "Unknown") for att in attachments]
        logger.info(
            f"--- Node: Embedding Hierarchical Text Chunks (Attachments: {', '.join(attachment_names)}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            # Use hierarchical chunks for embedding
            hierarchical_chunks = state.get("hierarchical_chunks", [])

            if hierarchical_chunks:
                # Use hierarchical chunks for embedding
                chunk_texts = [chunk["text"] for chunk in hierarchical_chunks]
                embeddings_list = await asyncio.to_thread(
                    self.embedding_model_lc.embed_documents, chunk_texts
                )

                embedded_chunks_data = []
                for i, (hierarchical_chunk, embedding) in enumerate(
                    zip(hierarchical_chunks, embeddings_list)
                ):
                    # Create enhanced context from parent headers for better embedding and retrieval
                    context_text = hierarchical_chunk["text"]
                    section_title = hierarchical_chunk.get("section_title", "")
                    parent_headers = hierarchical_chunk.get("parent_headers", [])

                    # Build hierarchical context for better RAG retrieval
                    if parent_headers:
                        header_path = " → ".join([h["text"] for h in parent_headers])
                        if section_title and section_title not in header_path:
                            header_path += f" → {section_title}"
                        context_text = f"[Context: {header_path}]\n\n{context_text}"
                    elif section_title:
                        context_text = f"[Section: {section_title}]\n\n{context_text}"

                    embedded_chunks_data.append(
                        {
                            "text": context_text,
                            "embedding": embedding,
                            "source_filename": hierarchical_chunk.get(
                                "source_filename"
                            ),
                            "source_s3_path": self._get_s3_path_for_filename(
                                hierarchical_chunk.get("source_filename"), attachments
                            ),
                            "hierarchy_level": hierarchical_chunk.get(
                                "hierarchy_level"
                            ),
                            "section_title": section_title,
                            "parent_headers": parent_headers,
                            "page_number": hierarchical_chunk.get("page_number"),
                            "chunk_type": self._determine_chunk_type(
                                hierarchical_chunk
                            ),
                        }
                    )

                logger.info(
                    f"Successfully embedded {len(embedded_chunks_data)} hierarchical chunks"
                )

            else:
                logger.info("No hierarchical chunks to embed.")
                return {"embedded_chunks": []}

            return {"embedded_chunks": embedded_chunks_data}

        except Exception as e:
            logger.error(f"Error in embed_hierarchical_chunks: {e}", exc_info=True)
            return {
                "error_message": f"Failed to embed chunks: {str(e)}",
                "embedded_chunks": [],
            }

    def _get_s3_path_for_filename(
        self, filename: str, attachments: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Get S3 path for a given filename from attachments."""
        if not filename:
            return None
        for attachment in attachments:
            if attachment.get("filename") == filename:
                return attachment.get("s3_path")
        return None

    def _determine_chunk_type(self, hierarchical_chunk: Dict[str, Any]) -> str:
        """Determine the type of chunk based on hierarchy level and content."""
        hierarchy_level = hierarchical_chunk.get("hierarchy_level", 4)
        text = hierarchical_chunk.get("text", "").lower()

        if hierarchy_level <= 1:
            return "title"
        elif hierarchy_level == 2:
            return "chapter"
        elif hierarchy_level == 3:
            return "section"
        elif "conclusion" in text or "summary" in text:
            return "conclusion"
        elif "introduction" in text or "overview" in text:
            return "introduction"
        else:
            return "body"

    def _determine_chunk_source(
        self, chunk_text: str, attachments: List[Dict[str, Any]]
    ) -> tuple[Optional[str], Optional[str]]:
        """Determine source filename and S3 path for a chunk (fallback method)."""
        # Look for document separator patterns in the chunk
        for attachment in attachments:
            filename = attachment.get("filename", "")
            if f"--- Document: {filename} ---" in chunk_text:
                return filename, attachment.get("s3_path")

        # If we can't determine from separator, try to match against original text segments
        if attachments:
            chunk_clean = chunk_text.replace(f"--- Document:", "").strip()
            max_overlap = 0
            best_match = None

            for attachment in attachments:
                attachment_text = attachment.get("extracted_text", "")
                if attachment_text and chunk_clean in attachment_text:
                    overlap = len(chunk_clean)
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_match = attachment

            if best_match:
                return best_match.get("filename"), best_match.get("s3_path")

        return None, None

    async def generate_react_flow(self, state: GraphState) -> Dict[str, Any]:
        attachments = state.get("attachments", [])
        attachment_names = [att.get("filename", "Unknown") for att in attachments]
        logger.info(
            f"--- Node: Generating React Flow Data from Document Structure (Attachments: {', '.join(attachment_names)}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            # Extract hierarchy titles directly from hierarchical chunks
            hierarchical_chunks = state.get("hierarchical_chunks", [])

            logger.info(f"Found {len(hierarchical_chunks)} hierarchical chunks")

            if not hierarchical_chunks:
                logger.warning(
                    "No hierarchical chunks found, generating minimal structure"
                )
                return {
                    "react_flow_data": self._create_fallback_react_flow(),
                    "processed_triples": [],
                    "hierarchical_concepts": {},
                    "error_message": "No hierarchical structure found in document.",
                }

            # Extract titles directly from hierarchical structure
            hierarchy_titles = self._extract_hierarchy_titles(
                hierarchical_chunks, attachments
            )

            logger.info(
                f"Extracted {len(hierarchy_titles)} hierarchy titles for LLM processing"
            )

            # Generate React Flow data directly via LLM
            react_flow_data = await self._generate_react_flow_with_llm(hierarchy_titles)

            logger.info(
                f"Generated react_flow_data with {len(react_flow_data.get('nodes', []))} nodes and {len(react_flow_data.get('edges', []))} edges"
            )

            return {
                "react_flow_data": react_flow_data,
                "processed_triples": [],  # No longer needed with direct LLM approach
                "hierarchical_concepts": {"titles": hierarchy_titles},
                "error_message": None,
            }

        except Exception as e:
            logger.error(f"Error in generate_react_flow: {e}", exc_info=True)
            return {
                "react_flow_data": self._create_fallback_react_flow(),
                "processed_triples": [],
                "hierarchical_concepts": {},
                "error_message": str(e),
            }

    async def store_cmvs_data_in_mongodb(self, state: GraphState) -> Dict[str, Any]:
        attachments = state.get("attachments", [])
        attachment_names = [att.get("filename", "Unknown") for att in attachments]
        logger.info(
            f"--- Node: Storing Main Map & All Chunks in MongoDB (Attachments: {', '.join(attachment_names)}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            processed_triples = state.get("processed_triples", [])
            user_id = state.get("user_id")
            embedded_chunks = state.get("embedded_chunks", [])
            original_text = state.get("original_text", "")
            react_flow_data = state.get("react_flow_data")

            if not processed_triples and not embedded_chunks:
                return {
                    "mongodb_doc_id": None,
                    "mongodb_chunk_ids": [],
                    "error_message": state.get("error_message")
                    or "No processed data to store.",
                }
            if not user_id:
                return {
                    "mongodb_doc_id": None,
                    "mongodb_chunk_ids": [],
                    "error_message": "User ID missing.",
                }

            db = get_db()

            cm_collection = db[settings.MONGODB_CMVS_COLLECTION]
            chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]

            def _db_operations_sync():
                main_doc_id_obj = None
                stored_chunk_ids_obj = []

                if processed_triples:
                    # Create a unified title from all attachments
                    unified_title = ", ".join(
                        [att.get("filename", "Unknown") for att in attachments]
                    )
                    if len(unified_title) > 100:  # Truncate if too long
                        unified_title = unified_title[:97] + "..."

                    main_doc_to_insert = {
                        "user_id": user_id,
                        "unified_title": unified_title,
                        "attachments": [
                            {
                                "filename": att.get("filename", "Unknown"),
                                "s3_path": att.get("s3_path"),
                            }
                            for att in attachments
                        ],
                        "original_text_snippet": original_text[:500]
                        + ("..." if len(original_text) > 500 else ""),
                        "triples": processed_triples,
                        "react_flow_data": react_flow_data,
                        "created_at": datetime.datetime.now(UTC),
                    }
                    main_result = cm_collection.insert_one(main_doc_to_insert)
                    main_doc_id_obj = main_result.inserted_id

                if embedded_chunks:
                    chunk_docs_to_insert = []
                    for emb_chunk in embedded_chunks:
                        chunk_docs_to_insert.append(
                            {
                                "concept_map_id": (
                                    str(main_doc_id_obj) if main_doc_id_obj else None
                                ),
                                "user_id": user_id,
                                "text": emb_chunk["text"],
                                "embedding": emb_chunk["embedding"],
                                "source_filename": emb_chunk.get("source_filename"),
                                "source_s3_path": emb_chunk.get("source_s3_path"),
                                "hierarchy_level": emb_chunk.get(
                                    "hierarchy_level"
                                ),  # Store hierarchy level
                                "page_number": emb_chunk.get(
                                    "page_number"
                                ),  # Store page number
                                "chunk_type": emb_chunk.get(
                                    "chunk_type"
                                ),  # Store chunk type
                                "created_at": datetime.datetime.now(UTC),
                            }
                        )
                    if chunk_docs_to_insert:
                        chunk_results = chunks_collection.insert_many(
                            chunk_docs_to_insert
                        )
                        stored_chunk_ids_obj = chunk_results.inserted_ids

                return str(main_doc_id_obj) if main_doc_id_obj else None, [
                    str(id_val) for id_val in stored_chunk_ids_obj
                ]

            doc_id_str, chunk_ids_str = await asyncio.to_thread(_db_operations_sync)
            return {
                "mongodb_doc_id": doc_id_str,
                "mongodb_chunk_ids": chunk_ids_str,
                "error_message": None,
            }
        except Exception as e:
            logger.error(f"Error in store_cmvs_data_in_mongodb: {e}", exc_info=True)
            return {
                "mongodb_doc_id": None,
                "mongodb_chunk_ids": [],
                "error_message": str(e),
            }

    def _extract_hierarchy_titles(
        self,
        hierarchical_chunks: List[Dict[str, Any]],
        attachments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Extract hierarchy titles directly from structured_content in attachments.
        Returns only the titles without full text content for efficient LLM processing.
        """
        # Get document title from attachments
        document_title = "Document"
        if attachments:
            document_title = ", ".join(
                [att.get("filename", "Unknown") for att in attachments]
            )
            if len(document_title) > 100:
                document_title = document_title[:97] + "..."

        # Extract hierarchy directly from structured_content (preserve original nesting)
        nested_hierarchy = []
        total_titles = 0

        for attachment in attachments:
            structured_content = attachment.get("structured_content")
            if structured_content:
                logger.info(
                    f"Extracting hierarchy from structured_content for {attachment.get('filename', 'Unknown')}"
                )

                # Extract hierarchy while preserving nesting structure
                extracted_hierarchy = self._extract_nested_titles_from_content(
                    structured_content
                )
                if extracted_hierarchy:
                    nested_hierarchy.append(extracted_hierarchy)
                    total_titles += self._count_titles_recursive([extracted_hierarchy])

        if not nested_hierarchy:
            logger.warning(
                "No structured_content found in attachments, hierarchy will be empty"
            )

        logger.info(f"Extracted complete hierarchy with {total_titles} total titles")

        return {
            "document_title": document_title,
            "hierarchy": nested_hierarchy,
            "total_titles": total_titles,
        }

    def _extract_nested_titles_from_content(
        self, structured_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract titles directly from structured content while preserving the nested hierarchy.
        This maintains the original structure as created during PDF parsing.
        """

        def extract_recursive(node: Dict[str, Any], level: int = 0) -> Dict[str, Any]:
            title = node.get("title", "").strip()
            if not title:
                return None

            extracted = {"title": title, "level": level, "children": []}

            # Process children recursively to maintain hierarchy
            for child in node.get("children", []):
                child_data = extract_recursive(child, level + 1)
                if child_data:
                    extracted["children"].append(child_data)

            return extracted

        return extract_recursive(structured_content)

    def _extract_titles_from_structured_content(
        self, structured_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract titles directly from structured content recursively (flattened)"""
        titles = []

        def extract_recursive(node: Dict[str, Any], level: int = 0) -> None:
            title = node.get("title", "").strip()
            if title:
                titles.append(
                    {
                        "title": title,
                        "level": level,
                        "parent_headers": [],  # Will be filled in _build_nested_hierarchy
                    }
                )

            # Process children
            for child in node.get("children", []):
                extract_recursive(child, level + 1)

        extract_recursive(structured_content)
        return titles

    def _build_nested_hierarchy(
        self, flat_titles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build nested hierarchy structure from flat list of titles"""
        if not flat_titles:
            return []

        # Sort by level to process from top to bottom
        sorted_titles = sorted(flat_titles, key=lambda x: x.get("level", 0))

        # Build nested structure
        nested = []
        stack = []  # Stack to track parent hierarchy

        for title_info in sorted_titles:
            title = title_info["title"]
            level = title_info.get("level", 0)

            # Create title node
            title_node = {"title": title, "level": level, "children": []}

            # Adjust stack based on current level
            while stack and stack[-1]["level"] >= level:
                stack.pop()

            # Add to parent or root
            if stack:
                stack[-1]["children"].append(title_node)
            else:
                nested.append(title_node)

            # Add current node to stack
            stack.append(title_node)

        return nested

    def _count_titles_recursive(self, hierarchy: List[Dict[str, Any]]) -> int:
        """Count total number of titles in hierarchy recursively"""
        count = 0
        for node in hierarchy:
            count += 1  # Current node
            count += self._count_titles_recursive(node.get("children", []))
        return count

    async def _generate_react_flow_with_llm(
        self, hierarchy_titles: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate React Flow data from hierarchy titles with proper positioning.
        Uses deterministic positioning algorithm for ordered layout.
        """
        document_title = hierarchy_titles.get("document_title", "Document")
        hierarchy = hierarchy_titles.get("hierarchy", [])
        total_titles = hierarchy_titles.get("total_titles", 0)

        logger.info(
            f"Generating React Flow with {total_titles} titles from {len(hierarchy)} top-level nodes"
        )

        if not hierarchy:
            logger.warning("No hierarchy titles found, creating fallback")
            return self._create_fallback_react_flow()

        # Generate React Flow data with proper hierarchical positioning
        return self._create_hierarchical_react_flow(document_title, hierarchy)

    def _create_fallback_react_flow(self) -> Dict[str, Any]:
        """Create a simple fallback React Flow structure when hierarchy processing fails"""
        return {
            "nodes": [
                {
                    "id": "fallback-document",
                    "type": "default",
                    "data": {
                        "label": "Document Structure",
                        "level": 0,
                        "nodeType": "document",
                    },
                    "position": {"x": 50, "y": 50},
                    "style": self._get_node_style(0),
                },
                {
                    "id": "fallback-content",
                    "type": "default",
                    "data": {"label": "Content", "level": 1, "nodeType": "content"},
                    "position": {"x": 350, "y": 130},
                    "style": self._get_node_style(1),
                },
            ],
            "edges": [
                {
                    "id": "edge-fallback-document-content",
                    "source": "fallback-document",
                    "target": "fallback-content",
                    "type": "default",
                    "style": {"stroke": "#b1b1b7", "strokeWidth": 2},
                }
            ],
        }

    def _create_hierarchical_react_flow(
        self, document_title: str, hierarchy: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create React Flow data with proper horizontal hierarchical positioning.
        Uses tree-like layout with horizontal separation of siblings.
        """
        nodes = []
        edges = []

        # Layout configuration
        LEVEL_HEIGHT = 150  # Vertical spacing between hierarchy levels
        NODE_WIDTH = 250  # Horizontal spacing between sibling nodes
        START_X = 50  # Starting X position
        START_Y = 50  # Starting Y position

        # Create node ID mapping
        node_id_map = {}
        node_counter = 0

        def create_clean_node_id(title: str) -> str:
            nonlocal node_counter
            node_counter += 1
            # Create clean ID from title
            clean_title = re.sub(r"[^a-zA-Z0-9\s]", "", title)
            clean_title = re.sub(r"\s+", "-", clean_title.strip()).lower()
            if len(clean_title) > 30:
                clean_title = clean_title[:30]
            return f"{clean_title}-{node_counter}"

        def calculate_subtree_width(node: Dict[str, Any]) -> int:
            """Calculate the total width needed for a subtree"""
            children = node.get("children", [])
            if not children:
                return 1  # Single node width

            # Sum up all children widths
            total_width = sum(calculate_subtree_width(child) for child in children)
            return max(1, total_width)  # At least 1 for the parent node

        def position_nodes_horizontally(
            nodes_list: List[Dict[str, Any]],
            level: int = 0,
            start_x: int = START_X,
            parent_id: str = None,
        ) -> int:
            """
            Position nodes horizontally at the same level.
            Returns the next available X position.
            """
            current_x = start_x
            level_y = START_Y + level * LEVEL_HEIGHT

            for node in nodes_list:
                title = node.get("title", "").strip()
                if not title:
                    continue

                # Create or get node ID
                if title not in node_id_map:
                    node_id_map[title] = create_clean_node_id(title)
                node_id = node_id_map[title]

                # Calculate subtree width to center parent over children
                subtree_width = calculate_subtree_width(node)
                children = node.get("children", [])

                # If node has children, center it over them
                if children:
                    # Calculate total width needed for children
                    children_total_width = sum(
                        calculate_subtree_width(child) for child in children
                    )
                    children_pixel_width = children_total_width * NODE_WIDTH

                    # Center parent over children
                    node_x = current_x + (children_pixel_width - NODE_WIDTH) // 2
                    # Ensure minimum spacing
                    node_x = max(node_x, current_x)
                else:
                    node_x = current_x

                # Create React Flow node
                react_node = {
                    "id": node_id,
                    "type": "default",
                    "data": {
                        "label": title,
                        "level": level,
                        "nodeType": self._determine_node_type(title, level),
                    },
                    "position": {"x": node_x, "y": level_y},
                    "style": self._get_node_style(level),
                }

                nodes.append(react_node)

                # Create edge to parent
                if parent_id:
                    edge_id = f"edge-{parent_id}-{node_id}"
                    edge = {
                        "id": edge_id,
                        "source": parent_id,
                        "target": node_id,
                        "type": "default",
                        "style": {"stroke": "#b1b1b7", "strokeWidth": 2},
                        "animated": False,
                    }
                    edges.append(edge)

                # Process children recursively
                if children:
                    children_start_x = current_x
                    position_nodes_horizontally(
                        children, level + 1, children_start_x, node_id
                    )

                # Move to next position for siblings
                current_x += subtree_width * NODE_WIDTH

            return current_x

        # Add document root node if multiple top-level sections
        root_node_id = None
        start_level = 0

        if len(hierarchy) > 1:
            root_node_id = create_clean_node_id(document_title)

            # Calculate total width for all top-level sections
            total_top_level_width = sum(
                calculate_subtree_width(node) for node in hierarchy
            )
            root_x = START_X + (total_top_level_width * NODE_WIDTH - NODE_WIDTH) // 2

            root_node = {
                "id": root_node_id,
                "type": "default",
                "data": {"label": document_title, "level": 0, "nodeType": "document"},
                "position": {"x": root_x, "y": START_Y},
                "style": self._get_node_style(0),
            }
            nodes.append(root_node)
            start_level = 1

        # Position all hierarchy nodes
        position_nodes_horizontally(hierarchy, start_level, START_X, root_node_id)

        # Connect top-level nodes to root if root exists
        if root_node_id:
            for node in hierarchy:
                title = node.get("title", "").strip()
                if title and title in node_id_map:
                    child_id = node_id_map[title]
                    edge_id = f"edge-{root_node_id}-{child_id}"
                    edge = {
                        "id": edge_id,
                        "source": root_node_id,
                        "target": child_id,
                        "type": "default",
                        "style": {"stroke": "#b1b1b7", "strokeWidth": 2},
                        "animated": False,
                    }
                    edges.append(edge)

        logger.info(
            f"Created horizontal React Flow with {len(nodes)} nodes and {len(edges)} edges"
        )

        # Log positioning verification
        if nodes:
            # Group nodes by level to show horizontal distribution
            nodes_by_level = {}
            for node in nodes:
                level = node["data"]["level"]
                if level not in nodes_by_level:
                    nodes_by_level[level] = []
                nodes_by_level[level].append(node)

            logger.info("Horizontal layout by level:")
            for level in sorted(nodes_by_level.keys()):
                level_nodes = sorted(
                    nodes_by_level[level], key=lambda n: n["position"]["x"]
                )
                x_positions = [n["position"]["x"] for n in level_nodes]
                labels = [
                    (
                        n["data"]["label"][:30] + "..."
                        if len(n["data"]["label"]) > 30
                        else n["data"]["label"]
                    )
                    for n in level_nodes
                ]
                logger.info(
                    f"  Level {level}: {len(level_nodes)} nodes at X positions {x_positions}"
                )
                logger.info(f"    Labels: {labels}")

        return {"nodes": nodes, "edges": edges}

    def _determine_node_type(self, title: str, level: int) -> str:
        """Determine node type based on title content and hierarchy level"""
        title_lower = title.lower()

        if level == 0:
            return "document"
        elif level == 1:
            return "chapter"
        elif level == 2:
            return "section"
        elif "introduction" in title_lower or "overview" in title_lower:
            return "introduction"
        elif "conclusion" in title_lower or "summary" in title_lower:
            return "conclusion"
        elif "methodology" in title_lower or "method" in title_lower:
            return "methodology"
        elif "result" in title_lower or "finding" in title_lower:
            return "results"
        elif "reference" in title_lower or "bibliography" in title_lower:
            return "references"
        else:
            return "content"

    def _get_node_style(self, level: int) -> Dict[str, Any]:
        """Get styling for nodes based on hierarchy level"""
        base_style = {
            "border": "2px solid",
            "borderRadius": "8px",
            "padding": "10px",
            "fontSize": "14px",
            "fontWeight": "500",
        }

        # Color scheme based on level
        if level == 0:
            # Document root - dark blue
            base_style.update(
                {
                    "backgroundColor": "#1e40af",
                    "borderColor": "#1e3a8a",
                    "color": "white",
                    "fontSize": "16px",
                    "fontWeight": "600",
                }
            )
        elif level == 1:
            # Top level - blue
            base_style.update(
                {
                    "backgroundColor": "#3b82f6",
                    "borderColor": "#2563eb",
                    "color": "white",
                    "fontSize": "15px",
                }
            )
        elif level == 2:
            # Second level - light blue
            base_style.update(
                {
                    "backgroundColor": "#60a5fa",
                    "borderColor": "#3b82f6",
                    "color": "white",
                }
            )
        elif level == 3:
            # Third level - lighter blue
            base_style.update(
                {
                    "backgroundColor": "#93c5fd",
                    "borderColor": "#60a5fa",
                    "color": "#1e40af",
                }
            )
        else:
            # Deeper levels - very light blue
            base_style.update(
                {
                    "backgroundColor": "#dbeafe",
                    "borderColor": "#93c5fd",
                    "color": "#1e40af",
                }
            )

        return base_style
