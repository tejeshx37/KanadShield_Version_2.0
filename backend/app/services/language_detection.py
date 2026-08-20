from dataclasses import dataclass

from langdetect import DetectorFactory, detect_langs

from app.core.config import Settings

DetectorFactory.seed = 0  # deterministic detection


@dataclass
class LanguageDetectionResult:
    language: str
    confidence: float
    is_mixed: bool


# Gujarati and Devanagari Unicode blocks — used to flag genuine
# code-switched documents that a single-language detector call would
# otherwise force into one bucket.
_GUJARATI_RANGE = (0x0A80, 0x0AFF)
_DEVANAGARI_RANGE = (0x0900, 0x097F)
_LATIN_RANGE = (0x0041, 0x024F)


def _script_ratios(text: str) -> dict[str, float]:
    counts = {"gu": 0, "hi": 0, "en": 0}
    total = 0
    for ch in text:
        code = ord(ch)
        if _GUJARATI_RANGE[0] <= code <= _GUJARATI_RANGE[1]:
            counts["gu"] += 1
            total += 1
        elif _DEVANAGARI_RANGE[0] <= code <= _DEVANAGARI_RANGE[1]:
            counts["hi"] += 1
            total += 1
        elif _LATIN_RANGE[0] <= code <= _LATIN_RANGE[1] and ch.isalpha():
            counts["en"] += 1
            total += 1
    if total == 0:
        return {k: 0.0 for k in counts}
    return {k: v / total for k, v in counts.items()}


def detect_language(text: str, settings: Settings) -> LanguageDetectionResult:
    """Detects source language from content — never guessed from department
    or filename. Flags mixed-language (common in real Gujarati/English
    GRs) via script-ratio analysis rather than forcing a single label."""
    sample = text[:5000].strip()
    if not sample:
        return LanguageDetectionResult(language=settings.DEFAULT_LANGUAGE, confidence=0.0, is_mixed=False)

    ratios = _script_ratios(sample)
    present_scripts = [lang for lang, r in ratios.items() if r > 0.1]
    is_mixed = len(present_scripts) > 1

    try:
        candidates = detect_langs(sample)
        top = candidates[0]
        language = top.lang if top.lang in settings.supported_languages else settings.DEFAULT_LANGUAGE
        confidence = float(top.prob)
    except Exception:
        # langdetect can raise LangDetectException on very short/ambiguous
        # text — fall back to script-ratio detection rather than crashing.
        if present_scripts:
            language = max(ratios, key=ratios.get)
            confidence = ratios[language]
        else:
            language = settings.DEFAULT_LANGUAGE
            confidence = 0.0

    return LanguageDetectionResult(language=language, confidence=confidence, is_mixed=is_mixed)
