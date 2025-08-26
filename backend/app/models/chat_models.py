from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Represents a single chat message in the conversation."""

    id: str = Field(description="Unique identifier for the message")
    type: str = Field(description="Type of message: 'question' or 'answer'")
    content: str = Field(description="The actual message content")
    cited_sources: Optional[List[Dict[str, Any]]] = Field(
        default=[], description="Sources for answers"
    )
    timestamp: datetime = Field(description="When the message was created")
    node_id: str = Field(description="The node this message relates to")
    user_id: str = Field(description="ID of the user who created this message")
    map_id: str = Field(description="ID of the mind map this conversation belongs to")


class ChatConversation(BaseModel):
    """Represents a chat conversation for a specific node."""

    id: str = Field(description="Unique identifier for the conversation")
    map_id: str = Field(description="MongoDB document ID of the mind map")
    node_id: str = Field(description="ID of the node this conversation is about")
    node_label: str = Field(description="Label of the node for context")
    user_id: str = Field(description="ID of the user who owns this conversation")
    messages: List[ChatMessage] = Field(
        default=[], description="List of messages in the conversation"
    )
    created_at: datetime = Field(description="When the conversation was created")
    updated_at: datetime = Field(description="When the conversation was last updated")
    is_deleted: bool = Field(default=False, description="Soft delete flag")


class ChatHistoryResponse(BaseModel):
    """Response model for chat history operations."""

    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Success or error message")
    conversation_id: Optional[str] = Field(
        default=None, description="ID of the conversation"
    )


class GetChatHistoryResponse(BaseModel):
    """Response model for retrieving chat history."""

    conversation: Optional[ChatConversation] = Field(
        default=None, description="The conversation data"
    )
    messages: List[ChatMessage] = Field(
        default=[], description="List of messages in the conversation"
    )
