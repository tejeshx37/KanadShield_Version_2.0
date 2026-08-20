import hashlib
import json

import pytest

from app.core.config import get_settings
from app.intelligence.providers.base import LLMProvider
from app.models.document import Document
from app.models.enums import DocumentType, Jurisdiction
from app.services.language_detection import detect_language
from app.services.offline_bundle_service import build_offline_bundle
from app.services.translation_service import get_or_create_translation


class _FakeTranslatingLLM(LLMProvider):
    @property
    def model_name(self):
        return "fake-translator"

    async def complete(self, prompt, *, system=None, json_schema=None, max_tokens=None, temperature=0.1):
        if "translate" in prompt.lower():
            return "[translated] " + prompt.split("\n\n", 1)[-1]
        return json.dumps({"summary": "s", "key_provisions": [], "eligibility": [], "conditions": [], "dates": [], "limitations": []})


class _FakeEmbeddings:
    model_name = "fake"

    def __init__(self, dim):
        self.dimensions = dim

    async def embed(self, texts):
        return [[0.1] * self.dimensions for _ in texts]


def test_language_detection_distinguishes_english_gujarati_hindi():
    settings = get_settings()
    en = detect_language("This is an Act of the Government of India regarding pensions.", settings)
    gu = detect_language("આ સરકારનો ઠરાવ પેન્શન અંગે છે.", settings)
    hi = detect_language("यह सरकार का पेंशन के संबंध में संकल्प है।", settings)
    assert en.language == "en"
    assert gu.language == "gu"
    assert hi.language == "hi"


def test_language_detection_flags_mixed_language_documents():
    settings = get_settings()
    mixed = "This GR sanctions pension benefits. આ ઠરાવ પેન્શન લાભો મંજૂર કરે છે."
    result = detect_language(mixed, settings)
    assert result.is_mixed is True


@pytest.mark.asyncio
async def test_translation_is_cached_and_never_overwrites_original(db_session):
    text = "Original eligibility text in English."
    doc = Document(
        source="test_source",
        source_document_id="TRANSLATE-1",
        title="Test Doc",
        document_type=DocumentType.GR,
        jurisdiction=Jurisdiction.STATE,
        source_language="en",
        extracted_text=text,
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    llm = _FakeTranslatingLLM()
    translation = await get_or_create_translation(db_session, llm, doc, "gu")
    await db_session.commit()

    assert translation.translated_text.startswith("[translated]")
    assert doc.extracted_text == text  # original never overwritten

    # Second call must hit the cache, not call the LLM again.
    cached = await get_or_create_translation(db_session, llm, doc, "gu")
    assert cached.id == translation.id


@pytest.mark.asyncio
async def test_offline_bundle_includes_document_and_best_effort_summary(db_session):
    text = "Eligibility: retired workers with 10 years of service."
    doc = Document(
        source="test_source",
        source_document_id="BUNDLE-1",
        title="Bundle Test Doc",
        document_type=DocumentType.GR,
        jurisdiction=Jurisdiction.STATE,
        source_language="en",
        extracted_text=text,
        subject=text,
        source_url="https://example.test/doc",
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    settings = get_settings()
    bundle = await build_offline_bundle(db_session, settings, _FakeTranslatingLLM(), _FakeEmbeddings(settings.EMBEDDING_DIMENSIONS), [doc.id])

    assert len(bundle["items"]) == 1
    item = bundle["items"][0]
    assert item["document"]["title"] == "Bundle Test Doc"
    assert item["document"]["extracted_text"] == text
    # No indexed chunks were seeded for this document, so summarization
    # honestly returns no summary rather than fabricating one.
    assert item["summary"] is None
