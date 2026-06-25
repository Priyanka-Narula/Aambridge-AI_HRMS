import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas.cv import CandidateApprovalRequest, CandidateDraft, DriveSyncRequest
from app.core.config import settings
from app.core.database import get_db
from app.services.candidate_service import save_candidate_record, validate_candidate_draft
from app.services.cv_pipeline import apply_auto_approve, process_cv_document

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates-cv"])


@router.post("/upload")
async def upload_candidate_cv(
    file: UploadFile = File(...),
    auto_approve: bool = False,
    created_by: str | None = "upload-ui",
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = await asyncio.to_thread(
        process_cv_document,
        file.filename,
        pdf_bytes,
        "cv-upload",
    )

    if auto_approve:
        result = await asyncio.to_thread(
            apply_auto_approve,
            result,
            db,
            created_by,
            save_candidate_record,
        )

    return result


@router.post("/approve")
def approve_candidate(
    payload: CandidateApprovalRequest,
    db: Session = Depends(get_db),
):
    cleaned, errors = validate_candidate_draft(payload.candidate.model_dump(mode="json"))
    if errors or cleaned is None:
        print(errors)
        raise HTTPException(
            status_code=422,
            detail={"message": "Candidate data failed validation.", "validation_errors": errors},
        )

    candidate = save_candidate_record(
        db=db,
        draft=cleaned,
        created_by=payload.created_by,
    )
    return {
        "status": "saved",
        "candidate_id": str(candidate.id),
        "email": candidate.email,
        "candidate_status": candidate.candidate_status,
    }


@router.post("/drive-sync/process")
async def process_drive_sync(
    request: DriveSyncRequest,
    db: Session = Depends(get_db),
):
    folder_path = request.folder_path or settings.GOOGLE_DRIVE_SYNC_DIR
    if not folder_path:
        raise HTTPException(
            status_code=400,
            detail=(
                "No folder path provided. Set GOOGLE_DRIVE_SYNC_DIR in backend/.env "
                "or pass folder_path in request."
            ),
        )

    source_dir = Path(folder_path)
    if not source_dir.exists() or not source_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Drive sync folder not found: {source_dir}")

    pdf_files = sorted(source_dir.rglob("*.pdf"))[: max(1, min(request.max_files, 200))]
    if not pdf_files:
        return {"status": "no_files_found", "folder_path": str(source_dir), "processed": []}

    processed: list[dict[str, Any]] = []
    for pdf_path in pdf_files:
        result = await asyncio.to_thread(
            process_cv_document,
            pdf_path.name,
            pdf_path.read_bytes(),
            "google-drive-folder",
        )
        if request.auto_approve and not result["validation_errors"]:
            result = await asyncio.to_thread(
                apply_auto_approve,
                result,
                db,
                request.created_by,
                save_candidate_record,
            )
        processed.append(result)

    return {
        "status": "processed",
        "folder_path": str(source_dir),
        "processed_count": len(processed),
        "processed": processed,
    }
