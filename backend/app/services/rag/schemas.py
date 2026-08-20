from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    document_id: str
    page: int | None = None
    section: str | None = None
    source_url: str | None = None


class DocumentSummary(BaseModel):
    summary: str
    key_provisions: list[str] = Field(default_factory=list)
    eligibility: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)


class AskAnswer(BaseModel):
    answer: str
    citations: list[SourceReference] = Field(default_factory=list)
    insufficient_evidence: bool = False
