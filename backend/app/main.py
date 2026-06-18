import logging
import sys
from contextlib import asynccontextmanager

import fitz
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from minio.error import S3Error
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_storage, init_storage

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_storage()
    yield


app = FastAPI(
    title="Aambridge HR Platform API",
    version="1.0",
    lifespan=lifespan,
)

PREVIEW_SNIPPET_LENGTH = 300
PARSING_ENGINE_BORDER = "--- [AI PARSING ENGINE] ---"


def log_extracted_text(raw_text: str) -> None:
    """Log extracted CV text without crashing on Windows console encoding."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    safe_text = raw_text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    print(PARSING_ENGINE_BORDER)
    print(safe_text)
    print(PARSING_ENGINE_BORDER)
    logger.info("Extracted %d characters", len(raw_text))


@app.get("/")
def health():
    return {"status": "running"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "running", "database": "connected"}


@app.get("/health/storage")
def health_storage():
    storage = get_storage()
    storage.client.bucket_exists(storage.bucket)
    return {"status": "running", "storage": "connected", "bucket": storage.bucket}


@app.get("/test-upload", response_class=HTMLResponse)
def test_upload_page() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Aambridge CV Dropbox</title>
  <style>
    :root {
      --purple-deep: #4c1d95;
      --purple-mid: #7c3aed;
      --cyan: #06b6d4;
      --sky: #38bdf8;
      --bg: #0f172a;
      --surface: #1e293b;
      --text: #f1f5f9;
      --muted: #94a3b8;
      --border: #334155;
      --success: #22c55e;
      --error: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: linear-gradient(145deg, var(--bg) 0%, #1a1033 50%, #0c1929 100%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }
    .card {
      width: 100%;
      max-width: 640px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 2.5rem;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    .logo {
      text-align: center;
      font-size: 2.25rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 0.5rem;
    }
    .logo .aa { color: var(--purple-mid); }
    .logo .arrows { color: var(--cyan); font-size: 0.85em; }
    .logo .bridge { color: var(--sky); }
    .subtitle {
      text-align: center;
      color: var(--muted);
      font-size: 0.95rem;
      margin-bottom: 2rem;
    }
    .dropzone {
      border: 2px dashed var(--border);
      border-radius: 12px;
      padding: 2.5rem 1.5rem;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.2s, background 0.2s;
      background: rgba(15, 23, 42, 0.5);
    }
    .dropzone:hover, .dropzone.dragover {
      border-color: var(--cyan);
      background: rgba(6, 182, 212, 0.08);
    }
    .dropzone-icon {
      font-size: 2.5rem;
      margin-bottom: 0.75rem;
      opacity: 0.7;
    }
    .dropzone p { color: var(--muted); font-size: 0.9rem; }
    .dropzone strong { color: var(--sky); }
    #file-input { display: none; }
    .file-name {
      margin-top: 1rem;
      font-size: 0.85rem;
      color: var(--cyan);
      min-height: 1.25rem;
    }
    .submit-btn {
      width: 100%;
      margin-top: 1.5rem;
      padding: 0.9rem 1.5rem;
      font-size: 1rem;
      font-weight: 600;
      color: #fff;
      background: linear-gradient(135deg, var(--purple-mid), var(--cyan));
      border: none;
      border-radius: 10px;
      cursor: pointer;
      transition: opacity 0.2s, transform 0.1s;
    }
    .submit-btn:hover:not(:disabled) { opacity: 0.92; }
    .submit-btn:active:not(:disabled) { transform: scale(0.99); }
    .submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }
    #result {
      margin-top: 1.5rem;
      padding: 1.25rem;
      border-radius: 10px;
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border);
      display: none;
      font-size: 0.875rem;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }
    #result.visible { display: block; }
    #result.success { border-color: var(--success); }
    #result.error { border-color: var(--error); color: #fca5a5; }
    .spinner {
      display: inline-block;
      width: 1rem;
      height: 1rem;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      vertical-align: middle;
      margin-right: 0.5rem;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">
      <span class="aa">Aa</span><span class="arrows">▲▼</span><span class="bridge">bridge</span>
    </div>
    <p class="subtitle">Local CV Dropbox — upload a PDF résumé to extract candidate text</p>

    <form id="upload-form">
      <div class="dropzone" id="dropzone">
        <div class="dropzone-icon">📄</div>
        <p>Drag &amp; drop your <strong>.pdf</strong> here</p>
        <p style="margin-top:0.4rem">or click to browse</p>
        <input type="file" id="file-input" accept=".pdf,application/pdf" />
        <div class="file-name" id="file-name"></div>
      </div>
      <button type="submit" class="submit-btn" id="submit-btn" disabled>
        Extract Candidate Info
      </button>
    </form>

    <div id="result"></div>
  </div>

  <script>
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");
    const fileNameEl = document.getElementById("file-name");
    const submitBtn = document.getElementById("submit-btn");
    const form = document.getElementById("upload-form");
    const resultEl = document.getElementById("result");

    let selectedFile = null;

    function setFile(file) {
      if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
        showResult("Please select a valid PDF file.", true);
        return;
      }
      selectedFile = file;
      fileNameEl.textContent = file.name;
      submitBtn.disabled = false;
      resultEl.className = "";
    }

    function clearSelection() {
      selectedFile = null;
      fileInput.value = "";
      fileNameEl.textContent = "";
      submitBtn.disabled = true;
    }

    dropzone.addEventListener("click", () => {
      fileInput.value = "";
      fileInput.click();
    });
    fileInput.addEventListener("change", (e) => setFile(e.target.files[0]));

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      setFile(e.dataTransfer.files[0]);
    });

    function showResult(content, isError) {
      resultEl.textContent = content;
      resultEl.className = isError ? "visible error" : "visible success";
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!selectedFile) return;

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span>Extracting…';

      const formData = new FormData();
      formData.append("file", selectedFile);

      try {
        const response = await fetch("/api/v1/candidates/upload", {
          method: "POST",
          body: formData,
        });

        let data;
        const responseText = await response.text();
        try {
          data = JSON.parse(responseText);
        } catch {
          showResult(
            "Server error (" + response.status + "): " +
            (responseText || "Unknown error. Check the Uvicorn terminal."),
            true
          );
          return;
        }

        if (!response.ok) {
          showResult(
            typeof data.detail === "string"
              ? data.detail
              : JSON.stringify(data.detail || data, null, 2),
            true
          );
        } else {
          showResult(
            "Filename: " + data.filename + "\\n" +
            "Status: " + data.status + "\\n" +
            "Characters extracted: " + data.total_characters + "\\n" +
            "Stored in MinIO: " + data.storage_uri + "\\n\\n" +
            "Preview:\\n" + data.text_preview + "\\n\\n" +
            "Ready for next CV — drop or select another PDF.",
            false
          );
          clearSelection();
        }
      } catch (err) {
        showResult("Network error: " + err.message, true);
      } finally {
        submitBtn.textContent = "Extract Candidate Info";
        if (selectedFile) {
          submitBtn.disabled = false;
        }
      }
    });
  </script>
</body>
</html>"""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Read PDF bytes from memory and concatenate text from every page."""
    text_parts: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        for page in document:
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()


@app.post("/api/v1/candidates/upload")
async def upload_candidate_cv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # --- Step 0: Persist PDF to MinIO for later processing ---
    try:
        storage_info = get_storage().upload_cv(pdf_bytes, file.filename)
    except S3Error as exc:
        logger.exception("MinIO upload failed for %s", file.filename)
        raise HTTPException(status_code=503, detail=f"Could not store CV: {exc}") from exc

    # --- Step 1: PyMuPDF raw text extraction (current milestone) ---
    try:
        raw_text = extract_text_from_pdf(pdf_bytes)
    except Exception as exc:
        logger.exception("PDF extraction failed for %s", file.filename)
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {exc}") from exc

    log_extracted_text(raw_text)
    logger.info("Source file: %s", file.filename)

    # --- Milestone A: LLM structured parsing ---
    # Send raw_text to an LLM (Gemini / Llama) and map the response to our
    # Candidate schema fields (first_name, last_name, email, skills, etc.).
    # parsed_candidate: dict = await llm_parse_candidate(raw_text)

    # --- Milestone B: Persist to PostgreSQL ---
    # Inject get_db, build a Candidate ORM instance from parsed_candidate, and
    # commit via SQLAlchemy session (skills, education, work_experience tables).
    # def save_candidate(parsed_candidate: dict, db: Session = Depends(get_db)) -> Candidate:
    #     ...

    preview = raw_text[:PREVIEW_SNIPPET_LENGTH]
    if len(raw_text) > PREVIEW_SNIPPET_LENGTH:
        preview += "…"

    return {
        "filename": file.filename,
        "status": "extracted",
        "total_characters": len(raw_text),
        "text_preview": preview,
        "bucket": storage_info["bucket"],
        "object_key": storage_info["object_key"],
        "storage_uri": storage_info["storage_uri"],
    }
