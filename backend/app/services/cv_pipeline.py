import logging
from typing import Any

from fastapi import HTTPException
from minio.error import S3Error

from app.api.schemas.cv import CandidateDraft
from app.core.config import settings
from app.core.storage import get_storage
from app.services.candidate_service import validate_candidate_draft
from app.services.llm_parser import parse_candidate_with_llm
from app.services.pdf_extractor import build_text_preview, extract_text_from_pdf
from app.services.regex_parser import parse_candidate_from_text

logger = logging.getLogger(__name__)


def parse_cv_text(raw_text: str, storage_uri: str, source: str) -> tuple[dict[str, Any], str]:
    """Parse extracted CV text. Returns (parsed_data, parsing_method)."""
    if settings.HF_API_TOKEN:
        try:
            parsed = parse_candidate_with_llm(raw_text, storage_uri, source)
            model_used = str(parsed.pop("_llm_model", settings.HF_MODEL) or settings.HF_MODEL)
            return parsed, f"hf:{model_used}"
        except Exception as exc:
            logger.warning("LLM parsing failed, falling back to regex: %s", exc)

    parsed = parse_candidate_from_text(raw_text, storage_uri, source)
    return parsed, "regex_fallback"


def process_cv_document(filename: str, pdf_bytes: bytes, source: str) -> dict[str, Any]:
    try:
        storage_info = get_storage().upload_cv(pdf_bytes, filename)
    except S3Error as exc:
        logger.exception("MinIO upload failed for %s", filename)
        raise HTTPException(status_code=503, detail=f"Could not store CV: {exc}") from exc

    try:
        raw_text = extract_text_from_pdf(pdf_bytes)
    except Exception as exc:
        logger.exception("PDF extraction failed for %s", filename)
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {exc}") from exc

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the PDF.")

    logger.info("Extracted %d characters from %s", len(raw_text), filename)

    parsed_candidate, parsing_method = parse_cv_text(
        raw_text=raw_text,
        storage_uri=storage_info["storage_uri"],
        source=source,
    )
    draft, validation_errors = validate_candidate_draft(parsed_candidate)

    return {
        "filename": filename,
        "status": "parsed" if draft else "validation_failed",
        "parsing_method": parsing_method,
        "total_characters": len(raw_text),
        "text_preview": build_text_preview(raw_text),
        "bucket": storage_info["bucket"],
        "object_key": storage_info["object_key"],
        "storage_uri": storage_info["storage_uri"],
        "candidate_preview": draft.model_dump(mode="json") if draft else parsed_candidate,
        "validation_errors": validation_errors,
    }


def apply_auto_approve(
    result: dict[str, Any],
    db,
    created_by: str | None,
    save_fn,
) -> dict[str, Any]:
    if result["validation_errors"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Candidate data failed validation; approval skipped.",
                "validation_errors": result["validation_errors"],
                "candidate_preview": result["candidate_preview"],
            },
        )
    draft = CandidateDraft(**result["candidate_preview"])
    try:
        saved = save_fn(db=db, draft=draft, created_by=created_by)
        result["saved_candidate_id"] = str(saved.id)
        result["status"] = "approved_and_saved"
    except HTTPException as exc:
        if exc.status_code == 409:
            result["status"] = "already_exists"
            result["message"] = exc.detail
        else:
            raise
    return result
