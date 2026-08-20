import re
from dataclasses import dataclass
from datetime import date, datetime

from app.models.enums import ExtractionMethod, Jurisdiction

_MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December"
)

_DATE_PATTERNS: list[tuple[re.Pattern, str, float]] = [
    # "15th March, 2021" / "15 March 2021"
    (re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTHS})[,.]?\s+(\d{{4}})\b", re.I), "%d %B %Y", 0.85),
    # "dated 15/03/2021" or "15-03-2021"
    (re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"), "%d/%m/%Y", 0.6),
    # ISO "2021-03-15"
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), "%Y-%m-%d", 0.75),
]

# Common Gujarat/Central department name fragments — extend via config/DB
# lookup against the departments table in production; this is the
# structural first pass before falling back to a lower-confidence guess.
_DEPARTMENT_HINT_PATTERN = re.compile(
    r"([A-Z][A-Za-z&,.\s]{2,60}?)\s+Department\b", re.I
)

_STOPWORDS = frozenset(
    "the a an of to in and for on by with is are was were shall be this that as it "
    "or from at government gujarat india rules act section notification order".split()
)


@dataclass
class DateExtraction:
    value: date | None
    confidence: float
    method: ExtractionMethod


@dataclass
class DepartmentExtraction:
    name: str | None
    confidence: float


def extract_date(text: str) -> DateExtraction:
    """Date parsing from scanned government documents is genuinely
    unreliable — every result carries an honest confidence and method
    rather than presenting a guess as certain."""
    for pattern, fmt, base_confidence in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        raw = match.group(0)
        try:
            if fmt == "%d %B %Y":
                normalized = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                parsed = datetime.strptime(normalized, "%d %B %Y").date()
            elif fmt == "%d/%m/%Y":
                parsed = datetime.strptime(f"{match.group(1)}/{match.group(2)}/{match.group(3)}", "%d/%m/%Y").date()
            else:
                parsed = datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
        return DateExtraction(value=parsed, confidence=base_confidence, method=ExtractionMethod.REGEX)
    return DateExtraction(value=None, confidence=0.0, method=ExtractionMethod.UNKNOWN)


def extract_department(text: str) -> DepartmentExtraction:
    match = _DEPARTMENT_HINT_PATTERN.search(text)
    if match:
        name = match.group(1).strip().strip(",")
        return DepartmentExtraction(name=f"{name} Department", confidence=0.7)
    return DepartmentExtraction(name=None, confidence=0.0)


def infer_jurisdiction(*, source: str, department_name: str | None) -> tuple[Jurisdiction, str | None]:
    if source in {"SOURCE_GUJARAT_GR"}:
        return Jurisdiction.STATE, "Gujarat"
    if source in {"SOURCE_INDIA_CODE"}:
        return Jurisdiction.CENTRAL, None
    if department_name and "gujarat" in department_name.lower():
        return Jurisdiction.STATE, "Gujarat"
    return Jurisdiction.CENTRAL, None


def extract_keywords(text: str, *, top_n: int = 12) -> list[str]:
    """Deterministic keyword extraction by term frequency after stopword
    removal — not the full document dumped into a tag field."""
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if w in _STOPWORDS:
            continue
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)
    return [w for w, _ in ranked[:top_n]]
