from bs4 import BeautifulSoup

from app.core.config import Settings
from app.services.ingestion.base import (
    FetchedDocument,
    RawContentFormat,
    SourceConnector,
    SourceDocumentRef,
)
from app.services.ingestion.http_client import RetryingHTTPClient


class GujaratGRConnector(SourceConnector):
    """Connector for gr.gujarat.gov.in — Gujarat Government Resolutions
    across departments (Home, GAD, Labour, UDD, ...). Not live-verified in
    this sandbox — outbound access to *.gujarat.gov.in is blocked by this
    environment's network policy (see docs/CONNECTOR_STATUS.md)."""

    def __init__(self, settings: Settings, http: RetryingHTTPClient | None = None):
        self._base_url = settings.SOURCE_GUJARAT_GR_BASE_URL.rstrip("/")
        self._http = http or RetryingHTTPClient(settings)

    @property
    def source_name(self) -> str:
        return "SOURCE_GUJARAT_GR"

    async def list_documents(self, *, since: str | None = None) -> list[SourceDocumentRef]:
        resp = await self._http.get(f"{self._base_url}/Digigr.aspx")
        soup = BeautifulSoup(resp.text, "lxml")
        refs: list[SourceDocumentRef] = []
        for row in soup.select("table.gr-list tr, table#GridView1 tr"):
            link = row.select_one("a[href$='.pdf']")
            if link is None:
                continue
            href = link.get("href", "")
            gr_number_cell = row.select_one("td")
            refs.append(
                SourceDocumentRef(
                    source_document_id=(gr_number_cell.get_text(strip=True) if gr_number_cell else href),
                    source_url=href if href.startswith("http") else f"{self._base_url}/{href.lstrip('/')}",
                    title=row.get_text(strip=True)[:500],
                )
            )
        return refs

    async def fetch_document(self, ref: SourceDocumentRef) -> FetchedDocument:
        resp = await self._http.get(ref.source_url)
        return FetchedDocument(
            source_document_id=ref.source_document_id,
            source_url=ref.source_url,
            title=ref.title or ref.source_document_id,
            raw_bytes=resp.content,
            content_format=RawContentFormat.PDF,
        )
