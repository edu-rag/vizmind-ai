from datetime import datetime, timezone
from typing import List
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from app.db.mongodb_utils import get_chat_collection
from app.models.chat_models import (
    ChatMessage,
    ChatConversation,
    ChatHistoryResponse,
    GetChatHistoryResponse,
)
from app.core.config import logger


class ChatService:
    """Service for managing chat conversations and history."""

    def __init__(self):
        self.chat_collection = get_chat_collection()

    async def save_message(
        self,
        user_id: str,
        map_id: str,
        node_id: str,
        node_label: str,
        message: ChatMessage,
    ) -> ChatHistoryResponse:
        """Save a message to the chat conversation."""
        try:
            # Atomically upsert conversation to prevent duplicate key errors
            conversation_filter = {
                "user_id": user_id,
                "map_id": map_id,
                "node_id": node_id,
            }

            now = datetime.now(timezone.utc)
            message_dict = message.model_dump()

            conversation_doc = self.chat_collection.find_one_and_update(
                conversation_filter,
                {
                    "$push": {"messages": message_dict},
                    "$set": {
                        "node_label": node_label,
                        "updated_at": now,
                        "is_deleted": False,
                    },
                    "$setOnInsert": {
                        "created_at": now,
                    },
                },
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )

            if conversation_doc:
                logger.info(
                    f"Message saved for conversation: {conversation_doc['_id']}"
                )
                return ChatHistoryResponse(
                    success=True,
                    message="Message saved successfully",
                    conversation_id=str(conversation_doc["_id"]),
                )

            logger.error("Failed to save conversation document")
            return ChatHistoryResponse(success=False, message="Failed to save message")

        except PyMongoError as e:
            logger.error(f"Database error saving message: {e}")
            return ChatHistoryResponse(success=False, message="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error saving message: {e}")
            return ChatHistoryResponse(
                success=False, message="An unexpected error occurred"
            )

    async def get_conversation_history(
        self, user_id: str, map_id: str, node_id: str
    ) -> GetChatHistoryResponse:
        """Get chat history for a specific node."""
        try:
            conversation_filter = {
                "user_id": user_id,
                "map_id": map_id,
                "node_id": node_id,
                "is_deleted": False,
            }

            conversation_doc = self.chat_collection.find_one(conversation_filter)

            if not conversation_doc:
                return GetChatHistoryResponse(conversation=None, messages=[])

            # Convert _id to id for Pydantic model
            conversation_doc["id"] = str(conversation_doc["_id"])
            del conversation_doc["_id"]

            conversation = ChatConversation(**conversation_doc)

            logger.info(
                f"Retrieved conversation history for node {node_id}: {len(conversation.messages)} messages"
            )

            return GetChatHistoryResponse(
                conversation=conversation, messages=conversation.messages
            )

        except PyMongoError as e:
            logger.error(f"Database error retrieving conversation history: {e}")
            return GetChatHistoryResponse(conversation=None, messages=[])
        except Exception as e:
            logger.error(f"Unexpected error retrieving conversation history: {e}")
            return GetChatHistoryResponse(conversation=None, messages=[])

    async def get_recent_messages_for_context(
        self, user_id: str, map_id: str, node_id: str, limit: int = 5
    ) -> List[ChatMessage]:
        """Get recent messages for LLM context (limit to reduce token count)."""
        try:
            conversation_filter = {
                "user_id": user_id,
                "map_id": map_id,
                "node_id": node_id,
                "is_deleted": False,
            }

            conversation_doc = self.chat_collection.find_one(conversation_filter)

            if not conversation_doc or not conversation_doc.get("messages"):
                return []

            # Get the last 'limit' messages for context
            messages = conversation_doc["messages"]
            recent_messages = messages[-limit:] if len(messages) > limit else messages

            # Convert to ChatMessage objects
            chat_messages = []
            for msg in recent_messages:
                try:
                    chat_messages.append(ChatMessage(**msg))
                except Exception as e:
                    logger.warning(f"Error parsing message: {e}")
                    continue

            logger.info(f"Retrieved {len(chat_messages)} recent messages for context")
            return chat_messages

        except PyMongoError as e:
            logger.error(f"Database error retrieving recent messages: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving recent messages: {e}")
            return []

    async def soft_delete_conversation(
        self, user_id: str, map_id: str, node_id: str
    ) -> ChatHistoryResponse:
        """Soft delete a conversation (mark as deleted)."""
        try:
            conversation_filter = {
                "user_id": user_id,
                "map_id": map_id,
                "node_id": node_id,
                "is_deleted": False,
            }

            result = self.chat_collection.update_one(
                conversation_filter,
                {
                    "$set": {
                        "is_deleted": True,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            if result.modified_count > 0:
                logger.info(f"Conversation soft deleted for node {node_id}")
                return ChatHistoryResponse(
                    success=True, message="Conversation deleted successfully"
                )
            else:
                logger.warning(f"No conversation found to delete for node {node_id}")
                return ChatHistoryResponse(
                    success=False, message="No conversation found to delete"
                )

        except PyMongoError as e:
            logger.error(f"Database error deleting conversation: {e}")
            return ChatHistoryResponse(success=False, message="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error deleting conversation: {e}")
            return ChatHistoryResponse(
                success=False, message="An unexpected error occurred"
            )

    def format_messages_for_llm_context(self, messages: List[ChatMessage]) -> str:
        """Format recent messages for LLM context."""
        if not messages:
            return ""

        context_parts = []
        context_parts.append("## Previous Conversation Context:")

        for msg in messages:
            if msg.type == "question":
                context_parts.append(f"**User:** {msg.content}")
            elif msg.type == "answer":
                context_parts.append(f"**Assistant:** {msg.content}")

        context_parts.append("## Current Question:")

        return "\n".join(context_parts)
