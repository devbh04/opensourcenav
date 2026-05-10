"""
MongoDB async client — provides access to all collections.

Collections:
  - users     : guest user records
  - queue     : job queue with status tracking
  - docs      : generated documentation per repo
  - chat_sessions : chat history per user per repo

Supports both local MongoDB and MongoDB Atlas (mongodb+srv://).
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import MONGODB_URI, MONGODB_DB_NAME

logger = logging.getLogger(__name__)

# ── Singleton Client ─────────────────────────────────────────────────
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def get_db() -> AsyncIOMotorDatabase:
    """Return the database instance, creating the client on first call."""
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
        _db = _client[MONGODB_DB_NAME]
        logger.info(f"Connected to MongoDB: {MONGODB_URI[:40]}.../{MONGODB_DB_NAME}")
        # Create indexes (graceful — don't crash the server if it fails)
        try:
            await _create_indexes(_db)
        except Exception as e:
            logger.warning(f"Failed to create MongoDB indexes (will retry later): {e}")
    return _db


async def _create_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create required indexes for performance."""
    # Users
    await db.users.create_index("user_id", unique=True)

    # Queue
    await db.queue.create_index("job_id", unique=True)
    await db.queue.create_index("user_id")
    await db.queue.create_index("status")
    await db.queue.create_index("created_at")

    # Docs
    await db.docs.create_index("repo_name", unique=True)
    await db.docs.create_index("repo_url")
    await db.docs.create_index("generated_by")

    # Chat sessions
    await db.chat_sessions.create_index("session_id", unique=True)
    await db.chat_sessions.create_index([("user_id", 1), ("repo_name", 1)])

    logger.info("MongoDB indexes created")


async def close_db() -> None:
    """Close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


# ── Convenience Helpers ──────────────────────────────────────────────

async def get_collection(name: str):
    """Shorthand to get a collection handle."""
    db = await get_db()
    return db[name]
