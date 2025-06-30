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
        try:
            self.structured_llm = self.llm.with_structured_output(ExtractedTriplesLLM)
            self.use_structured_output = True
            logger.info("Using structured output for triple extraction.")
        except Exception as e:
            logger.warning(
                f"Structured output for ExtractedTriplesLLM not fully compatible or available, may use fallback: {e}"
            )
            self.structured_llm = (
                None  # Fallback to manual parsing if this specific model fails
            )
            self.use_structured_output = False

        self.embedding_model_lc = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
        )
        self.text_splitter = SemanticChunker(
            self.embedding_model_lc, breakpoint_threshold_type="percentile"
        )
        self.similarity_embedding_model = SentenceTransformer(embedding_model_name)
        logger.info("CMVSNodes initialized.")

    def _parse_triples_from_text(self, llm_output_text: str) -> List[Dict[str, str]]:
        """
        Robustly parse triples from LLM text response, looking for JSON.
        """
        triples = []
        # Ensure llm_output_text is a string
        if not isinstance(llm_output_text, str):
            logger.warning(
                f"LLM output is not a string: {type(llm_output_text)}. Cannot parse triples."
            )
            return []

        try:
            # Attempt to find a JSON block within the text that matches the expected structure
            # This regex is a bit more flexible for finding the JSON list of triples
            json_match = re.search(
                r'{\s*"triples"\s*:\s*\[.*?\]\s*}', llm_output_text, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(0)
                logger.debug(f"Found JSON block for triples: {json_str}")
                data = json.loads(json_str)
                if "triples" in data and isinstance(data["triples"], list):
                    for triple_item in data["triples"]:
                        if (
                            isinstance(triple_item, dict)
                            and "source" in triple_item
                            and "target" in triple_item
                            and "relation" in triple_item
                        ):
                            triples.append(
                                {
                                    "source": str(triple_item["source"]),
                                    "target": str(triple_item["target"]),
                                    "relation": str(triple_item["relation"]),
                                }
                            )
                    logger.info(
                        f"Successfully parsed {len(triples)} triples from JSON block."
                    )
                    return triples

            # If no specific block found, try to parse the whole string if it looks like JSON
            # This is a fallback and might be less reliable
            logger.debug(
                "No specific '{\"triples\": [...]}' block found, attempting to parse entire output as JSON if it starts with { or [."
            )
            stripped_output = llm_output_text.strip()
            if stripped_output.startswith("{") and stripped_output.endswith("}"):
                data = json.loads(stripped_output)
                if "triples" in data and isinstance(
                    data["triples"], list
                ):  # Check again for structure
                    for triple_item in data["triples"]:
                        if (
                            isinstance(triple_item, dict)
                            and "source" in triple_item
                            and "target" in triple_item
                            and "relation" in triple_item
                        ):
                            triples.append(
                                {
                                    "source": str(triple_item["source"]),
                                    "target": str(triple_item["target"]),
                                    "relation": str(triple_item["relation"]),
                                }
                            )
                    logger.info(
                        f"Successfully parsed {len(triples)} triples from full text JSON."
                    )
                    return triples

            logger.warning(
                "Could not find or parse a valid JSON structure for triples in LLM output."
            )
            logger.debug(
                f"LLM output that failed flexible parsing: {llm_output_text[:500]}..."
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError while parsing triples from text: {e}")
            logger.debug(
                f"LLM Raw Output (JSONDecodeError): {llm_output_text[:500]}..."
            )
        except Exception as e:
            logger.error(f"Unexpected error while parsing triples: {e}", exc_info=True)
        return triples

    async def chunk_text(self, state: GraphState) -> Dict[str, Any]:
        attachments = state.get("attachments", [])
        attachment_names = [att.get("filename", "Unknown") for att in attachments]
        logger.info(
            f"--- Node: Chunking Text (Attachments: {', '.join(attachment_names)}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            text = state["original_text"]
            if not text or not text.strip():
                return {
                    "error_message": "Input text is empty.",
                    "text_chunks": [],
                    "embedded_chunks": [],  # Ensure this is initialized
                }
            chunks = await asyncio.to_thread(self.text_splitter.split_text, text)
            logger.info(
                f"Text chunked into {len(chunks)} parts from {len(attachments)} attachment(s)."
            )
            return {
                "text_chunks": chunks,
                "error_message": None,
                "embedded_chunks": state.get("embedded_chunks", []),
            }  # Preserve existing if any
        except Exception as e:
            logger.error(f"Error in chunk_text: {e}", exc_info=True)
            return {
                "error_message": str(e),
                "text_chunks": [],
                "embedded_chunks": state.get("embedded_chunks", []),
            }

    async def embed_text_chunks(self, state: GraphState) -> Dict[str, Any]:
        attachments = state.get("attachments", [])
        attachment_names = [att.get("filename", "Unknown") for att in attachments]
        logger.info(
            f"--- Node: Embedding Text Chunks (Attachments: {', '.join(attachment_names)}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            text_chunks = state.get("text_chunks")
            if not text_chunks:
                logger.info("No text chunks to embed.")
                return {
                    "embedded_chunks": []
                }  # Return empty list, don't overwrite other state

            embeddings_list = await asyncio.to_thread(
                self.embedding_model_lc.embed_documents, text_chunks
            )

            # Determine source file for each chunk by analyzing the text content
            embedded_chunks_data: List[EmbeddedChunk] = []
            for i, chunk_text in enumerate(text_chunks):
                # Try to determine which attachment this chunk came from
                source_filename = None
                source_s3_path = None

                # Look for document separator patterns in the chunk
                for attachment in attachments:
                    filename = attachment.get("filename", "")
                    if f"--- Document: {filename} ---" in chunk_text:
                        source_filename = filename
                        source_s3_path = attachment.get("s3_path")
                        break

                # If we can't determine from separator, try to match against original text segments
                if not source_filename and attachments:
                    # For chunks that don't contain separators, try to match against attachment texts
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
                        source_filename = best_match.get("filename")
                        source_s3_path = best_match.get("s3_path")

                embedded_chunks_data.append(
                    EmbeddedChunk(
                        text=chunk_text,
                        embedding=embeddings_list[i],
                        source_filename=source_filename,
                        source_s3_path=source_s3_path,
                    )
                )

            logger.info(
                f"Successfully embedded {len(embedded_chunks_data)} text chunks from {len(attachments)} attachment(s)."
            )
            return {"embedded_chunks": embedded_chunks_data}
        except Exception as e:
            logger.error(f"Error in embed_text_chunks: {e}", exc_info=True)
            return {
                "error_message": f"Failed to embed chunks: {str(e)}",  # Add to error message
                "embedded_chunks": [],  # Return empty on error
            }

    async def extract_main_concept_map(
        self, state: GraphState
    ) -> Dict[str, Any]:  # RENAMED & MODIFIED
        attachments = state.get("attachments", [])
        attachment_names = [att.get("filename", "Unknown") for att in attachments]
        logger.info(
            f"--- Node: Extracting Main Concept Map (Attachments: {', '.join(attachment_names)}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            full_text = state["original_text"]
            if not full_text or not full_text.strip():
                return {
                    "raw_triples": [],
                    "error_message": "Original text is empty for main concept map extraction.",
                }

            # Adjust prompt for high-level mind map of main ideas from multiple documents
            document_context = ""
            if len(attachments) > 1:
                document_context = f"\n\nNote: This analysis combines content from {len(attachments)} documents: {', '.join(attachment_names)}. Focus on finding connections and relationships between concepts across all documents."
            elif len(attachments) == 1:
                document_context = f"\n\nNote: This analysis is based on the document: {attachment_names[0]}."

            prompt = f"""Please analyze the following document(s) and generate a high-level mind map that captures the main conceptual ideas and their relationships.

MIND MAP GUIDELINES:
1. Focus on CONCEPTUAL NODES - abstract ideas, theories, principles, main topics, key themes
2. AVOID: References, citations, page numbers, author names, specific examples, minor details
3. Extract 5-15 core concepts that represent the essence of the content
4. Create meaningful relationships between concepts using clear relational terms
5. Think like creating a mind map - start with central themes and branch out to related concepts

GOOD NODES: "Machine Learning", "Neural Networks", "Data Processing", "Algorithm Optimization"
BAD NODES: "Figure 1.2", "Smith et al. 2020", "Table 3", "Example A", "Reference [1]"

GOOD RELATIONS: "implements", "is part of", "leads to", "requires", "influences", "contains", "depends on"
BAD RELATIONS: "mentioned in", "cited by", "shown in", "referenced as"

Create a mind map structure that helps users understand the core conceptual framework of the content.{document_context}

Document Text:
---
{full_text}
---

Return ONLY a valid JSON object in this exact format:
{{"triples": [{{"source": "Core Concept A", "target": "Related Concept B", "relation": "meaningful relationship"}}]}}

If the document lacks sufficient conceptual content for a mind map, return:
{{"triples": []}}

Focus on capturing the conceptual landscape, not the documentary structure.
"""
            all_triples: List[Dict[str, str]] = []
            try:
                if self.use_structured_output and self.structured_llm:
                    try:
                        logger.debug(
                            "Attempting main map extraction with structured output LLM."
                        )
                        response: ExtractedTriplesLLM = (
                            await self.structured_llm.ainvoke(prompt)
                        )
                        if response.triples:
                            for triple_obj in response.triples:
                                all_triples.append(triple_obj.dict())
                            logger.info(
                                f"Extracted {len(response.triples)} main map triples (structured)."
                            )
                        else:
                            logger.info(
                                "No main map triples extracted by structured LLM."
                            )
                    except Exception as struct_e:
                        logger.warning(
                            f"Main map structured output failed: {struct_e}, trying fallback LLM call..."
                        )
                        llm_response_content = (await self.llm.ainvoke(prompt)).content
                        parsed_triples = self._parse_triples_from_text(
                            llm_response_content
                        )
                        all_triples.extend(parsed_triples)
                        logger.info(
                            f"Extracted {len(parsed_triples)} main map triples (fallback parsing)."
                        )
                else:
                    logger.debug(
                        "Attempting main map extraction with regular LLM call and manual parsing."
                    )
                    llm_response_content = (await self.llm.ainvoke(prompt)).content
                    parsed_triples = self._parse_triples_from_text(llm_response_content)
                    all_triples.extend(parsed_triples)
                    logger.info(
                        f"Extracted {len(parsed_triples)} main map triples (manual parsing)."
                    )

            except Exception as e:
                logger.error(
                    f"Error processing full text with LLM for main map: {e}",
                    exc_info=True,
                )
                # Keep existing error message if one was already set, otherwise set new one
                return {
                    "raw_triples": [],
                    "error_message": state.get("error_message")
                    or f"LLM processing error for main map: {str(e)}",
                }

            # Filter triples to keep only conceptual nodes suitable for mind mapping
            conceptual_triples = self._filter_conceptual_triples(all_triples)

            logger.info(
                f"Extracted {len(all_triples)} raw triples, {len(conceptual_triples)} conceptual triples suitable for mind mapping"
            )
            logger.info(f"DEBUG: All raw triples = {all_triples}")
            logger.info(f"DEBUG: Filtered conceptual triples = {conceptual_triples}")

            return {
                "raw_triples": conceptual_triples,
                "error_message": state.get("error_message"),
            }  # Preserve prior errors
        except Exception as e:
            logger.error(
                f"Overall error in extract_main_concept_map node: {e}", exc_info=True
            )
            return {
                "error_message": str(e),
                "raw_triples": [],
            }  # Set error, clear triples

    async def _get_node_embeddings_for_similarity(
        self, node_labels: List[str]
    ) -> np.ndarray:
        return await asyncio.to_thread(
            self.similarity_embedding_model.encode, node_labels, convert_to_tensor=False
        )

    async def process_graph_data(self, state: GraphState) -> Dict[str, Any]:
        # This node remains largely the same, processing the `raw_triples`
        # which are now from the main concept map extraction.
        attachments = state.get("attachments", [])
        attachment_names = [att.get("filename", "Unknown") for att in attachments]
        logger.info(
            f"--- Node: Processing Graph Data for Main Map (Attachments: {', '.join(attachment_names)}, User: {state.get('user_id', 'N/A')}) ---"
        )

        # Ensure it uses normalize_label from app.utils.cmvs_helpers
        try:
            raw_triples = state.get("raw_triples", [])
            if not raw_triples:
                logger.info("No raw triples (from main map) to process.")
                return {
                    "processed_triples": [],
                    "error_message": state.get("error_message"),
                }

            normalized_triples_intermediate = []
            for triple in raw_triples:
                if (
                    not all(k in triple for k in ["source", "target", "relation"])
                    or not triple["source"]
                    or not triple["target"]
                    or not triple["relation"]
                ):
                    logger.warning(f"Skipping malformed triple: {triple}")
                    continue
                normalized_triples_intermediate.append(
                    {
                        "source": normalize_label(str(triple["source"])),
                        "target": normalize_label(str(triple["target"])),
                        "relation": str(triple["relation"]).strip(),
                    }
                )
            if not normalized_triples_intermediate:  # ...
                return {
                    "processed_triples": [],
                    "error_message": "No valid triples after normalization.",
                }

            nodes = set()  # ...
            for triple in normalized_triples_intermediate:
                nodes.add(triple["source"])
                nodes.add(triple["target"])
            unique_node_labels = list(nodes)
            node_map = {label: label for label in unique_node_labels}

            if (
                len(unique_node_labels) > 1
            ):  # Apply similarity-based merging for conceptual nodes
                node_embeddings = await self._get_node_embeddings_for_similarity(
                    unique_node_labels
                )
                cosine_matrix = await asyncio.to_thread(
                    cosine_similarity, node_embeddings
                )

                # Use higher similarity threshold for conceptual nodes to avoid over-merging
                # Conceptual nodes should be more distinct in a mind map
                similarity_threshold = 0.90  # Higher threshold for mind mapping

                logger.info(
                    f"Applying similarity merging with threshold {similarity_threshold} for {len(unique_node_labels)} conceptual nodes"
                )

                for i in range(len(unique_node_labels)):
                    if node_map[unique_node_labels[i]] != unique_node_labels[i]:
                        continue
                    for j in range(i + 1, len(unique_node_labels)):
                        if node_map[unique_node_labels[j]] != unique_node_labels[j]:
                            continue
                        if cosine_matrix[i, j] > similarity_threshold:
                            # For mind mapping, prefer keeping the shorter, more general term
                            label_i = unique_node_labels[i]
                            label_j = unique_node_labels[j]

                            if len(label_i) <= len(label_j):
                                keep_label, merge_label = label_i, label_j
                            else:
                                keep_label, merge_label = label_j, label_i

                            logger.info(
                                f"    Merging conceptual nodes: '{merge_label}' -> '{keep_label}' (similarity: {cosine_matrix[i,j]:.2f})"
                            )
                            node_map[merge_label] = keep_label

            # Apply node mappings and create final triples
            merged_triples_final = []
            for triple in normalized_triples_intermediate:
                source = triple["source"]
                target = triple["target"]

                # Apply node mappings
                while node_map.get(source, source) != source:
                    source = node_map[source]
                while node_map.get(target, target) != target:
                    target = node_map[target]

                # Skip self-loops which don't make sense in mind maps
                if source != target:
                    merged_triples_final.append(
                        {
                            "source": source,
                            "target": target,
                            "relation": triple["relation"],
                        }
                    )

            # Remove duplicate triples and bidirectional duplicates for mind mapping
            # In mind maps, we typically want undirected relationships
            final_triples_set = set()
            final_unique_triples = []

            for triple in merged_triples_final:
                source, target, relation = (
                    triple["source"],
                    triple["target"],
                    triple["relation"],
                )

                # Create a normalized tuple for comparison (alphabetically sorted to handle bidirectionality)
                normalized_tuple = (
                    min(source, target),
                    max(source, target),
                    relation.lower().strip(),
                )

                if normalized_tuple not in final_triples_set:
                    final_unique_triples.append(triple)
                    final_triples_set.add(normalized_tuple)

            logger.info(
                f"Mind map processing: {len(raw_triples)} raw -> {len(normalized_triples_intermediate)} normalized -> {len(final_unique_triples)} final unique conceptual relationships"
            )
            logger.info(f"DEBUG: Final processed triples = {final_unique_triples}")
            return {"processed_triples": final_unique_triples, "error_message": None}

        except Exception as e:
            logger.error(f"Error in process_graph_data: {e}", exc_info=True)
            return {"error_message": str(e), "processed_triples": []}

    async def generate_react_flow(self, state: GraphState) -> Dict[str, Any]:
        attachments = state.get("attachments", [])
        attachment_names = [att.get("filename", "Unknown") for att in attachments]
        logger.info(
            f"--- Node: Generating React Flow Data for Main Map (Attachments: {', '.join(attachment_names)}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            processed_triples = state.get("processed_triples", [])
            logger.info(f"DEBUG: processed_triples = {processed_triples}")
            logger.info(
                f"DEBUG: Number of processed_triples = {len(processed_triples)}"
            )

            if not processed_triples:  # ... (handle no triples) ...
                logger.warning("No processed triples found for React Flow generation")
                react_flow_data = await asyncio.to_thread(generate_react_flow_data, [])
                logger.info(f"DEBUG: Empty react_flow_data = {react_flow_data}")
                return {
                    "react_flow_data": react_flow_data,
                    "error_message": state.get("error_message")
                    or "No processed triples for React Flow.",
                }

            logger.info(
                f"Generating React Flow data from {len(processed_triples)} processed triples"
            )
            react_flow_data = await asyncio.to_thread(
                generate_react_flow_data, processed_triples
            )
            logger.info(f"DEBUG: Generated react_flow_data = {react_flow_data}")
            logger.info(
                f"DEBUG: react_flow_data keys = {react_flow_data.keys() if react_flow_data else 'None'}"
            )
            if react_flow_data and "edges" in react_flow_data:
                logger.info(
                    f"DEBUG: Number of edges generated = {len(react_flow_data['edges'])}"
                )
                logger.info(
                    f"DEBUG: First few edges = {react_flow_data['edges'][:3] if react_flow_data['edges'] else 'No edges'}"
                )

            return {"react_flow_data": react_flow_data, "error_message": None}
        except Exception as e:
            logger.error(f"Error in generate_react_flow: {e}", exc_info=True)
            return {
                "react_flow_data": generate_react_flow_data([]),
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

    def _is_conceptual_node(self, node_text: str) -> bool:
        """
        Determines if a node represents a conceptual idea suitable for mind mapping.
        Filters out references, citations, examples, and non-conceptual content.
        """
        if not node_text or not node_text.strip():
            return False

        node_text = node_text.strip().lower()

        # Filter out common non-conceptual patterns
        non_conceptual_patterns = [
            r"^figure\s+\d+",  # Figure 1, Figure 2.1, etc.
            r"^table\s+\d+",  # Table 1, Table 2.1, etc.
            r"^section\s+\d+",  # Section 1, Section 2.1, etc.
            r"^chapter\s+\d+",  # Chapter 1, Chapter 2, etc.
            r"^page\s+\d+",  # Page 1, Page 123, etc.
            r"^reference\s*\[?\d+\]?",  # Reference 1, Reference [1], etc.
            r"^\[?\d+\]?$",  # [1], 2, [123], etc.
            r"^example\s*\d*$",  # Example, Example 1, etc.
            r"^appendix\s+[a-z]?",  # Appendix, Appendix A, etc.
            r"et\s+al\.?$",  # Smith et al., Jones et al
            r"^\d{4}$",  # Years like 2023, 2024
            r"^vol\.?\s*\d+",  # Vol. 1, Volume 2, etc.
            r"^pp?\.?\s*\d+",  # p. 123, pp. 45-67, etc.
            r"^isbn",  # ISBN numbers
            r"^doi:",  # DOI references
            r"http[s]?://",  # URLs
            r"^www\.",  # Web addresses
        ]

        # Check against patterns
        for pattern in non_conceptual_patterns:
            if re.search(pattern, node_text):
                return False

        # Filter out very short non-descriptive words
        if len(node_text) < 3:
            return False

        # Filter out common non-conceptual words
        non_conceptual_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "here",
            "there",
            "where",
            "when",
            "why",
            "how",
            "what",
            "which",
            "who",
            "above",
            "below",
            "before",
            "after",
            "during",
            "through",
            "between",
            "among",
            "within",
            "without",
            "across",
            "around",
            "toward",
            "towards",
            "under",
            "over",
            "above",
            "below",
            "beside",
            "near",
            "far",
            "close",
            "same",
            "different",
            "similar",
            "unlike",
            "like",
            "such",
            "also",
            "too",
            "very",
            "much",
            "many",
            "most",
            "more",
            "less",
            "few",
            "little",
            "some",
            "any",
            "all",
            "each",
            "every",
            "both",
            "either",
            "neither",
            "first",
            "second",
            "third",
            "last",
            "next",
            "previous",
            "other",
            "another",
        }

        if node_text in non_conceptual_words:
            return False

        # Must contain at least one alphabetic character
        if not re.search(r"[a-zA-Z]", node_text):
            return False

        # Prefer longer, more descriptive terms for concepts
        # But allow some shorter conceptual terms
        meaningful_short_terms = {
            "ai",
            "ml",
            "api",
            "cpu",
            "gpu",
            "ram",
            "sql",
            "xml",
            "json",
            "html",
            "css",
            "php",
            "ios",
            "ui",
            "ux",
            "seo",
            "crm",
            "erp",
            "roi",
            "kpi",
            "sdg",
            "gdp",
            "nasa",
            "who",
            "faq",
            "ceo",
            "cto",
            "hr",
            "it",
            "pr",
        }

        if len(node_text) < 4 and node_text not in meaningful_short_terms:
            return False

        return True

    def _filter_conceptual_triples(
        self, triples: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Filters triples to keep only those with conceptual nodes suitable for mind mapping.
        """
        conceptual_triples = []

        for triple in triples:
            source = triple.get("source", "").strip()
            target = triple.get("target", "").strip()
            relation = triple.get("relation", "").strip()

            # Both source and target must be conceptual
            if (
                self._is_conceptual_node(source)
                and self._is_conceptual_node(target)
                and source.lower() != target.lower()  # Avoid self-loops
                and relation  # Must have a relation
            ):
                conceptual_triples.append(triple)
            else:
                logger.debug(
                    f"Filtered out non-conceptual triple: {source} -> {target}"
                )

        return conceptual_triples
