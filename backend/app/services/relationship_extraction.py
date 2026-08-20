import re
from dataclasses import dataclass

from app.models.enums import RelationshipType

# Deterministic structural signals for the relationship types that show up
# in predictable legal phrasing. Ambiguous cross-references still need a
# human/LLM review pass — this extracts the confident, common cases.
_PATTERNS: list[tuple[re.Pattern, RelationshipType, float]] = [
    (re.compile(r"(?i)\bamends?\b.{0,120}?\b([A-Z][A-Za-z,\.\s]{5,120}?\bAct,?\s*\d{4})"), RelationshipType.AMENDS, 0.75),
    (re.compile(r"(?i)\brepeals?\b.{0,120}?\b([A-Z][A-Za-z,\.\s]{5,120}?\bAct,?\s*\d{4})"), RelationshipType.REPEALS, 0.75),
    (re.compile(r"(?i)\bsupersedes?\b.{0,120}?\b([A-Z][A-Za-z0-9,\.\/\s]{5,120}?(?:GR|Order|Notification)[\s\S]{0,40})"), RelationshipType.SUPERSEDES, 0.6),
    (
        re.compile(r"(?i)in exercise of the powers conferred (?:by|under)\s+(section\s+\d+[A-Za-z]?\s+of\s+the\s+[A-Z][A-Za-z,\.\s]{5,120}?\bAct,?\s*\d{4})"),
        RelationshipType.IMPLEMENTS,
        0.8,
    ),
    (re.compile(r"(?i)\bissued by\b.{0,80}?\b([A-Z][A-Za-z&,.\s]{5,80}?\bDepartment)"), RelationshipType.ISSUED_BY, 0.7),
    # Common Indian law citation formats: "AIR 2020 SC 123", "(2020) 5 SCC 100"
    (re.compile(r"\b(AIR\s+\d{4}\s+[A-Z]{2,5}\s+\d+)\b"), RelationshipType.CITES, 0.85),
    (re.compile(r"\((\d{4})\)\s*\d+\s*SCC\s*\d+"), RelationshipType.CITES, 0.85),
]


@dataclass
class ExtractedRelationship:
    relationship_type: RelationshipType
    target_text: str
    confidence: float
    evidence_text: str


def extract_relationships(text: str, *, max_per_type: int = 10) -> list[ExtractedRelationship]:
    """Real, deterministic extraction from document text — never a
    placeholder graph. Ambiguous references simply aren't extracted here
    rather than being guessed."""
    results: list[ExtractedRelationship] = []
    counts: dict[RelationshipType, int] = {}

    for pattern, rel_type, confidence in _PATTERNS:
        for match in pattern.finditer(text):
            if counts.get(rel_type, 0) >= max_per_type:
                break
            target = match.group(1).strip() if match.groups() else match.group(0).strip()
            evidence_start = max(0, match.start() - 60)
            evidence_end = min(len(text), match.end() + 60)
            results.append(
                ExtractedRelationship(
                    relationship_type=rel_type,
                    target_text=target,
                    confidence=confidence,
                    evidence_text=text[evidence_start:evidence_end].strip(),
                )
            )
            counts[rel_type] = counts.get(rel_type, 0) + 1
    return results
