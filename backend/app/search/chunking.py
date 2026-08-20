import re
from dataclasses import dataclass

from app.core.config import Settings
from app.models.enums import ChunkType, DocumentType

_SECTION_HEADER = re.compile(r"(?im)^\s*(\d+[A-Z]?)\.\s+([^\n]{0,150})$")

_JUDGMENT_SECTION_MARKERS: list[tuple[re.Pattern, ChunkType]] = [
    (re.compile(r"(?i)\b(facts of the case|brief facts|background)\b"), ChunkType.FACTS),
    (re.compile(r"(?i)\b(issues? for consideration|questions? of law)\b"), ChunkType.ISSUES),
    (re.compile(r"(?i)\b(analysis|discussion|reasoning|findings)\b"), ChunkType.ANALYSIS),
    (re.compile(r"(?i)\b(order|decision|conclusion|held)\b"), ChunkType.DECISION),
]

_GR_SECTION_MARKERS: list[tuple[re.Pattern, ChunkType]] = [
    (re.compile(r"(?i)\bsubject\b"), ChunkType.SUBJECT),
    (re.compile(r"(?i)\b(eligibility|eligible)\b"), ChunkType.ELIGIBILITY),
    (re.compile(r"(?i)\b(condition|terms)\b"), ChunkType.CONDITIONS),
    (re.compile(r"(?i)\b(provision|resolution)\b"), ChunkType.PROVISIONS),
]


@dataclass
class TextChunk:
    text: str
    chunk_type: ChunkType
    section_ref: str | None
    page: int | None = None


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)  # rough heuristic, avoids a tokenizer dependency for chunk sizing


def _split_by_markers(text: str, markers: list[tuple[re.Pattern, ChunkType]]) -> list[TextChunk]:
    hits: list[tuple[int, ChunkType]] = []
    for pattern, chunk_type in markers:
        m = pattern.search(text)
        if m:
            hits.append((m.start(), chunk_type))
    if not hits:
        return []
    hits.sort()
    chunks: list[TextChunk] = []
    for i, (start, chunk_type) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else len(text)
        segment = text[start:end].strip()
        if segment:
            chunks.append(TextChunk(text=segment, chunk_type=chunk_type, section_ref=None))
    return chunks


def _fallback_fixed_chunks(text: str, settings: Settings, chunk_type: ChunkType) -> list[TextChunk]:
    """Last resort only — used when no structural signal is found at all,
    never the default for legal documents that do have real structure."""
    target_chars = settings.RAG_CHUNK_TARGET_TOKENS * 4
    overlap_chars = settings.RAG_CHUNK_OVERLAP_TOKENS * 4
    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = min(start + target_chars, len(text))
        segment = text[start:end].strip()
        if segment:
            chunks.append(TextChunk(text=segment, chunk_type=chunk_type, section_ref=None))
        if end == len(text):
            break
        start = end - overlap_chars
    return chunks


def chunk_act_text(sections: list[tuple[str, str, str | None]]) -> list[TextChunk]:
    """sections: list of (section_number, text, heading). Acts are always
    split by their real section boundaries, never blind fixed-char split."""
    return [
        TextChunk(text=text, chunk_type=ChunkType.SECTION, section_ref=number)
        for number, text, _heading in sections
        if text.strip()
    ]


def chunk_document_text(*, document_type: DocumentType, text: str, settings: Settings) -> list[TextChunk]:
    if document_type == DocumentType.JUDGMENT:
        chunks = _split_by_markers(text, _JUDGMENT_SECTION_MARKERS)
        if chunks:
            return chunks
    if document_type in {DocumentType.GR, DocumentType.SCHEME, DocumentType.NOTIFICATION, DocumentType.CIRCULAR}:
        chunks = _split_by_markers(text, _GR_SECTION_MARKERS)
        if chunks:
            return chunks
    if document_type in {DocumentType.ACT, DocumentType.STATUTE, DocumentType.RULE, DocumentType.REGULATION}:
        matches = list(_SECTION_HEADER.finditer(text))
        if matches:
            chunks = []
            for i, m in enumerate(matches):
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                segment = text[m.start():end].strip()
                if segment:
                    chunks.append(TextChunk(text=segment, chunk_type=ChunkType.SECTION, section_ref=m.group(1)))
            return chunks

    return _fallback_fixed_chunks(text, settings, ChunkType.GENERIC)
