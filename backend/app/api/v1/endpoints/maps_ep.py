from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Depends,
    Query,
)
from typing import List, Optional
import uuid

from app.core.config import logger
from app.models.user_models import UserModelInDB
from app.models.cmvs_models import (
    NodeDetailResponse,
    AttachmentInfo,
    MindMapResponse,
)
from app.api.v1.deps import get_current_active_user
from app.services.pdf_service import extract_text_from_pdf_bytes
from app.services.s3_service import S3Service
from app.services.cmvs_service import (
    get_node_details_with_rag,
    generate_hierarchical_mindmap,
)
from app.db.mongodb_utils import get_db
from app.core.config import settings
from bson import ObjectId
from pymongo.errors import PyMongoError


router = APIRouter()
s3_service_instance = S3Service()  # Instantiate S3 service


@router.get("/history/", tags=["Maps"])
async def get_map_history_endpoint(
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Retrieves the user's mind map history.
    """
    try:
        db = get_db()
        cm_collection = db[settings.MONGODB_CMVS_COLLECTION]

        # Find all mind maps for the current user
        maps_cursor = cm_collection.find(
            {"user_id": current_user.id},
            {
                "_id": 1,
                "title": 1,
                "original_filename": 1,
                "created_at": 1,
            },
        ).sort(
            "created_at", -1
        )  # Most recent first

        history = []
        for map_doc in maps_cursor:
            history.append(
                {
                    "map_id": str(map_doc["_id"]),
                    "title": map_doc.get("title", "Unknown"),
                    "original_filename": map_doc.get("original_filename", "Unknown"),
                    "created_at": (
                        map_doc.get("created_at").isoformat()
                        if map_doc.get("created_at")
                        else None
                    ),
                }
            )

        logger.info(f"Retrieved {len(history)} maps for user {current_user.email}")
        return {"history": history}

    except PyMongoError as e:
        logger.error(
            f"Database error retrieving map history for user {current_user.email}: {e}"
        )
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error retrieving map history for user {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{map_id}", tags=["Maps"])
async def get_mind_map_endpoint(
    map_id: str,
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Retrieves a specific mind map by ID.
    """
    try:
        # Validate map_id is a valid ObjectId
        if not ObjectId.is_valid(map_id):
            raise HTTPException(status_code=400, detail="Invalid map ID format")

        db = get_db()
        cm_collection = db[settings.MONGODB_CMVS_COLLECTION]

        # Find the mind map document
        map_doc = cm_collection.find_one(
            {
                "_id": ObjectId(map_id),
                "user_id": current_user.id,  # Ensure user can only access their own maps
            }
        )

        if not map_doc:
            raise HTTPException(status_code=404, detail="Mind map not found")

        # Get the hierarchical data
        hierarchical_data = map_doc.get("hierarchical_data")

        if not hierarchical_data:
            logger.warning(f"Map {map_id} exists but has no hierarchical_data")
            raise HTTPException(status_code=404, detail="Mind map data not found")

        response = {
            "mongodb_doc_id": str(map_doc["_id"]),
            "title": map_doc.get("title", "Unknown"),
            "hierarchical_data": hierarchical_data,
            "original_filename": map_doc.get("original_filename"),
        }

        logger.info(f"Retrieved mind map {map_id} for user {current_user.email}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except PyMongoError as e:
        logger.error(
            f"Database error retrieving map {map_id} for user {current_user.email}: {e}"
        )
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(
            f"Error retrieving map {map_id} for user {current_user.email}: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate-mindmap/", response_model=MindMapResponse, tags=["Mind Maps"])
async def generate_mindmap_endpoint(
    file: UploadFile = File(
        ..., description="PDF file to process into a hierarchical mind map."
    ),
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Generate hierarchical mind map from a single PDF document.

    This endpoint implements the new two-stage processing:
    1. Page-by-page analysis using PageProcessorAgent
    2. Master synthesis using MasterSynthesizerAgent
    3. Returns hierarchical JSON structure compatible with reaflow
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    logger.info(
        f"User '{current_user.email}' initiated hierarchical mind map generation for file: {file.filename}"
    )

    s3_file_path: Optional[str] = None

    try:
        # Read file content
        file_content = await file.read()

        # Extract text from PDF
        extracted_text = await extract_text_from_pdf_bytes(file_content)
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise HTTPException(
                status_code=422,
                detail="Could not extract sufficient text from PDF. The file might be image-based or corrupted.",
            )

        # Upload file to S3
        if s3_service_instance.is_configured():
            s3_object_name = (
                f"user_{current_user.id}/uploads/{uuid.uuid4()}-{file.filename}"
            )
            s3_file_path = await s3_service_instance.upload_pdf_bytes_async(
                file_bytes=file_content, object_name=s3_object_name
            )
            logger.info(f"File uploaded to S3: {s3_file_path}")

        # Generate hierarchical mind map
        mindmap_response = await generate_hierarchical_mindmap(
            filename=file.filename,
            extracted_text=extracted_text,
            s3_path=s3_file_path,
            user_id=current_user.id,
        )

        if mindmap_response.status == "error":
            logger.error(
                f"Mind map generation failed: {mindmap_response.error_message}"
            )
            raise HTTPException(status_code=500, detail=mindmap_response.error_message)

        logger.info(
            f"Successfully generated hierarchical mind map for file: {file.filename}"
        )
        return mindmap_response

    except HTTPException:
        # Clean up S3 file if upload succeeded but processing failed
        if s3_file_path:
            try:
                await s3_service_instance.delete_file_async(s3_file_path)
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to cleanup S3 file {s3_file_path}: {cleanup_error}"
                )
        raise
    except Exception as e:
        # Clean up S3 file if upload succeeded but processing failed
        if s3_file_path:
            try:
                await s3_service_instance.delete_file_async(s3_file_path)
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to cleanup S3 file {s3_file_path}: {cleanup_error}"
                )

        logger.error(
            f"Unhandled error in hierarchical mind map generation: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error occurred.")


@router.get("/details/", response_model=NodeDetailResponse, tags=["Maps"])
async def get_node_details_rag_endpoint(
    map_id: str = Query(..., description="The ID of the main mind map document."),
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
    if not map_id or not node_query:
        raise HTTPException(
            status_code=400, detail="map_id and node_query are required."
        )

    response = await get_node_details_with_rag(
        concept_map_id=map_id,
        node_query=node_query,
        user_id=current_user.id,
        top_k_retriever=top_k,
    )

    return response


@router.get("/ask/", response_model=NodeDetailResponse, tags=["Maps"])
async def ask_question_about_node_endpoint(
    concept_map_id: str = Query(
        ..., description="The ID of the main mind map document providing context."
    ),
    question: str = Query(
        ..., description="The specific question the user wants to ask."
    ),
    context_node_label: Optional[str] = Query(
        None,
        description="(Optional) The label of the node or concept this question is primarily about, to help focus the search.",
    ),
    top_k: Optional[int] = Query(
        3, description="Number of source chunks to retrieve for context.", ge=1, le=5
    ),
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Answers a specific question related to a concept/node within a given mind map,
    using a RAG pipeline with potential fallback to web search and source citation.
    """
    if not concept_map_id or not question:
        raise HTTPException(
            status_code=400, detail="concept_map_id and question are required."
        )

    # Construct an effective query for the RAG pipeline.
    # If context_node_label is provided, prepend it to the question for better focus.
    effective_query = question
    if context_node_label:
        effective_query = (
            f"Regarding the concept or topic of '{context_node_label}': {question}"
        )

    logger.info(
        f"User '{current_user.email}' asking about map '{concept_map_id}': '{effective_query}'"
    )

    try:
        # Call the existing RAG service function
        response = await get_node_details_with_rag(
            concept_map_id=concept_map_id,
            node_query=effective_query,
            user_id=current_user.id,
            top_k_retriever=top_k,
        )

        if not response:
            logger.error(f"No response from RAG service for query: {effective_query}")
            raise HTTPException(
                status_code=500, detail="Failed to process the question."
            )

        return response

    except Exception as e:
        logger.error(
            f"API Error in ask_question_about_node_endpoint for query '{effective_query}', map '{concept_map_id}': {e}",
            exc_info=True,
        )
        # Return a NodeDetailResponse compliant error structure
        return NodeDetailResponse(
            query=effective_query,
            answer=f"An internal server error occurred while processing your question: {str(e)}",
            cited_sources=[],
            message="Failed to get an answer due to a server error.",
        )
