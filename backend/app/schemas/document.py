import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import DocumentType, Jurisdiction


class DocumentSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    title: str
    document_type: DocumentType
    jurisdiction: Jurisdiction
    state: str | None
    source_language: str
    date: date | None
    year: int | None
    subject: str | None
    source_url: str | None
    text_available: bool
    classification_confidence: float | None


class DocumentDetailSchema(DocumentSummarySchema):
    case_number: str | None
    act_number: str | None
    keywords: list[str] | None
    pdf_path: str | None
    date_confidence: float | None
    doc_metadata: dict = {}
    created_at: datetime
    updated_at: datetime


class PaginatedDocuments(BaseModel):
    items: list[DocumentSummarySchema]
    total: int
    page: int
    page_size: int
