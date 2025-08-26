from fastapi import APIRouter, Body, HTTPException, Depends

from app.core.config import logger, settings
from app.models.user_models import UserModelInDB
from app.models.chat_models import (
    ChatHistoryResponse,
)
from app.api.v1.deps import get_current_active_user
from app.services.chat_service import ChatService
from app.db.mongodb_utils import get_db
from bson import ObjectId

from app.models.cmvs_models import NodeDetailResponse
from app.services.vizmind_service import VizMindAIService

router = APIRouter()


@router.post("/", response_model=NodeDetailResponse, tags=["VizMind AI RAG"])
async def ask_question_endpoint(
    current_user: UserModelInDB = Depends(get_current_active_user),
    question: str = Body(..., description="The user's question"),
    map_id: str = Body(..., description="MongoDB document ID of the mind map"),
    node_id: str = Body(None, description="ID of the node (for chat history context)"),
    node_label: str = Body(
        None, description="Label of the node (for chat history context)"
    ),
    top_k: int = Body(10, description="Number of relevant chunks to retrieve"),
):
    """
    Unified endpoint for asking questions about mind maps.

    Flow:
    1. Check if the exact question already exists in chat history for this node
    2. If found, return the cached answer from history
    3. If not found, run RAG workflow and save both question and answer to history
    """
    if not question:
        raise HTTPException(status_code=400, detail="A question is required.")

    logger.info(f"User '{current_user.email}' asking: '{question[:100]}...'")

    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(map_id):
            raise HTTPException(status_code=400, detail="Invalid map ID format")

        # Verify the mind map exists and belongs to the user
        db = get_db()
        cm_collection = db[settings.MONGODB_MAPS_COLLECTION]
        map_doc = cm_collection.find_one(
            {"_id": ObjectId(map_id), "user_id": current_user.id}
        )

        if not map_doc:
            raise HTTPException(status_code=404, detail="Mind map not found")

        # Initialize chat service for history management
        from app.services.chat_service import ChatService
        from app.models.chat_models import ChatMessage
        import uuid
        from datetime import datetime, timezone

        chat_service = ChatService()

        # If node information is provided, check chat history first
        if node_id and node_label:
            # Check if this exact question already exists in chat history
            conversation_history = await chat_service.get_conversation_history(
                user_id=current_user.id, map_id=map_id, node_id=node_id
            )

            # Look for exact question match in chat history
            if conversation_history.messages:
                for i, msg in enumerate(conversation_history.messages):
                    if (
                        msg.type == "question"
                        and msg.content.strip().lower() == question.strip().lower()
                    ):
                        # Found exact question, look for the corresponding answer
                        if i + 1 < len(conversation_history.messages):
                            answer_msg = conversation_history.messages[i + 1]
                            if answer_msg.type == "answer":
                                logger.info(
                                    f"Returning cached answer for question: '{question[:50]}...'"
                                )
                                # Convert cached answer back to NodeDetailResponse format
                                from app.models.cmvs_models import CitationSource

                                cited_sources = []
                                for source in answer_msg.cited_sources:
                                    cited_sources.append(CitationSource(**source))

                                return NodeDetailResponse(
                                    query=question,
                                    answer=answer_msg.content,
                                    cited_sources=cited_sources,
                                    message="Retrieved from chat history",
                                )

            # Get recent messages for context (limit to 5 to reduce token count)
            recent_messages = await chat_service.get_recent_messages_for_context(
                user_id=current_user.id, map_id=map_id, node_id=node_id, limit=5
            )

            # Format context for LLM
            context = chat_service.format_messages_for_llm_context(recent_messages)

            # Prepare the enhanced query with context
            enhanced_query = question
            if context:
                enhanced_query = f"{context}\n{question}"
        else:
            enhanced_query = question

        # Question not found in history, run RAG workflow
        logger.info(f"Running RAG workflow for new question: '{question[:50]}...'")
        vizmind_service = VizMindAIService()
        response = await vizmind_service.query_mind_map(
            user_id=current_user.id,
            map_id=map_id,
            query=enhanced_query,
            top_k=top_k,
        )

        # Save both question and answer to chat history if node info provided
        if node_id and node_label:
            # Save the question
            question_message = ChatMessage(
                id=str(uuid.uuid4()),
                type="question",
                content=question,
                cited_sources=[],
                timestamp=datetime.now(timezone.utc),
                node_id=node_id,
                user_id=current_user.id,
                map_id=map_id,
            )

            await chat_service.save_message(
                user_id=current_user.id,
                map_id=map_id,
                node_id=node_id,
                node_label=node_label,
                message=question_message,
            )

            # Save the answer
            answer_message = ChatMessage(
                id=str(uuid.uuid4()),
                type="answer",
                content=response.answer,
                cited_sources=[
                    source.model_dump() for source in response.cited_sources
                ],
                timestamp=datetime.now(timezone.utc),
                node_id=node_id,
                user_id=current_user.id,
                map_id=map_id,
            )

            await chat_service.save_message(
                user_id=current_user.id,
                map_id=map_id,
                node_id=node_id,
                node_label=node_label,
                message=answer_message,
            )

            logger.info(
                f"New question and answer saved to chat history for node {node_id}"
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API Error in ask_question_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An internal server error occurred: {e}"
        )


@router.delete(
    "/delete/{map_id}/{node_id}",
    response_model=ChatHistoryResponse,
    tags=["Chat History"],
)
async def delete_chat_history_endpoint(
    map_id: str,
    node_id: str,
    current_user: UserModelInDB = Depends(get_current_active_user),
):
    """
    Soft delete chat history for a specific node.
    """
    try:
        # Validate map_id format
        if not ObjectId.is_valid(map_id):
            raise HTTPException(status_code=400, detail="Invalid map ID format")

        # Verify the mind map exists and belongs to the user
        db = get_db()
        cm_collection = db[settings.MONGODB_MAPS_COLLECTION]
        map_doc = cm_collection.find_one(
            {"_id": ObjectId(map_id), "user_id": current_user.id}
        )

        if not map_doc:
            raise HTTPException(status_code=404, detail="Mind map not found")

        chat_service = ChatService()
        result = await chat_service.soft_delete_conversation(
            user_id=current_user.id, map_id=map_id, node_id=node_id
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
