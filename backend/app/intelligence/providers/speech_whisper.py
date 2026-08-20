import asyncio
import io
import tempfile
from functools import lru_cache

from app.core.config import Settings
from app.intelligence.providers.base import SpeechProvider, TranscriptionResult


@lru_cache(maxsize=1)
def _load_model(model_size: str):
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, device="cpu", compute_type="int8")


class FasterWhisperSpeechProvider(SpeechProvider):
    """Voice search with language auto-detection — never a single
    hardcoded input language."""

    def __init__(self, settings: Settings):
        self._model_size = settings.WHISPER_MODEL_SIZE

    async def transcribe(self, audio_bytes: bytes, language_hint: str | None = None) -> TranscriptionResult:
        def _run() -> tuple[str, str, float]:
            model = _load_model(self._model_size)
            with tempfile.NamedTemporaryFile(suffix=".wav") as f:
                f.write(audio_bytes)
                f.flush()
                segments, info = model.transcribe(f.name, language=language_hint)
                text = " ".join(seg.text for seg in segments)
            return text.strip(), info.language, float(info.language_probability)

        loop = asyncio.get_running_loop()
        text, language, confidence = await loop.run_in_executor(None, _run)
        return TranscriptionResult(text=text, language=language, confidence=confidence)
