from datetime import datetime, timezone
from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Depends,
    Query,
    Body,
)
import uuid

from app.core.config import logger, settings
from app.models.user_models import UserModelInDB
from app.models.cmvs_models import (
    HierarchicalNode,
    NodeDetailResponse,
    MindMapResponse,
)
from app.api.v1.deps import get_current_active_user
from app.services.s3_service import S3Service
from app.services.rag_service import RAGService
from app.services.mind_map_service import MindMapService
from app.db.mongodb_utils import get_db
from bson import ObjectId
from pymongo.errors import PyMongoError

router = APIRouter()
s3_service_instance = S3Service()


@router.post(
    "/generate-mindmap", response_model=MindMapResponse, tags=["Docling Mind Maps"]
)
async def generate_mindmap_endpoint(
    file: UploadFile = File(..., description="PDF file to process and ingest for RAG."),
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Generates a mind map from a PDF, and simultaneously chunks and ingests
    its content into the vector store for future RAG queries.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="A valid PDF file is required.")

    logger.info(
        f"User '{current_user.id}' initiating processing for file: {file.filename}"
    )

    s3_file_path = None
    try:
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

        concept_map_id = str(ObjectId())

        service = MindMapService(
            file_path=file_path_for_processing,
            user_id=current_user.id,
            concept_map_id=concept_map_id,
            s3_path=s3_file_path,
            original_filename=file.filename,
        )

        mind_map_data_dict = await service.generate_and_ingest()

        if "error" in mind_map_data_dict:
            raise HTTPException(status_code=500, detail=mind_map_data_dict["error"])

        hierarchical_node = HierarchicalNode(**mind_map_data_dict)

        db = get_db()
        cm_collection = db[settings.MONGODB_CMVS_COLLECTION]
        mindmap_doc = {
            "_id": ObjectId(concept_map_id),
            "user_id": current_user.id,
            "title": file.filename.replace(".pdf", ""),
            "original_filename": file.filename,
            "s3_path": s3_file_path,
            "hierarchical_data": mind_map_data_dict,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        cm_collection.insert_one(mindmap_doc)

        return MindMapResponse(
            attachment={
                "filename": file.filename,
                "s3_path": s3_file_path,
                "status": "success",
            },
            status="success",
            hierarchical_data=hierarchical_node,
            mongodb_doc_id=concept_map_id,
        )

    except Exception as e:
        logger.error(f"Error in generate_mindmap_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred during mind map generation.",
        )


@router.get("/history", tags=["Docling Mind Maps"])
async def get_map_history_endpoint(
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Retrieves the user's mind map history.
    """
    try:
        db = get_db()
        cm_collection = db[settings.MONGODB_CMVS_COLLECTION]
        maps_cursor = cm_collection.find(
            {"user_id": current_user.id},
            {"_id": 1, "title": 1, "original_filename": 1, "created_at": 1},
        ).sort("created_at", -1)
        history = [
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
            for map_doc in maps_cursor
        ]
        logger.info(f"Retrieved {len(history)} maps for user {current_user.email}")
        return {"history": history}
    except PyMongoError as e:
        logger.error(
            f"Database error retrieving map history for user {current_user.email}: {e}"
        )
        raise HTTPException(status_code=500, detail="Database error occurred")


@router.get("/details", response_model=NodeDetailResponse, tags=["Docling RAG"])
async def get_node_details_endpoint(
    map_id: str = Query(..., description="MongoDB document ID of the mind map"),
    node_query: str = Query(..., description="Query about a specific node or concept"),
    top_k: int = Query(3, description="Number of relevant chunks to retrieve"),
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Get detailed information about a specific node or concept in a mind map using RAG.
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(map_id):
            raise HTTPException(status_code=400, detail="Invalid map ID format")

        # Get the mind map document from MongoDB
        db = get_db()
        cm_collection = db[settings.MONGODB_CMVS_COLLECTION]
        map_doc = cm_collection.find_one(
            {"_id": ObjectId(map_id), "user_id": current_user.id}
        )

        if not map_doc:
            raise HTTPException(status_code=404, detail="Mind map not found")

        logger.info(
            f"User '{current_user.email}' querying node: '{node_query}' for map: {map_id}"
        )

        # Use RAG service to get detailed information
        rag_service = RAGService(user_id=current_user.id, concept_map_id=map_id)
        response = await rag_service.run_rag(node_query, top_k=top_k)

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Extract cited sources from the context documents
        cited_sources = []
        context_docs = response.get("context", [])

        for doc in context_docs:
            # Handle LangChain Document objects
            if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                # Extract title from H1 or H2 metadata, or use a default
                title = (
                    doc.metadata.get("H1")
                    or doc.metadata.get("H2")
                    or "Untitled Section"
                )

                # Extract page number from metadata
                page_number = doc.metadata.get("page")
                if page_number is not None:
                    try:
                        page_number = int(page_number)
                    except (ValueError, TypeError):
                        page_number = None

                # Create snippet from page content (first 200 characters)
                snippet = (
                    (
                        doc.page_content[:200] + "..."
                        if len(doc.page_content) > 200
                        else doc.page_content
                    )
                    if doc.page_content
                    else None
                )

                citation = {
                    "type": "document",
                    "identifier": str(doc.metadata.get("_id", "unknown")),
                    "source": doc.metadata.get("original_filename", "Unknown Source"),
                    "title": title,
                    "page_number": page_number,
                    "snippet": snippet,
                    "content": (
                        doc.page_content[:500] + "..."
                        if len(doc.page_content) > 500
                        else doc.page_content
                    ),
                    "metadata": {
                        "page": doc.metadata.get("page", "N/A"),
                        "section": doc.metadata.get("H1", "N/A"),
                        "chunk_id": str(doc.metadata.get("_id", "N/A")),
                    },
                }
                cited_sources.append(citation)

        return NodeDetailResponse(
            query=node_query,
            answer=response.get("answer", "No answer generated."),
            cited_sources=cited_sources,
            message="Successfully retrieved node details using Docling RAG.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_node_details_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")


@router.get("/{map_id}", tags=["Docling Mind Maps"])
async def get_mind_map_endpoint(
    map_id: str,
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Retrieves a specific mind map by ID.
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(map_id):
            raise HTTPException(status_code=400, detail="Invalid map ID format")

        db = get_db()
        cm_collection = db[settings.MONGODB_CMVS_COLLECTION]
        map_doc = cm_collection.find_one(
            {"_id": ObjectId(map_id), "user_id": current_user.id}
        )

        if not map_doc:
            raise HTTPException(status_code=404, detail="Mind map not found")

        return {
            "mongodb_doc_id": str(map_doc["_id"]),
            "title": map_doc.get("title", "Unknown"),
            "hierarchical_data": map_doc.get("hierarchical_data"),
            "original_filename": map_doc.get("original_filename"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error retrieving map {map_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")


@router.post("/ask", response_model=NodeDetailResponse, tags=["Docling RAG"])
async def ask_question_endpoint(
    current_user: UserModelInDB = Depends(get_current_active_user),
    question: str = Body(..., description="The user's question"),
    map_id: str = Body(..., description="MongoDB document ID of the mind map"),
):
    """
    Answers a specific question related to a concept within a given mind map,
    using a RAG pipeline with Docling.
    """
    if not question:
        raise HTTPException(status_code=400, detail="A question is required.")

    logger.info(f"User '{current_user.email}' asking: '{question}'")

    try:
        # Add top_k parameter (you might want to make this configurable)
        rag_service = RAGService(user_id=current_user.id, concept_map_id=map_id)
        response = await rag_service.run_rag(question, top_k=3)

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Extract cited sources from the context documents
        cited_sources = []
        context_docs = response.get("context", [])

        for doc in context_docs:
            # Handle LangChain Document objects
            if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                # Extract title from H1 or H2 metadata, or use a default
                title = (
                    doc.metadata.get("H1")
                    or doc.metadata.get("H2")
                    or "Untitled Section"
                )

                # Extract page number from metadata
                page_number = doc.metadata.get("page")
                if page_number is not None:
                    try:
                        page_number = int(page_number)
                    except (ValueError, TypeError):
                        page_number = None

                # Create snippet from page content (first 200 characters)
                snippet = (
                    (
                        doc.page_content[:200] + "..."
                        if len(doc.page_content) > 200
                        else doc.page_content
                    )
                    if doc.page_content
                    else None
                )

                citation = {
                    "type": "document",
                    "identifier": str(doc.metadata.get("_id", "unknown")),
                    "source": doc.metadata.get("original_filename", "Unknown Source"),
                    "title": title,
                    "page_number": page_number,
                    "snippet": snippet,
                    "content": (
                        doc.page_content[:500] + "..."
                        if len(doc.page_content) > 500
                        else doc.page_content
                    ),
                    "metadata": {
                        "page": doc.metadata.get("page", "N/A"),
                        "section": doc.metadata.get("H1", "N/A"),
                        "chunk_id": str(doc.metadata.get("_id", "N/A")),
                    },
                }
                cited_sources.append(citation)

        return NodeDetailResponse(
            query=question,
            answer=response.get("answer", "No answer generated."),
            cited_sources=cited_sources,
            message="Successfully retrieved answer using Docling RAG.",
        )
    except Exception as e:
        logger.error(f"API Error in ask_question_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An internal server error occurred: {e}"
        )
