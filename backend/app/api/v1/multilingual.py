import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_db
from app.core.config import Settings
from app.intelligence.factory import get_llm_provider, get_speech_provider
from app.repositories.document_repository import DocumentRepository
from app.services.translation_service import get_or_create_translation

router = APIRouter(tags=["multilingual"])


@router.get("/documents/{document_id}/translations/{language}")
async def get_document_translation(
    document_id: uuid.UUID,
    language: str,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    if language not in settings.supported_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "unsupported_language", "message": f"Language '{language}' is not configured"}},
        )
    document = await DocumentRepository(db).get(document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "Document not found"}},
        )
    try:
        translation = await get_or_create_translation(db, get_llm_provider(), document, language)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "no_source_text", "message": str(exc)}},
        )
    return {
        "language": translation.language,
        "translated_text": translation.translated_text,
        "generated_by": translation.generated_by,
        "generated_at": translation.generated_at,
    }


@router.post("/search/voice")
async def voice_search_transcribe(audio: UploadFile = File(...)):
    """Transcribes voice input with language auto-detection — never a
    single hardcoded input language. The frontend feeds the resulting text
    into the normal /search endpoint."""
    audio_bytes = await audio.read()
    result = await get_speech_provider().transcribe(audio_bytes)
    return {"text": result.text, "detected_language": result.language, "confidence": result.confidence}
