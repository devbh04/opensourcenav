"""
Centralized LLM factory — provides a unified interface for LLM calling.

Now upgraded to use the native Google GenAI SDK to fully support the new
gemini-3-flash-preview model, bypassing LangChain limitations.
Provides a simple wrapper that mimics LangChain's `.invoke().content` interface
so that existing agent nodes don't need rewriting.
"""
import logging
from google import genai
from google.genai.types import HttpOptions
from app.config import GCP_PROJECT, GCP_LOCATION, LLM_MODEL, GOOGLE_API_KEY

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
            logger.info(f"Google GenAI LLM client initialized (API Key)")
        else:
            # Vertex AI (Requires ADC or Service Account)
            _client = genai.Client(
                vertexai=True,
                project=GCP_PROJECT,
                location=GCP_LOCATION,
                http_options=HttpOptions(api_version="v1"),
            )
            logger.info(f"Google GenAI LLM client initialized (Vertex AI)")
    return _client


# ── Wrapper ──────────────────────────────────────────────────────────

class DummyResponse:
    def __init__(self, content: str):
        self.content = content


class NativeLLMWrapper:
    """
    A lightweight wrapper around Google GenAI client.
    Exposes a `.invoke(prompt)` method that returns an object with a `.content` attribute,
    making it a drop-in replacement for ChatGoogleGenerativeAI in our existing nodes.
    """
    def __init__(self, model: str, temperature: float, max_output_tokens: int):
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.client = _get_client()

    def invoke(self, prompt: str) -> DummyResponse:
        """Call Gemini model and return wrapped text response."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                }
            )
            # Gemini 3.0 / 2.5 flash may return text directly
            text = response.text if response.text else ""
            return DummyResponse(text)
        except Exception as e:
            logger.error(f"NativeLLMWrapper invoke failed for {self.model}: {e}")
            raise


def get_llm(
    model: str | None = None,
    temperature: float = 0.2,
    max_output_tokens: int = 8192,
) -> NativeLLMWrapper:
    """
    Return a NativeLLMWrapper instance configured with ADC.
    
    Uses the new Google GenAI SDK (google-genai) to support gemini-3-flash-preview.
    """
    return NativeLLMWrapper(
        model=model or LLM_MODEL,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
