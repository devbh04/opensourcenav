"""
Pydantic models for the RAG-based chatbot.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Chat message from a user on a specific repo's doc page."""
    question: str = Field(..., description="User's question")
    repo_name: str = Field(..., description="owner/repo — identifies the Qdrant collection")
    user_id: str = Field(..., description="Guest user ID")
    session_id: str = Field("", description="Chat session ID for history continuity")


class ChatSource(BaseModel):
    """A source chunk referenced in the answer."""
    file_path: str
    content_preview: str = ""
    score: float = 0.0


class ChatResponse(BaseModel):
    """Chat response with sources."""
    answer: str
    sources: list[ChatSource] = []
    session_id: str = ""
    tokens_used: int = 0


class ChatMessage(BaseModel):
    """Single message in chat history (stored in MongoDB)."""
    role: str  # "user" or "assistant"
    content: str
    sources: list[ChatSource] = []
    timestamp: str = ""


class ChatSession(BaseModel):
    """Chat session record in MongoDB."""
    session_id: str
    user_id: str
    repo_name: str
    messages: list[ChatMessage] = []
    created_at: str = ""
    last_active: str = ""
