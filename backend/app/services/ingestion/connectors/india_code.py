from bs4 import BeautifulSoup

from app.core.config import Settings
from app.services.ingestion.base import (
    FetchedDocument,
    RawContentFormat,
    SourceConnector,
    SourceDocumentRef,
)
from app.services.ingestion.http_client import RetryingHTTPClient


class IndiaCodeConnector(SourceConnector):
    """Connector for indiacode.nic.in — the central government's repository
    of Acts. Listing/detail page structure is documented against the
    public site's HTML; NOT live-verified in this sandbox because outbound
    access to *.nic.in is blocked by this environment's network policy
    (see docs/CONNECTOR_STATUS.md). Uses the real, publicly documented
    search-by-handle listing pages, not an invented API."""

    def __init__(self, settings: Settings, http: RetryingHTTPClient | None = None):
        self._base_url = settings.SOURCE_INDIA_CODE_BASE_URL.rstrip("/")
        self._http = http or RetryingHTTPClient(settings)

    @property
    def source_name(self) -> str:
        return "SOURCE_INDIA_CODE"

    async def list_documents(self, *, since: str | None = None) -> list[SourceDocumentRef]:
        resp = await self._http.get(f"{self._base_url}/handle/123456789/1362/simple-search")
        soup = BeautifulSoup(resp.text, "lxml")
        refs: list[SourceDocumentRef] = []
        for anchor in soup.select("a[href*='/handle/']"):
            href = anchor.get("href", "")
            if "/handle/123456789/" not in href or href.rstrip("/").endswith("/1362"):
                continue
            handle_id = href.rstrip("/").rsplit("/", 1)[-1]
            title = anchor.get_text(strip=True)
            if not handle_id or not title:
                continue
            refs.append(
                SourceDocumentRef(
                    source_document_id=handle_id,
                    source_url=f"{self._base_url}{href}",
                    title=title,
                )
            )
        return refs

    async def fetch_document(self, ref: SourceDocumentRef) -> FetchedDocument:
        detail_resp = await self._http.get(ref.source_url)
        soup = BeautifulSoup(detail_resp.text, "lxml")
        pdf_link = soup.select_one("a[href$='.pdf']")
        title = ref.title or (soup.select_one("h1, .page-header") and soup.select_one("h1, .page-header").get_text(strip=True)) or ref.source_document_id

        if pdf_link is not None:
            pdf_url = pdf_link.get("href", "")
            if not pdf_url.startswith("http"):
                pdf_url = f"{self._base_url}{pdf_url}"
            pdf_resp = await self._http.get(pdf_url)
            return FetchedDocument(
                source_document_id=ref.source_document_id,
                source_url=ref.source_url,
                title=title,
                raw_bytes=pdf_resp.content,
                content_format=RawContentFormat.PDF,
            )

        return FetchedDocument(
            source_document_id=ref.source_document_id,
            source_url=ref.source_url,
            title=title,
            raw_bytes=detail_resp.content,
            content_format=RawContentFormat.HTML,
        )
