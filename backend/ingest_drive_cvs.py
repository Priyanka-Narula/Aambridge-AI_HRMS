"""
Download all CVs from a public Google Drive folder and ingest them into the
HRMS candidates table via the existing upload endpoint.

Usage (from backend/ with venv activated, while uvicorn is running):
    python ingest_drive_cvs.py
"""

import sys
import tempfile
from pathlib import Path

import gdown
import requests

DRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/1LW-rfMZL0oLRtTLsPgF--C6Mdjp8wmLm"
)
UPLOAD_ENDPOINT = "http://127.0.0.1:8000/api/v1/candidates/upload"


def download_folder(dest: Path) -> list[Path]:
    print(f"Downloading CVs from Google Drive folder...")
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
            params={"auto_approve": "true", "created_by": "drive-ingestion-script"},
            timeout=60,
        )
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

        print(f"Uploading {len(pdfs)} CV(s) to backend...\n")
        results = []
        for pdf in pdfs:
            print(f"  Processing: {pdf.name}")
            try:
                data, status_code = upload_cv(pdf)
            except requests.ConnectionError:
                print("    ERROR: Cannot reach backend. Is uvicorn running?")
                sys.exit(1)

            status = data.get("status", "unknown")
            candidate_id = data.get("saved_candidate_id", "—")
            errors = data.get("validation_errors", [])
            message = data.get("message", data.get("detail", ""))

            print(f"    HTTP {status_code} | status={status} | candidate_id={candidate_id}")
            if status == "already_exists":
                print(f"    Skipped: {message}")
            if errors:
                print(f"    Validation errors: {errors}")
            if message and status not in ("already_exists", "approved_and_saved"):
                print(f"    Detail: {message}")

            results.append(
                {"file": pdf.name, "status": status, "candidate_id": candidate_id}
            )

        saved = [r for r in results if r["status"] == "approved_and_saved"]
        duplicates = [r for r in results if r["status"] == "already_exists"]
        failed = [r for r in results if r["status"] not in ("approved_and_saved", "already_exists")]

        print("\n" + "=" * 50)
        print(f"SUMMARY  —  Saved: {len(saved)}  |  Duplicates: {len(duplicates)}  |  Failed: {len(failed)}")
        print("=" * 50)
        for r in saved:
            print(f"  + {r['file']:<35} candidate_id = {r['candidate_id']}")
        for r in duplicates:
            print(f"  = {r['file']:<35} already exists — skipped")
        for r in failed:
            print(f"  - {r['file']:<35} status = {r['status']}")


if __name__ == "__main__":
    main()
