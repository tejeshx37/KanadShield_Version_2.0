"""SourceConnector interface. Every ingestion source (India Code, eGazette,
Gujarat GR portal, court judgment platforms, ...) implements this one
interface — the pipeline never contains source-specific branching."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class RawContentFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"


@dataclass
class SourceDocumentRef:
    """A lightweight listing entry — enough to decide whether to fetch."""

    source_document_id: str
    source_url: str
    title: str | None = None
    last_modified_hint: str | None = None


@dataclass
class FetchedDocument:
    source_document_id: str
    source_url: str
    title: str
    raw_bytes: bytes
    content_format: RawContentFormat
    extra_metadata: dict = field(default_factory=dict)


class SourceConnector(ABC):
    """One connector per source. `source_name` must match the `source`
    column value used across `Document.source` for natural-key upserts."""

    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    async def list_documents(self, *, since: str | None = None) -> list[SourceDocumentRef]:
        """Enumerate documents available at the source, optionally only
        those changed since a watermark (connector-defined format)."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_document(self, ref: SourceDocumentRef) -> FetchedDocument:
        raise NotImplementedError
