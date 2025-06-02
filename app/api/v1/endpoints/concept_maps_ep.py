from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Depends,
    BackgroundTasks,
    Query,
)
from typing import List, Optional
import uuid

from app.core.config import settings, logger
from app.models.user_models import UserModelInDB
from app.models.cmvs_models import (
    CMVSResponse,
    MultipleCMVSResponse,
    NodeDetailResponse,
)
from app.api.v1.deps import get_current_active_user
from app.services.pdf_service import extract_text_from_pdf_bytes
from app.services.s3_service import S3Service
from app.services.cmvs_service import get_rag_details_for_node, run_cmvs_pipeline
from app.langgraph_pipeline.state import GraphState


router = APIRouter()
s3_service_instance = S3Service()  # Instantiate S3 service


@router.post("/secure-generate/", response_model=MultipleCMVSResponse)
async def generate_concept_map_secure_endpoint(
    files: List[UploadFile] = File(
        ..., description="One or more PDF files to process."
    ),
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    results = []
    logger.info(
        f"User '{current_user.email}' (ID: {current_user.id}) initiated CMVS generation for {len(files)} file(s)."
    )

    for uploaded_file in files:
        s3_file_path: Optional[str] = None
        filename = (
            uploaded_file.filename
            if uploaded_file.filename
            else f"unknown_file_{uuid.uuid4()}.pdf"
        )

        if uploaded_file.content_type != "application/pdf":
            results.append(
                CMVSResponse(
                    filename=filename,
                    status="error",
                    error_message="Invalid file type. Only PDF.",
                )
            )
            logger.warning(
                f"Invalid file type '{uploaded_file.content_type}' for file '{filename}' by user '{current_user.email}'."
            )
            continue

        try:
            logger.info(f"Processing file: {filename} for user: {current_user.email}")
            pdf_bytes = await uploaded_file.read()

            # S3 Upload Step
            if s3_service_instance.is_configured():
                s3_object_name = (
                    f"user_{current_user.id}/uploads/{uuid.uuid4()}-{filename}"
                )
                s3_file_path = await s3_service_instance.upload_pdf_bytes_async(
                    file_bytes=pdf_bytes, object_name=s3_object_name
                )
                if not s3_file_path:
                    logger.warning(
                        f"S3 upload failed for {filename}, but continuing concept map generation."
                    )
            else:
                logger.info(
                    "S3 client not configured or bucket not set. Skipping S3 upload."
                )

            # Text Extraction
            extracted_text = await extract_text_from_pdf_bytes(
                pdf_bytes
            )  # Using the service
            if not extracted_text.strip():
                logger.warning(
                    f"No text extracted from PDF '{filename}' for user '{current_user.email}'."
                )
                results.append(
                    CMVSResponse(
                        filename=filename,
                        status="error",
                        s3_path=s3_file_path,
                        error_message="No text extracted from PDF.",
                    )
                )
                continue

            # LangGraph Pipeline Invocation via CMVS Service
            initial_state = GraphState(
                original_text=extracted_text,
                text_chunks=[],
                embedded_chunks=[],
                raw_triples=[],
                processed_triples=[],
                mermaid_code="",
                mongodb_doc_id=None,
                mongodb_chunk_ids=[],
                error_message=None,
                current_filename=filename,
                s3_path=s3_file_path,
                user_id=current_user.id,  # Pass authenticated user's MongoDB ID
            )

            final_graph_state_dict = await run_cmvs_pipeline(initial_state)

            if final_graph_state_dict.get("error_message"):
                logger.error(
                    f"Pipeline error for '{filename}', user '{current_user.email}': {final_graph_state_dict['error_message']}"
                )
                results.append(
                    CMVSResponse(
                        filename=filename,
                        status="error",
                        s3_path=s3_file_path,
                        error_message=final_graph_state_dict["error_message"],
                    )
                )
            else:
                logger.info(
                    f"Successfully processed '{filename}' for user '{current_user.email}'."
                )
                results.append(
                    CMVSResponse(
                        filename=filename,
                        status="success",
                        s3_path=s3_file_path,
                        mermaid_code=final_graph_state_dict.get("mermaid_code"),
                        processed_triples=final_graph_state_dict.get(
                            "processed_triples"
                        ),
                        mongodb_doc_id=final_graph_state_dict.get("mongodb_doc_id"),
                        mongodb_chunk_ids=final_graph_state_dict.get(
                            "mongodb_chunk_ids"
                        ),
                    )
                )
        except HTTPException as http_exc:
            logger.error(
                f"HTTPException during processing for '{filename}', user '{current_user.email}': {http_exc.detail}",
                exc_info=True,
            )
            results.append(
                CMVSResponse(
                    filename=filename, status="error", error_message=http_exc.detail
                )
            )
        except Exception as e:
            logger.error(
                f"Unhandled error processing file '{filename}' for user '{current_user.email}': {e}",
                exc_info=True,
            )
            results.append(
                CMVSResponse(
                    filename=filename,
                    status="error",
                    error_message=f"Unexpected server error: {str(e)}",
                )
            )
        finally:
            if (
                uploaded_file
                and hasattr(uploaded_file, "file")
                and uploaded_file.file
                and not uploaded_file.file.closed
            ):
                await uploaded_file.close()

    return MultipleCMVSResponse(results=results)


@router.get(
    "/node-details-rag/", response_model=NodeDetailResponse, tags=["Concept Maps"]
)  # New path or updated old one
async def get_node_details_rag_endpoint(  # Renamed endpoint function for clarity
    concept_map_id: str = Query(
        ..., description="The ID of the main concept map document."
    ),
    node_query: str = Query(
        ..., description="The label/text of the tapped node (your question)."
    ),
    top_k: Optional[int] = Query(
        3, description="Number of source chunks to retrieve for context.", ge=1, le=5
    ),
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Retrieves a generated answer and source chunks for a given node query
    using RAG with MongoDB Atlas Vector Search.
    """
    if not concept_map_id or not node_query:
        raise HTTPException(
            status_code=400, detail="concept_map_id and node_query are required."
        )

    try:
        # Call the new RAG service function
        response = await get_rag_details_for_node(
            concept_map_id=concept_map_id,
            node_query=node_query,  # This is the "question"
            user_id=current_user.id,
            top_k_retriever=top_k,
        )

        if not response or (
            not response.answer and not response.source_chunks
        ):  # Check if response is minimal
            # If the service returned a response with an error message in 'answer', it will be passed through.
            # This specific check is more for if the service function itself returned None or an empty valid response.
            return NodeDetailResponse(
                query=node_query,
                answer="Could not retrieve or generate information for this node.",
                source_chunks=[],
                message="No details found or an error occurred during processing.",
            )

        return response  # The service function now returns the full NodeDetailResponse

    except Exception as e:  # Catch any unexpected errors from the service call itself
        logger.error(
            f"API Error in get_node_details_rag_endpoint for query '{node_query}', map '{concept_map_id}': {e}",
            exc_info=True,
        )
        # Return a NodeDetailResponse compliant error structure
        return NodeDetailResponse(
            query=node_query,
            answer=f"An internal server error occurred: {str(e)}",
            source_chunks=[],
            message="Failed to fetch node details due to a server error.",
        )
