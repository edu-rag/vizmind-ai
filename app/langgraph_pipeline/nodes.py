import asyncio
import numpy as np
import json
import re
from typing import List, Dict, Any, Optional

# Langchain & supporting libs
from langchain_groq import ChatGroq
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer  # For direct use in similarity
from sklearn.metrics.pairwise import cosine_similarity

# App specific imports
from app.core.config import settings, logger
from app.langgraph_pipeline.state import GraphState, EmbeddedChunk
from app.models.cmvs_models import (
    ConceptTripleLLM,
    ExtractedTriplesLLM,
)  # LLM specific models
from app.db.mongodb_utils import get_db  # To get collections within the node
from app.utils.cmvs_helpers import (
    normalize_label,
    generate_mermaid_graph_syntax,
)  # Utility functions

import datetime  # For pymongo utcnow
from pymongo import ReturnDocument  # For MongoDB operations

# Ensure this is the correct way to handle pymongo utcnow based on your version
# This is a placeholder for how you might handle it if direct attribute access fails.
# It's better if pymongo itself provides this.
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
            temperature=0,
            groq_api_key=groq_api_key,
            model_name=settings.LLM_MODEL_NAME_GROQ,
        )
        # Try to use structured output, but have fallback ready
        try:
            self.structured_llm = self.llm.with_structured_output(ExtractedTriplesLLM)
            self.use_structured_output = True
            logger.info("Using structured output for triple extraction.")
        except Exception as e:
            logger.warning(f"Structured output not available, using fallback: {e}")
            self.structured_llm = None
            self.use_structured_output = False

        self.embedding_model_lc = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            # model_kwargs={'device': 'cpu'} # Optional: if CUDA issues
        )
        self.text_splitter = SemanticChunker(
            self.embedding_model_lc, breakpoint_threshold_type="percentile"
        )
        # For cosine similarity between node labels specifically
        self.similarity_embedding_model = SentenceTransformer(embedding_model_name)
        logger.info("CMVSNodes initialized.")

    def _parse_triples_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Parse triples from LLM text response when structured output fails.
        Looks for JSON patterns in the text.
        """
        triples = []
        try:
            # Try to find JSON in the text
            # Look for patterns like {"triples": [...]}
            json_match = re.search(
                r'\{[^{}]*"triples"[^{}]*\[[^\]]*\][^{}]*\}', text, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
                if "triples" in parsed_data and isinstance(
                    parsed_data["triples"], list
                ):
                    for triple in parsed_data["triples"]:
                        if (
                            isinstance(triple, dict)
                            and "source" in triple
                            and "target" in triple
                            and "relation" in triple
                        ):
                            triples.append(
                                {
                                    "source": str(triple["source"]),
                                    "target": str(triple["target"]),
                                    "relation": str(triple["relation"]),
                                }
                            )
            else:
                # Try to parse the entire text as JSON
                parsed_data = json.loads(text.strip())
                if "triples" in parsed_data:
                    for triple in parsed_data["triples"]:
                        if (
                            isinstance(triple, dict)
                            and "source" in triple
                            and "target" in triple
                            and "relation" in triple
                        ):
                            triples.append(
                                {
                                    "source": str(triple["source"]),
                                    "target": str(triple["target"]),
                                    "relation": str(triple["relation"]),
                                }
                            )
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to parse triples from text: {e}")
            logger.debug(f"Text that failed to parse: {text[:500]}...")

        return triples

    async def chunk_text(self, state: GraphState) -> Dict[str, Any]:
        # ... (Logic from previous full script, adapted with logger and correct state fields) ...
        logger.info(
            f"--- Node: Chunking Text (File: {state.get('current_filename', 'N/A')}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            text = state["original_text"]
            if not text or not text.strip():
                return {
                    "error_message": "Input text is empty.",
                    "text_chunks": [],
                    "embedded_chunks": [],
                }
            # SemanticChunker can be blocking; run in thread for async safety
            chunks = await asyncio.to_thread(self.text_splitter.split_text, text)
            logger.info(f"Text chunked into {len(chunks)} parts.")
            return {"text_chunks": chunks, "error_message": None, "embedded_chunks": []}
        except Exception as e:
            logger.error(f"Error in chunk_text: {e}", exc_info=True)
            return {"error_message": str(e), "text_chunks": [], "embedded_chunks": []}

    async def embed_text_chunks(self, state: GraphState) -> Dict[str, Any]:
        # ... (Logic from previous full script, adapted with logger) ...
        logger.info(
            f"--- Node: Embedding Text Chunks (File: {state.get('current_filename', 'N/A')}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            text_chunks = state.get("text_chunks")
            if not text_chunks:
                logger.info("No text chunks to embed.")
                return {"embedded_chunks": []}

            # embed_documents can be blocking
            embeddings_list = await asyncio.to_thread(
                self.embedding_model_lc.embed_documents, text_chunks
            )

            embedded_chunks_data: List[EmbeddedChunk] = [
                EmbeddedChunk(text=chunk_text, embedding=embeddings_list[i])
                for i, chunk_text in enumerate(text_chunks)
            ]
            logger.info(
                f"Successfully embedded {len(embedded_chunks_data)} text chunks."
            )
            return {"embedded_chunks": embedded_chunks_data}
        except Exception as e:
            logger.error(f"Error in embed_text_chunks: {e}", exc_info=True)
            return {
                "error_message": f"Failed to embed chunks: {str(e)}",
                "embedded_chunks": [],
            }

    async def extract_triples_from_chunks(self, state: GraphState) -> Dict[str, Any]:
        logger.info(
            f"--- Node: Extracting Triples (File: {state.get('current_filename', 'N/A')}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            chunks = state["text_chunks"]
            if not chunks:
                return {
                    "raw_triples": [],
                    "error_message": "No text chunks for triple extraction.",
                }

            all_triples: List[Dict[str, str]] = []
            for i, chunk_text in enumerate(chunks):
                logger.info(
                    f"  Processing chunk {i+1}/{len(chunks)} for triple extraction..."
                )

                # Create a clear prompt for JSON output
                prompt = f"""Extract key concepts and their relationships from the text below as JSON triples.

