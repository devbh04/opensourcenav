"""
Chat Agent — RAG-based chatbot that answers questions about a specific repo.
Uses the per-repo Qdrant collection for context retrieval.
"""
import logging
import uuid
from datetime import datetime
from app.services.llm_service import get_llm
from app.db.qdrant import search_vectors, repo_to_collection_name, collection_exists
from app.db.mongodb import get_collection
from app.services.embedding_service import embed_single
from app.models.chat import (
    ChatRequest, ChatResponse, ChatSource,
    ChatMessage, ChatSession,
)

logger = logging.getLogger(__name__)


async def chat_with_repo(request: ChatRequest) -> ChatResponse:
    """
    Answer a question about a specific repository using RAG.

    1. Route to the correct Qdrant collection based on repo_name
    2. Embed the question
    3. Retrieve relevant chunks
    4. Build context and ask LLM
    5. Store in chat history
    """
    repo_name = request.repo_name
    question = request.question
    user_id = request.user_id
    session_id = request.session_id or uuid.uuid4().hex

    logger.info(f"[chat] Question for {repo_name}: {question[:80]}...")

    # 1. Check collection exists
    coll_name = repo_to_collection_name(repo_name)
    if not collection_exists(coll_name):
        return ChatResponse(
            answer=f"No documentation found for **{repo_name}**. Please generate docs first.",
            sources=[],
            session_id=session_id,
        )

    # 2. Get chat history for context
    history_messages = await _get_recent_history(session_id, limit=6)
    history_context = ""
    if history_messages:
        history_context = "Previous conversation:\n"
        for msg in history_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_context += f"{role}: {msg['content'][:200]}\n"
        history_context += "\n"

    # 3. Embed the question and search
    question_embedding = embed_single(question)
    search_results = search_vectors(
        collection_name=coll_name,
        query_vector=question_embedding,
        top_k=8,
        score_threshold=0.3,
    )

    # 4. Build context from search results
    sources = []
    context_parts = []
    for result in search_results:
        file_path = result.get("file_path", "unknown")
        content = result.get("content", "")
        score = result.get("score", 0.0)

        context_parts.append(
            f"--- File: {file_path} (relevance: {score:.2f}) ---\n{content}"
        )
        sources.append(ChatSource(
            file_path=file_path,
            content_preview=content[:150],
            score=score,
        ))

    context_text = "\n\n".join(context_parts)

    # 5. Ask LLM
    llm = get_llm(temperature=0.3)

    prompt = f"""You are a helpful documentation assistant for the repository "{repo_name}".
Answer the user's question based on the code context provided below.

{history_context}

Code Context:
{context_text[:8000]}

User Question: {question}

Instructions:
- Answer based on the actual code context provided
- Use code blocks with proper syntax highlighting when showing code
- Reference specific file paths when relevant
- If the context doesn't contain enough information, say so honestly
- Be concise but thorough
- Format your response in Markdown"""

    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()
    except Exception as e:
        logger.error(f"[chat] LLM failed: {e}")
        answer = "I'm sorry, I encountered an error processing your question. Please try again."

    # 6. Store in chat history
    await _store_message(session_id, user_id, repo_name, "user", question)
    await _store_message(session_id, user_id, repo_name, "assistant", answer, sources)

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=session_id,
        tokens_used=len(prompt) // 4 + len(answer) // 4,
    )


async def _get_recent_history(session_id: str, limit: int = 6) -> list[dict]:
    """Get recent messages from a chat session."""
    col = await get_collection("chat_sessions")
    session = await col.find_one({"session_id": session_id})
    if not session:
        return []
    messages = session.get("messages", [])
    return messages[-limit:]


async def _store_message(
    session_id: str,
    user_id: str,
    repo_name: str,
    role: str,
    content: str,
    sources: list[ChatSource] | None = None,
) -> None:
    """Store a message in the chat session."""
    col = await get_collection("chat_sessions")

    message = {
        "role": role,
        "content": content,
        "sources": [s.model_dump() for s in (sources or [])],
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Upsert the session
    await col.update_one(
        {"session_id": session_id},
        {
            "$push": {"messages": message},
            "$set": {
                "user_id": user_id,
                "repo_name": repo_name,
                "last_active": datetime.utcnow().isoformat(),
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow().isoformat(),
            },
        },
        upsert=True,
    )


async def get_chat_sessions(user_id: str) -> list[dict]:
    """Get all chat sessions for a user."""
    col = await get_collection("chat_sessions")
    cursor = col.find(
        {"user_id": user_id},
        {"messages": 0},  # Exclude messages for listing
    ).sort("last_active", -1)

    sessions = []
    async for doc in cursor:
        sessions.append({
            "session_id": doc["session_id"],
            "repo_name": doc["repo_name"],
            "last_active": doc.get("last_active", ""),
            "created_at": doc.get("created_at", ""),
        })
    return sessions
