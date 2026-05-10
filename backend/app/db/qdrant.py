"""
Qdrant vector DB client — manages per-repo collections.

Each repo gets its own collection named `{owner}__{repo}` so that
RAG queries are scoped to the correct codebase.

Supports both local (host:port) and Qdrant Cloud (url + api_key).
"""
import logging
import re
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.config import (
    QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY, QDRANT_IS_CLOUD,
    EMBEDDING_DIMENSION,
)

logger = logging.getLogger(__name__)

# ── Singleton Client ─────────────────────────────────────────────────
_client: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    """Return the Qdrant client, creating it on first call."""
    global _client
    if _client is None:
        if QDRANT_IS_CLOUD:
            # Cloud — connect via HTTPS URL + API key
            _client = QdrantClient(
                url=QDRANT_HOST,
                api_key=QDRANT_API_KEY,
                timeout=60.0
            )
            logger.info(f"Connected to Qdrant Cloud: {QDRANT_HOST[:50]}...")
        else:
            # Local — plain host:port
            _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            logger.info(f"Connected to Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    return _client


def repo_to_collection_name(repo_name: str) -> str:
    """
    Convert 'owner/repo' to a valid Qdrant collection name.
    Qdrant allows alphanumeric + underscores + hyphens.
    """
    clean = re.sub(r"[^a-zA-Z0-9_-]", "__", repo_name)
    return clean.lower()


def ensure_collection(collection_name: str) -> None:
    """Create a collection if it doesn't already exist, or recreate if dimensions mismatch."""
    client = get_qdrant()
    collections = [c.name for c in client.get_collections().collections]
    
    if collection_name in collections:
        # Check if dimensions match
        col_info = client.get_collection(collection_name)
        existing_dim = col_info.config.params.vectors.size
        if existing_dim != EMBEDDING_DIMENSION:
            logger.warning(f"Dimension mismatch in {collection_name} ({existing_dim} vs {EMBEDDING_DIMENSION}). Recreating collection.")
            client.delete_collection(collection_name)
            collections.remove(collection_name)
        else:
            logger.info(f"Qdrant collection already exists with correct dimensions: {collection_name}")
            return

    # Create collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=EMBEDDING_DIMENSION,
            distance=Distance.COSINE,
        ),
    )
    logger.info(f"Created Qdrant collection: {collection_name} (dim={EMBEDDING_DIMENSION})")


def upsert_vectors(
    collection_name: str,
    ids: list[str],
    vectors: list[list[float]],
    payloads: list[dict],
) -> None:
    """
    Insert or update vectors in a collection.

    Args:
        ids: unique string IDs for each point
        vectors: embedding vectors
        payloads: metadata dicts (file_path, content, chunk_index, etc.)
    """
    client = get_qdrant()
    points = [
        PointStruct(
            id=idx,  # Qdrant accepts int or uuid-string
            vector=vec,
            payload=payload,
        )
        for idx, (vec, payload) in enumerate(zip(vectors, payloads))
    ]

    # Batch upsert in chunks of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)

    logger.info(f"Upserted {len(points)} vectors into {collection_name}")


def search_vectors(
    collection_name: str,
    query_vector: list[float],
    top_k: int = 10,
    score_threshold: float = 0.3,
    file_path_filter: str | None = None,
) -> list[dict]:
    """
    Semantic search in a collection.

    Returns list of dicts with keys: file_path, content, score, chunk_index, etc.
    """
    client = get_qdrant()

    query_filter = None
    if file_path_filter:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="file_path",
                    match=MatchValue(value=file_path_filter),
                )
            ]
        )

    response = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
        query_filter=query_filter,
    )

    return [
        {
            **hit.payload,
            "score": hit.score,
        }
        for hit in response.points
    ]


def delete_collection(collection_name: str) -> None:
    """Delete a collection entirely."""
    client = get_qdrant()
    try:
        client.delete_collection(collection_name)
        logger.info(f"Deleted Qdrant collection: {collection_name}")
    except Exception as e:
        logger.warning(f"Failed to delete collection {collection_name}: {e}")


def collection_exists(collection_name: str) -> bool:
    """Check if a collection exists."""
    client = get_qdrant()
    collections = [c.name for c in client.get_collections().collections]
    return collection_name in collections