Text:
{chunk_text}

Return ONLY a valid JSON object in this exact format:
{{"triples": [{{"source": "concept1", "target": "concept2", "relation": "relationship"}}]}}

If no meaningful relationships are found, return:
{{"triples": []}}

Focus on clear, specific concepts and meaningful relationships. Ensure each triple has all three fields populated."""

                try:
                    if self.use_structured_output and self.structured_llm:
                        # Try structured output first
                        try:
                            response: ExtractedTriplesLLM = (
                                await self.structured_llm.ainvoke(prompt)
                            )
                            if response.triples:
                                for triple_obj in response.triples:
                                    all_triples.append(triple_obj.dict())
                                logger.info(
                                    f"    Extracted {len(response.triples)} triples from this chunk (structured)."
                                )
                            else:
                                logger.info(
                                    "    No triples extracted from this chunk by structured LLM."
                                )
                        except Exception as struct_e:
                            logger.warning(
                                f"    Structured output failed: {struct_e}, trying fallback..."
                            )
                            # Fallback to regular LLM
                            response_text = await self.llm.ainvoke(prompt)
                            parsed_triples = self._parse_triples_from_text(
                                response_text.content
                            )
                            all_triples.extend(parsed_triples)
                            logger.info(
                                f"    Extracted {len(parsed_triples)} triples from this chunk (fallback)."
                            )
                    else:
                        # Use regular LLM with manual parsing
                        response_text = await self.llm.ainvoke(prompt)
                        parsed_triples = self._parse_triples_from_text(
                            response_text.content
                        )
                        all_triples.extend(parsed_triples)
                        logger.info(
                            f"    Extracted {len(parsed_triples)} triples from this chunk (manual parsing)."
                        )

                except Exception as e:
                    logger.warning(
                        f"    Error processing chunk {i+1} with LLM for triple extraction: {e}",
                        exc_info=True,
                    )

            logger.info(f"Total raw triples extracted: {len(all_triples)}")
            return {"raw_triples": all_triples, "error_message": None}
        except Exception as e:
            logger.error(
                f"Error in extract_triples_from_chunks node: {e}", exc_info=True
            )
            return {"error_message": str(e), "raw_triples": []}

    async def _get_node_embeddings_for_similarity(
        self, node_labels: List[str]
    ) -> np.ndarray:
        # This uses the dedicated SentenceTransformer model for node label similarity
        return await asyncio.to_thread(
            self.similarity_embedding_model.encode, node_labels, convert_to_tensor=False
        )

    async def process_graph_data(self, state: GraphState) -> Dict[str, Any]:
        # ... (Logic from previous full script, adapted with logger, normalize_label, and correct state fields) ...
        logger.info(
            f"--- Node: Processing Graph Data (File: {state.get('current_filename', 'N/A')}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            raw_triples = state.get("raw_triples", [])
            if not raw_triples:
                logger.info("No raw triples to process in process_graph_data.")
                return {
                    "processed_triples": [],
                    "error_message": (
                        None
                        if not state.get("error_message")
                        else state.get("error_message")
                    ),
                }

            normalized_triples_intermediate = []
            for triple in raw_triples:
                if (
                    not all(k in triple for k in ["source", "target", "relation"])
                    or not triple["source"]
                    or not triple["target"]
                    or not triple["relation"]
                ):  # Basic validation
                    logger.warning(f"Skipping malformed triple: {triple}")
                    continue
                normalized_triples_intermediate.append(
                    {
                        "source": normalize_label(
                            str(triple["source"])
                        ),  # Ensure string
                        "target": normalize_label(
                            str(triple["target"])
                        ),  # Ensure string
                        "relation": str(triple["relation"]).strip(),  # Ensure string
                    }
                )

            if not normalized_triples_intermediate:
                logger.info("No valid triples after initial normalization.")
                return {
                    "processed_triples": [],
                    "error_message": "No valid triples after initial normalization.",
                }

            nodes = set()
            for triple in normalized_triples_intermediate:
                nodes.add(triple["source"])
                nodes.add(triple["target"])
            unique_node_labels = list(nodes)
            node_map = {label: label for label in unique_node_labels}

            if len(unique_node_labels) > 1:
                logger.info(
                    f"  Attempting to merge {len(unique_node_labels)} unique node labels using semantic similarity..."
                )
                node_embeddings = await self._get_node_embeddings_for_similarity(
                    unique_node_labels
                )
                # cosine_similarity is CPU-bound, run in thread pool
                cosine_matrix = await asyncio.to_thread(
                    cosine_similarity, node_embeddings
                )
                similarity_threshold = 0.85  # Adjust as needed

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
                # Resolve chained mappings
                while node_map.get(source, source) != source:  # Use .get for safety
                    source = node_map[source]
                while node_map.get(target, target) != target:  # Use .get for safety
                    target = node_map[target]
                merged_triples_final.append(
                    {"source": source, "target": target, "relation": triple["relation"]}
                )

            final_triples_set = set()
            final_unique_triples = []
            for triple in merged_triples_final:
                # Create a hashable representation of the triple for set uniqueness
                triple_tuple = tuple(sorted(triple.items()))
                if triple_tuple not in final_triples_set:
                    final_unique_triples.append(triple)
                    final_triples_set.add(triple_tuple)

            logger.info(
                f"  Post-processing resulted in {len(final_unique_triples)} unique triples."
            )
            return {"processed_triples": final_unique_triples, "error_message": None}
        except Exception as e:
            logger.error(f"Error in process_graph_data: {e}", exc_info=True)
            return {"error_message": str(e), "processed_triples": []}

    async def generate_mermaid(self, state: GraphState) -> Dict[str, Any]:
        # ... (Logic from previous full script, adapted with logger and generate_mermaid_graph_syntax util) ...
        logger.info(
            f"--- Node: Generating Mermaid Code (File: {state.get('current_filename', 'N/A')}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            processed_triples = state.get(
                "processed_triples", []
            )  # Default to empty list
            if not processed_triples:
                logger.info(
                    "No processed triples to generate Mermaid from. Returning empty graph syntax."
                )
                # Pass empty list to ensure valid Mermaid for empty graph
                mermaid_code = await asyncio.to_thread(
                    generate_mermaid_graph_syntax, []
                )
                return {
                    "mermaid_code": mermaid_code,
                    "error_message": (
                        "No processed triples for Mermaid."
                        if not state.get("error_message")
                        else state.get("error_message")
                    ),
                }

            mermaid_code = await asyncio.to_thread(
                generate_mermaid_graph_syntax, processed_triples
            )
            logger.info("  Mermaid code generated successfully.")
            return {"mermaid_code": mermaid_code, "error_message": None}
        except Exception as e:
            logger.error(f"Error in generate_mermaid: {e}", exc_info=True)
            return {
                "mermaid_code": generate_mermaid_graph_syntax([]),
                "error_message": str(e),
            }  # Return empty graph on error

    async def store_cmvs_data_in_mongodb(self, state: GraphState) -> Dict[str, Any]:
        # ... (Logic from previous full script, adapted with logger and correct state fields, using get_db from mongodb_utils) ...
        logger.info(
            f"--- Node: Storing CMVS Data in MongoDB (File: {state.get('current_filename', 'N/A')}, User: {state.get('user_id', 'N/A')}) ---"
        )
        try:
            processed_triples = state.get("processed_triples", [])
            user_id = state.get("user_id")
            s3_path = state.get("s3_path")
            mermaid_code = state.get("mermaid_code")
            embedded_chunks = state.get("embedded_chunks", [])
            original_text = state.get(
                "original_text", ""
            )  # Get original_text for snippet

            # Only proceed if there's something to store or if we are expecting to link chunks
            if not processed_triples and not embedded_chunks:
                logger.info(
                    "No processed data (triples or chunks) to store in MongoDB."
                )
                return {
                    "mongodb_doc_id": None,
                    "mongodb_chunk_ids": [],
                    "error_message": (
                        "No processed data to store."
                        if not state.get("error_message")
                        else state.get("error_message")
                    ),
                }

            if not user_id:  # Storing user_id is critical
                logger.error(
                    "User ID not found in state. Cannot store data without user association."
                )
                return {
                    "mongodb_doc_id": None,
                    "mongodb_chunk_ids": [],
                    "error_message": "User ID missing, cannot save to DB.",
                }

            db = get_db()  # Get DB instance from mongodb_utils
            cm_collection = db[settings.MONGODB_CMVS_COLLECTION]
            chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]

            def _db_operations_sync():  # Synchronous function to be run in a thread
                main_doc_id_obj = None  # Store ObjectId directly
                stored_chunk_ids_obj = []

                # 1. Store main CMVS document
                if processed_triples:  # Only store main doc if there are triples
                    main_doc_to_insert = {
                        "user_id": user_id,
                        "original_filename": state.get("current_filename", "N/A"),
                        "s3_path": s3_path,
                        "original_text_snippet": original_text[:500]
                        + ("..." if len(original_text) > 500 else ""),
                        "triples": processed_triples,
                        "mermaid_code": mermaid_code,
                        "created_at": datetime.datetime.now(
                            UTC
                        ),  # Use timezone aware UTC
                    }
                    main_result = cm_collection.insert_one(main_doc_to_insert)
                    main_doc_id_obj = main_result.inserted_id
                    logger.info(
                        f"  Main CMVS data stored in MongoDB with ID: {main_doc_id_obj}"
                    )
                else:
                    logger.info("No processed triples to store for main CMVS document.")

                # 2. Store chunk embeddings
                if embedded_chunks:
                    chunk_docs_to_insert = []
                    for emb_chunk in embedded_chunks:
                        chunk_docs_to_insert.append(
                            {
                                # Link to the main CMVS document ID if it was created
                                "concept_map_id": (
                                    str(main_doc_id_obj) if main_doc_id_obj else None
                                ),
                                "user_id": user_id,
                                "text": emb_chunk["text"],
                                "embedding": emb_chunk["embedding"],
                                "s3_path_source_pdf": s3_path,  # Link to the source PDF on S3
                                "original_filename_source_pdf": state.get(
                                    "current_filename", "N/A"
                                ),
                                "created_at": datetime.datetime.now(UTC),
                            }
                        )

                    if chunk_docs_to_insert:
                        chunk_results = chunks_collection.insert_many(
                            chunk_docs_to_insert
                        )
                        stored_chunk_ids_obj = chunk_results.inserted_ids
                        logger.info(
                            f"  Stored {len(stored_chunk_ids_obj)} chunk embeddings in MongoDB."
                        )
                else:
                    logger.info("No embedded chunks to store.")

                # Convert ObjectIds to strings for the state
                main_doc_id_str = str(main_doc_id_obj) if main_doc_id_obj else None
                stored_chunk_ids_str = [str(id_val) for id_val in stored_chunk_ids_obj]
                return main_doc_id_str, stored_chunk_ids_str

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
