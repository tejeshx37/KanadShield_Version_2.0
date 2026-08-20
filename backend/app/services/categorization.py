import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from app.intelligence.providers.base import LLMProvider
from app.models.enums import DocumentType, ExtractionMethod

# Source connectors whose entire output is unambiguously one document type —
# a GR from the Gujarat GR portal never needs a model call to confirm it's a GR.
_SOURCE_DETERMINISTIC_TYPE: dict[str, DocumentType] = {
    "SOURCE_GUJARAT_GR": DocumentType.GR,
    "SOURCE_EGAZETTE": DocumentType.GAZETTE,
}

# Title/heading regex signals for sources (e.g. India Code) that mix
# multiple document types.
_TITLE_PATTERNS: list[tuple[re.Pattern, DocumentType]] = [
    (re.compile(r"\bAct,?\s*\d{4}\b", re.I), DocumentType.ACT),
    (re.compile(r"\bOrdinance\b", re.I), DocumentType.ORDINANCE),
    (re.compile(r"\bRules?,?\s*\d{4}\b", re.I), DocumentType.RULE),
    (re.compile(r"\bRegulations?\b", re.I), DocumentType.REGULATION),
    (re.compile(r"\bNotification\b", re.I), DocumentType.NOTIFICATION),
    (re.compile(r"\bCircular\b", re.I), DocumentType.CIRCULAR),
    (re.compile(r"\b(vs\.?|versus)\b", re.I), DocumentType.JUDGMENT),
    (re.compile(r"\bScheme\b", re.I), DocumentType.SCHEME),
    (re.compile(r"\bGuidelines?\b", re.I), DocumentType.GUIDELINE),
    (re.compile(r"\bOrder\b", re.I), DocumentType.ORDER),
]


@dataclass
class ClassificationResult:
    document_type: DocumentType
    confidence: float
    method: ExtractionMethod


class _LLMClassification(BaseModel):
    document_type: DocumentType
    confidence: float


_ENUM_VALUES = [t.value for t in DocumentType]


def classify_deterministic(*, source: str, title: str) -> ClassificationResult | None:
    if source in _SOURCE_DETERMINISTIC_TYPE:
        return ClassificationResult(
            document_type=_SOURCE_DETERMINISTIC_TYPE[source], confidence=1.0, method=ExtractionMethod.STRUCTURAL
        )
    for pattern, doc_type in _TITLE_PATTERNS:
        if pattern.search(title):
            return ClassificationResult(document_type=doc_type, confidence=0.9, method=ExtractionMethod.REGEX)
    return None


async def classify_document(*, source: str, title: str, text_excerpt: str, llm: LLMProvider) -> ClassificationResult:
    deterministic = classify_deterministic(source=source, title=title)
    if deterministic is not None:
        return deterministic

    prompt = (
        "Classify this Indian government/legal document into exactly one type from "
        f"{_ENUM_VALUES}. Base your answer only on the text below, never on assumptions.\n\n"
        f"Title: {title}\n\nExcerpt:\n{text_excerpt[:2000]}\n\n"
        'Respond with strict JSON: {"document_type": "<one of the listed types>", "confidence": <0-1 float>}'
    )
    raw = await llm.complete(prompt, temperature=0.0)
    try:
        parsed = _LLMClassification.model_validate(json.loads(raw))
        return ClassificationResult(
            document_type=parsed.document_type, confidence=parsed.confidence, method=ExtractionMethod.LLM
        )
    except (json.JSONDecodeError, ValidationError):
        # Never trust malformed model output — fall back to an honest
        # low-confidence OTHER rather than fabricating a type.
        return ClassificationResult(document_type=DocumentType.OTHER, confidence=0.0, method=ExtractionMethod.UNKNOWN)
