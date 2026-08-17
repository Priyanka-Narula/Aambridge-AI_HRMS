import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes import (
    attendance,
    auth,
    candidates,
    clients,
    cv,
    dashboard,
    job_requirements,
    pipeline,
    submissions,
    users,
)
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.deps import get_current_user
from app.core.storage import get_storage, init_storage
from app.services.auth_service import ensure_bootstrap_owner

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    from app.services.dashboard_events import set_event_loop

    set_event_loop(asyncio.get_running_loop())
    init_storage()
    db = SessionLocal()
    try:
        try:
            ensure_bootstrap_owner(db)
        except Exception:
            logger.exception("DB bootstrap skipped (database unavailable)")
    finally:
        db.close()
    yield

app = FastAPI(
    title="Aambridge HR Platform API",
    version="1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.get("/")
def health():
    return {"status": "running"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "running", "database": "connected"}


@app.get("/health/storage")
def health_storage():
    try:
        storage = get_storage()
        storage.client.bucket_exists(storage.bucket)
        return {"status": "running", "storage": "connected", "bucket": storage.bucket}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"MinIO unavailable at {settings.MINIO_ENDPOINT}: {exc}",
        ) from exc


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


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(job_requirements.router)
app.include_router(attendance.router, dependencies=[Depends(get_current_user)])
app.include_router(cv.router, dependencies=[Depends(get_current_user)])
app.include_router(candidates.router, dependencies=[Depends(get_current_user)])
app.include_router(submissions.router)
app.include_router(pipeline.router)
app.include_router(dashboard.router)
