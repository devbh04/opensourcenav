"""
Embedding service — generates vector embeddings using Google's
gemini-embedding-2 model via Vertex AI (ADC-authenticated).

gemini-embedding-2 is Google's latest embedding model:
  - Up to 3072 dimensions (configurable)
  - 8192 max input tokens
  - Supports task_type for optimized retrieval
"""
import logging
from google import genai
from google.genai.types import HttpOptions, EmbedContentConfig
from app.config import GCP_PROJECT, GCP_LOCATION, EMBEDDING_MODEL, EMBEDDING_DIMENSION, GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# ── Singleton Client ─────────────────────────────────────────────────
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Lazy-init the Google GenAI client (API Key or Vertex AI)."""
    global _client
    if _client is None:
        if GOOGLE_API_KEY:
            # Simple API Key (Google AI Studio)
            _client = genai.Client(api_key=GOOGLE_API_KEY)
            logger.info(f"Google GenAI embedding client initialized (API Key)")
        else:
            # Vertex AI (Requires ADC or Service Account)
            _client = genai.Client(
                vertexai=True,
                project=GCP_PROJECT,
                location=GCP_LOCATION,
                http_options=HttpOptions(api_version="v1"),
            )
            logger.info(f"Google GenAI embedding client initialized (Vertex AI)")
    return _client


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Generate embeddings for a list of texts using Google's embedding model.

    IMPORTANT: client.models.embed_content() treats a list of strings as
    multi-part content (ONE embedding). To get one embedding per text,
    we must call it once per text.

    We batch the calls in groups to avoid overwhelming the API,
    with error handling per-text so one failure doesn't kill the batch.

    Args:
        texts: list of strings to embed
        task_type: one of RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, SEMANTIC_SIMILARITY,
                   CLASSIFICATION, CLUSTERING, QUESTION_ANSWERING, FACT_VERIFICATION

    Returns:
        list of embedding vectors (each is a list of floats), one per input text
    """
    if not texts:
        return []

    client = _get_client()
    all_embeddings: list[list[float]] = []

    config = EmbedContentConfig(
        task_type=task_type,
        output_dimensionality=EMBEDDING_DIMENSION,
    )

    for i, text in enumerate(texts):
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,  # Single string → 1 embedding
                config=config,
            )
            all_embeddings.append(result.embeddings[0].values)
        except Exception as e:
            logger.error(f"[embed_texts] Text {i+1}/{len(texts)} failed: {e}")
            # Append zero vector to keep indexing aligned with chunks
            all_embeddings.append([0.0] * EMBEDDING_DIMENSION)

        # Log progress every 50 texts
        if (i + 1) % 50 == 0:
            logger.info(f"[embed_texts] Progress: {i+1}/{len(texts)} embeddings generated")

    logger.info(f"[embed_texts] Generated {len(all_embeddings)} embeddings from {len(texts)} texts")
    return all_embeddings


def embed_single(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    """
    Generate embedding for a single text string.
    Uses RETRIEVAL_QUERY task_type by default (optimized for search queries).
    """
    results = embed_texts([text], task_type=task_type)
    return results[0] if results else [0.0] * EMBEDDING_DIMENSION
