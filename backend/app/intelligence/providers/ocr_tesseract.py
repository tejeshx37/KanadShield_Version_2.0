import asyncio
import io

import pytesseract
from PIL import Image

from app.intelligence.providers.base import OCRProvider, OCRResult

_TESSERACT_LANG_MAP = {"en": "eng", "gu": "guj", "hi": "hin"}


class TesseractOCRProvider(OCRProvider):
    """Multilingual OCR — never assumes English-only scanning. Mixed
    Gujarati/English/Hindi pages are handled by passing tesseract a
    combined language string (e.g. 'guj+eng')."""

    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> OCRResult:
        tess_langs = "+".join(_TESSERACT_LANG_MAP.get(l, "eng") for l in languages) or "eng"

        def _run() -> tuple[str, float]:
            image = Image.open(io.BytesIO(image_bytes))
            data = pytesseract.image_to_data(
                image, lang=tess_langs, output_type=pytesseract.Output.DICT
            )
            words = [w for w in data["text"] if w.strip()]
            confidences = [int(c) for c, w in zip(data["conf"], data["text"]) if w.strip() and c != "-1"]
            text = " ".join(words)
            avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
            return text, avg_conf

        loop = asyncio.get_running_loop()
        text, confidence = await loop.run_in_executor(None, _run)
        primary_lang = languages[0] if languages else "en"
        return OCRResult(text=text, language=primary_lang, confidence=confidence)
