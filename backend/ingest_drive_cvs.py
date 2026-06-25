"""
Download CVs from a public Google Drive folder, parse via the backend API,
and print a summary. Parsed candidates are NOT auto-saved — verify them in the
frontend at /candidates/verify after uploading individual files, or set
AUTO_APPROVE=true to skip verification.

Usage (from backend/ with venv activated, while uvicorn is running):
    python ingest_drive_cvs.py
"""

import os
import sys
import tempfile
from pathlib import Path

import gdown
import requests

DRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/1LW-rfMZL0oLRtTLsPgF--C6Mdjp8wmLm"
)
UPLOAD_ENDPOINT = "http://127.0.0.1:8000/api/v1/candidates/upload"
AUTO_APPROVE = os.getenv("AUTO_APPROVE", "false").lower() in ("1", "true", "yes")
UPLOAD_TIMEOUT = int(os.getenv("UPLOAD_TIMEOUT", "180"))


def download_folder(dest: Path) -> list[Path]:
    print("Downloading CVs from Google Drive folder...")
    gdown.download_folder(
        url=DRIVE_FOLDER_URL,
        output=str(dest),
        quiet=False,
        use_cookies=False,
    )
    pdfs = sorted(dest.glob("*.pdf"))
    print(f"\nFound {len(pdfs)} PDF(s): {[p.name for p in pdfs]}\n")
    return pdfs


def upload_cv(pdf_path: Path) -> tuple[dict, int]:
    with pdf_path.open("rb") as f:
        response = requests.post(
            UPLOAD_ENDPOINT,
            files={"file": (pdf_path.name, f, "application/pdf")},
            params={
                "auto_approve": str(AUTO_APPROVE).lower(),
                "created_by": "drive-ingestion-script",
            },
            timeout=UPLOAD_TIMEOUT,
        )
    if response.status_code >= 400:
        try:
            return response.json(), response.status_code
        except ValueError:
            return {"detail": response.text}, response.status_code
    return response.json(), response.status_code


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        try:
            pdfs = download_folder(tmp_path)
        except Exception as exc:
            print(f"ERROR: Failed to download from Google Drive: {exc}")
            sys.exit(1)

        if not pdfs:
            print("No PDF files found in the Drive folder.")
            sys.exit(0)

        print(f"Uploading {len(pdfs)} CV(s) to backend (auto_approve={AUTO_APPROVE})...\n")
        results = []
        for pdf in pdfs:
            print(f"  Processing: {pdf.name}")
            try:
                data, status_code = upload_cv(pdf)
            except requests.ConnectionError:
                print("    ERROR: Cannot reach backend. Is uvicorn running?")
                sys.exit(1)
            except requests.ReadTimeout:
                print(f"    ERROR: Timed out after {UPLOAD_TIMEOUT}s (LLM parsing can be slow).")
                results.append({"file": pdf.name, "status": "timeout"})
                continue

            status = data.get("status", "unknown")
            parsing = data.get("parsing_method", "—")
            candidate_id = data.get("saved_candidate_id", "—")
            errors = data.get("validation_errors", [])
            message = data.get("message", data.get("detail", ""))

            print(f"    HTTP {status_code} | status={status} | parser={parsing} | id={candidate_id}")
            if errors:
                print(f"    Validation errors: {errors}")
            if message and status not in ("already_exists", "approved_and_saved", "parsed"):
                print(f"    Detail: {message}")
            if status == "parsed" and not AUTO_APPROVE:
                print("    → Review in frontend: /candidates/verify")

            results.append(
                {"file": pdf.name, "status": status, "candidate_id": candidate_id}
            )

        saved = [r for r in results if r["status"] == "approved_and_saved"]
        parsed = [r for r in results if r["status"] == "parsed"]
        duplicates = [r for r in results if r["status"] == "already_exists"]
        failed = [
            r
            for r in results
            if r["status"]
            not in ("approved_and_saved", "already_exists", "parsed")
        ]

        print("\n" + "=" * 50)
        print(
            f"SUMMARY  —  Saved: {len(saved)}  |  Parsed (pending review): {len(parsed)}  "
            f"|  Duplicates: {len(duplicates)}  |  Failed: {len(failed)}"
        )
        print("=" * 50)


if __name__ == "__main__":
    main()
