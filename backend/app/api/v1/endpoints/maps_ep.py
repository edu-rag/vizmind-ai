from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Depends,
)
import uuid

from app.core.config import logger, settings
from app.models.user_models import UserModelInDB
from app.models.cmvs_models import (
    MindMapResponse,
)
from app.api.v1.deps import get_current_active_user
from app.services.s3_service import S3Service
from app.services.vizmind_service import VizMindAIService
from app.db.mongodb_utils import get_db
from bson import ObjectId
from pymongo.errors import PyMongoError

router = APIRouter()
s3_service_instance = S3Service()


@router.post(
    "/generate-mindmap", response_model=MindMapResponse, tags=["VizMind AI Mind Maps"]
)
async def generate_mindmap_endpoint(
    file: UploadFile = File(
        ..., description="PDF file to process and create mind map."
    ),
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Generates a hierarchical mind map from a PDF using VizMind AI workflow.

    This endpoint:
    1. Uploads the PDF to S3 (if configured)
    2. Extracts and cleans the content using Docling and LLM
    3. Generates a hierarchical mind map structure
    4. Chunks the content by headings and stores embeddings in MongoDB for RAG
    5. Returns the mind map data as HierarchicalNode structure
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="A valid PDF file is required.")

    logger.info(
        f"User '{current_user.id}' initiating VizMind AI processing for file: {file.filename}"
    )

    s3_file_path = None
    try:
        # Handle file upload to S3 if configured
        if s3_service_instance.is_configured():
            s3_object_name = (
                f"user_{current_user.id}/uploads/{uuid.uuid4()}-{file.filename}"
            )
            file_content = await file.read()
            s3_file_path = await s3_service_instance.upload_pdf_bytes_async(
                file_content, s3_object_name
            )
            logger.info(f"File uploaded to S3: {s3_file_path}")
            file_path_for_processing = s3_file_path
        else:
            # Fallback for local development without S3
            # Note: This is not recommended for production
            file_path_for_processing = file.filename
            logger.warning(
                "S3 not configured. Using temporary filename for processing."
            )

        # Generate concept map ID
        map_id = str(ObjectId())

        # Initialize VizMind AI service
        vizmind_service = VizMindAIService()

        # Execute the document processing workflow
        result = await vizmind_service.process_document_and_generate_mindmap(
            file_path=file_path_for_processing,
            user_id=current_user.id,
            s3_path=s3_file_path,
            original_filename=file.filename,
            map_id=map_id,
        )

        logger.info(f"VizMind AI processing completed with status: {result.status}")
        return result

    except Exception as e:
        logger.error(f"Unexpected error in mind map generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during mind map generation: {str(e)}",
        )

    except Exception as e:
        logger.error(f"Error in generate_mindmap_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred during mind map generation.",
        )


@router.get("/history", tags=["VizMind AI Mind Maps"])
async def get_map_history_endpoint(
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Retrieves the user's mind map history from VizMind AI.
    """
    try:
        db = get_db()
        cm_collection = db[settings.MONGODB_MAPS_COLLECTION]
        maps_cursor = cm_collection.find(
            {"user_id": current_user.id},
            {
                "_id": 1,
                "title": 1,
                "original_filename": 1,
                "created_at": 1,
                "processing_metadata": 1,
            },
        ).sort("created_at", -1)

        history = []
        for map_doc in maps_cursor:
            processing_metadata = map_doc.get("processing_metadata", {})
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
                    "chunk_count": processing_metadata.get("chunk_count"),
                    "processing_time": processing_metadata.get("processing_time"),
                }
            )

        logger.info(
            f"Retrieved {len(history)} VizMind AI maps for user {current_user.email}"
        )
        return {"history": history}
    except PyMongoError as e:
        logger.error(
            f"Database error retrieving map history for user {current_user.email}: {e}"
        )
        raise HTTPException(status_code=500, detail="Database error occurred")


@router.get("/{map_id}", tags=["VizMind AI Mind Maps"])
async def get_mind_map_endpoint(
    map_id: str,
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Retrieves a specific VizMind AI mind map by ID.
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(map_id):
            raise HTTPException(status_code=400, detail="Invalid map ID format")

        db = get_db()
        cm_collection = db[settings.MONGODB_MAPS_COLLECTION]
        map_doc = cm_collection.find_one(
            {"_id": ObjectId(map_id), "user_id": current_user.id}
        )

        if not map_doc:
            raise HTTPException(status_code=404, detail="Mind map not found")

        processing_metadata = map_doc.get("processing_metadata", {})

        return {
            "mongodb_doc_id": str(map_doc["_id"]),
            "title": map_doc.get("title", "Unknown"),
            "hierarchical_data": map_doc.get("hierarchical_data"),
            "original_filename": map_doc.get("original_filename"),
            "processing_metadata": processing_metadata,
            "created_at": map_doc.get("created_at"),
            "updated_at": map_doc.get("updated_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error retrieving map {map_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
