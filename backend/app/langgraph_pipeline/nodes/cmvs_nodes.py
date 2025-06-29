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

            prompt = f"""Please analyze the following document(s) and generate a high-level concept map that outlines the main ideas, core arguments, and overall structure.
Focus on creating a 'mind map' style overview, not a detailed, granular breakdown of every piece of information.
Extract between 5 to 15 key concepts and their primary relationships to represent the essence of the content.
Avoid including minor details, specific examples from the text, or overly granular sub-points in THIS main map.
The goal is a concise overview that a user can explore, with details to be fetched later.{document_context}

Document Text:
---
{full_text}
---

Return ONLY a valid JSON object in this exact format:
{{"triples": [{{"source": "Main Idea A", "target": "Main Idea B", "relation": "is related to/explains/is part of"}}]}}

If the document is too short or abstract to extract such a map, return:
{{"triples": []}}

Ensure each triple has 'source', 'target', and 'relation' fields populated with meaningful, concise text.
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

            logger.info(
                f"Total raw triples extracted for main concept map: {len(all_triples)}"
            )
            return {
                "raw_triples": all_triples,
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

            if len(unique_node_labels) > 1:  # ... (cosine similarity merging logic) ...
                node_embeddings = await self._get_node_embeddings_for_similarity(
                    unique_node_labels
                )
                cosine_matrix = await asyncio.to_thread(
                    cosine_similarity, node_embeddings
                )
                # ... (loop and merge) ...
                similarity_threshold = 0.85
                for i in range(len(unique_node_labels)):
                    if node_map[unique_node_labels[i]] != unique_node_labels[i]:
                        continue
                    for j in range(i + 1, len(unique_node_labels)):
                        if node_map[unique_node_labels[j]] != unique_node_labels[j]:
                            continue
                        if cosine_matrix[i, j] > similarity_threshold:
                            logger.info(
                                f"    Merging '{unique_node_labels[j]}' into '{unique_node_labels[i]}' (similarity: {cosine_matrix[i,j]:.2f})"
                            )
                            node_map[unique_node_labels[j]] = unique_node_labels[i]

            merged_triples_final = []
            for triple in normalized_triples_intermediate:
                source = triple["source"]
                target = triple["target"]
                while node_map.get(source, source) != source:
                    source = node_map[source]
                while node_map.get(target, target) != target:
                    target = node_map[target]
                merged_triples_final.append(
                    {"source": source, "target": target, "relation": triple["relation"]}
                )

            final_triples_set = set()
            final_unique_triples = []
            for triple in merged_triples_final:
                triple_tuple = tuple(sorted(triple.items()))
                if triple_tuple not in final_triples_set:
                    final_unique_triples.append(triple)
                    final_triples_set.add(triple_tuple)

            logger.info(
                f"Main map post-processing resulted in {len(final_unique_triples)} unique triples."
            )
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
            if not processed_triples:  # ... (handle no triples) ...
                react_flow_data = await asyncio.to_thread(generate_react_flow_data, [])
                return {
                    "react_flow_data": react_flow_data,
                    "error_message": state.get("error_message")
                    or "No processed triples for React Flow.",
                }
            react_flow_data = await asyncio.to_thread(
                generate_react_flow_data, processed_triples
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
