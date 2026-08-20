from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.providers.base import LLMProvider
from app.models.document import Document, DocumentTranslation

_PROMPT_TEMPLATE = (
    "Translate the following legal/government document text into {language_name}. "
    "Preserve legal meaning precisely — do not summarize, omit, or add content. "
    "Return only the translated text, no commentary.\n\n{text}"
)

_LANGUAGE_NAMES = {"en": "English", "gu": "Gujarati", "hi": "Hindi"}


async def get_or_create_translation(
    db: AsyncSession, llm: LLMProvider, document: Document, language: str
) -> DocumentTranslation:
    """Translations are generated on demand and cached — never a live
    blocking call for a document that's already been translated. The
    original extracted_text is never overwritten; both coexist."""
    stmt = select(DocumentTranslation).where(
        DocumentTranslation.document_id == document.id, DocumentTranslation.language == language
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing

    if not document.extracted_text:
        raise ValueError("Document has no extracted text to translate")

    language_name = _LANGUAGE_NAMES.get(language, language)
    prompt = _PROMPT_TEMPLATE.format(language_name=language_name, text=document.extracted_text[:8000])
    translated_text = await llm.complete(prompt, temperature=0.0)

    translation = DocumentTranslation(
        document_id=document.id,
        language=language,
        translated_text=translated_text,
        generated_by=llm.model_name,
        confidence=None,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(translation)
    await db.flush()
    return translation
