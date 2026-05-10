"""
Node: Embed Repository — chunks all files and stores vectors in Qdrant.
"""
import logging
from app.utils.chunker import chunk_files
from app.services.embedding_service import embed_texts
from app.db.qdrant import repo_to_collection_name, ensure_collection, upsert_vectors

logger = logging.getLogger(__name__)


def embed_repo(state: dict) -> dict:
    """
    Chunk all repository files and embed them into Qdrant.

    Reads from state: files, repo_name
    Writes to state: qdrant_collection, chunks_count
    """
    files = state["files"]
    repo_name = state.get("repo_name", "unknown")

    logger.info(f"[embed_repo] Chunking {len(files)} files for embedding")

    # 1. Chunk all files
    chunks = chunk_files(files)

    if not chunks:
        logger.warning("[embed_repo] No chunks generated")
        return {
            **state,
            "qdrant_collection": "",
            "chunks_count": 0,
        }

    # 2. Create/ensure Qdrant collection
    collection_name = repo_to_collection_name(repo_name)
    ensure_collection(collection_name)

    # 3. Generate embeddings
    # Prepare text for embedding: combine file path + content for better search
    embed_texts_list = [
        f"File: {chunk['file_path']}\n{chunk['content']}"
        for chunk in chunks
    ]

    logger.info(f"[embed_repo] Generating embeddings for {len(chunks)} chunks...")
    vectors = embed_texts(embed_texts_list)

    # Validate: vectors count must match chunks count
    if len(vectors) != len(chunks):
        logger.error(
            f"[embed_repo] MISMATCH: {len(vectors)} vectors for {len(chunks)} chunks! "
            f"Some chunks may not be searchable."
        )

    # 4. Prepare payloads — only for chunks that have a corresponding vector
    count = min(len(vectors), len(chunks))
    payloads = [
        {
            "file_path": chunks[i]["file_path"],
            "content": chunks[i]["content"],
            "chunk_index": chunks[i]["chunk_index"],
            "start_line": chunks[i].get("start_line", 0),
            "end_line": chunks[i].get("end_line", 0),
            "language": chunks[i].get("language", "text"),
        }
        for i in range(count)
    ]

    # 5. Upsert into Qdrant
    ids = [str(i) for i in range(count)]
    used_vectors = vectors[:count]
    upsert_vectors(collection_name, ids, used_vectors, payloads)

    logger.info(f"[embed_repo] Stored {count} vectors in collection '{collection_name}'")

    return {
        **state,
        "qdrant_collection": collection_name,
        "chunks_count": len(chunks),
    }
