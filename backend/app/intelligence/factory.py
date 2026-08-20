from functools import lru_cache

from app.core.config import get_settings
from app.intelligence.providers.base import EmbeddingProvider, LLMProvider, OCRProvider, SpeechProvider
from app.intelligence.providers.embedding_local import LocalEmbeddingProvider
from app.intelligence.providers.llm_ollama import OllamaLLMProvider
from app.intelligence.providers.llm_openai_compatible import OpenAICompatibleLLMProvider
from app.intelligence.providers.ocr_tesseract import TesseractOCRProvider
from app.intelligence.providers.speech_whisper import FasterWhisperSpeechProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.AI_PROVIDER == "openai_compatible":
        return OpenAICompatibleLLMProvider(settings)
    return OllamaLLMProvider(settings)


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return LocalEmbeddingProvider(get_settings())


@lru_cache
def get_ocr_provider() -> OCRProvider:
    return TesseractOCRProvider()


@lru_cache
def get_speech_provider() -> SpeechProvider:
    return FasterWhisperSpeechProvider(get_settings())
