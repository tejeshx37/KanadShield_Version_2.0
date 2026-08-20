"""Provider interfaces. Every AI capability is accessed through one of
these — call sites never talk to Ollama/OpenAI/Tesseract/Whisper directly,
so a commercial provider can be swapped in via config alone."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        json_schema: dict[str, Any] | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.1,
    ) -> str:
        """Return raw text completion. If json_schema is given, the provider
        should constrain/validate output to match it where the backend
        supports it; callers still validate against a Pydantic model."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str: ...


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...


@dataclass
class OCRResult:
    text: str
    language: str
    confidence: float


class OCRProvider(ABC):
    @abstractmethod
    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> OCRResult:
        raise NotImplementedError


@dataclass
class TranscriptionResult:
    text: str
    language: str
    confidence: float


class SpeechProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language_hint: str | None = None) -> TranscriptionResult:
        raise NotImplementedError
