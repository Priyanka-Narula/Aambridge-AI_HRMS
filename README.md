# Aambridge AI HRMS

A recruitment management system built with FastAPI, Vue 3, PostgreSQL, and MinIO.

---

## Quick Start (Daily Workflow)

Use this every time you sit down to develop. Open **three terminals** from the project root:

**Terminal 1 — Infrastructure**
```powershell
docker compose up -d
```

**Terminal 2 — Backend**
```powershell
cd backend
..\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

**Terminal 3 — Frontend**
```powershell
cd frontend
npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://127.0.0.1:8000 |
| API Docs | http://127.0.0.1:8000/docs |
| MinIO Console | http://localhost:9001 |

When done for the day:
```powershell
docker compose down
```

> **Note:** Docker containers are set to `restart: "no"` — they will not start automatically on boot. Always run `docker compose up -d` before starting the backend.

---

## Prerequisites

Install the following before setup:

| Tool | Version | Purpose |
|------|---------|---------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Latest | PostgreSQL and MinIO via Docker Compose |
| [Python](https://www.python.org/downloads/) | 3.11+ | Backend API |
| [Node.js](https://nodejs.org/) | >= 22.12.0 | Frontend (see `frontend/package.json`) |
| [Git](https://git-scm.com/) | Latest | Clone and manage the repo |

Verify installations:

```bash
docker --version
docker compose version
python --version
node --version
npm --version
```

## Clone the repository

```bash
git clone https://github.com/Priyanka-Narula/Aambridge-AI_HRMS.git
cd Aambridge-AI_HRMS
```

## 1. Infrastructure (PostgreSQL + MinIO with Docker)

> Containers are configured with `restart: "no"` to keep your laptop fast. You must start them manually each session.

Start PostgreSQL and MinIO in the background:

```powershell
docker compose up -d
```

This creates:

**PostgreSQL**
- Container: `hrms-postgres`
- Database: `hrms`
- User / password: `hrms` / `hrms`
- Port: `5433` (host) → `5432` (container)

**MinIO (CV object storage)**
- Container: `hrms-minio`
- API: http://localhost:9000
- Console: http://localhost:9001 (login: `hrms` / `hrms_minio_secret`)
- Bucket: `hrms-cvs` (auto-created by `minio-init`)
- Uploaded CVs are stored under `cvs/{uuid}/{filename}.pdf`

Check that services are healthy:

```bash
docker compose ps
```

Stop services when finished:

```bash
docker compose down
```

Data persists in Docker volumes `postgres_data` and `minio_data`.

## 2. Backend setup

Create and activate a Python virtual environment:

**Windows (PowerShell):**

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy environment config and adjust if needed:

**Windows:**

```powershell
copy .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Default backend environment values in `.env.example`:

```
DATABASE_URL=postgresql://hrms:hrms@localhost:5433/hrms
DB_ECHO=false
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=hrms
MINIO_SECRET_KEY=hrms_minio_secret
MINIO_BUCKET=hrms-cvs
MINIO_SECURE=false
GOOGLE_DRIVE_SYNC_DIR=
```

Run database migrations (creates tables and seed data):

```bash
alembic upgrade head
```

Start the API server:

```bash
uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`.

Health checks:

- `GET /` — API status
- `GET /health/db` — database connection
- `GET /health/storage` — MinIO bucket connection
- `GET /test-upload` — browser CV upload test page

API docs: `http://127.0.0.1:8000/docs`

## Local CV Dropbox flow

Use the built-in upload page to test CV ingestion end-to-end:

1. Open `http://127.0.0.1:8000/test-upload`
2. Upload a `.pdf` CV
3. Click **Extract Candidate Info**
4. Confirm response includes `storage_uri` (for example `s3://hrms-cvs/cvs/<uuid>/resume.pdf`)

What happens after upload:

- PDF is saved to MinIO bucket `hrms-cvs`
- Text is extracted using PyMuPDF
- Candidate fields are parsed and validated into a `candidate_preview`
- Candidate is saved only after approval via API

Approval and save flow:

1. `POST /api/v1/candidates/upload` to upload/parse and get `candidate_preview`
2. Review/adjust preview in your candidate form
3. `POST /api/v1/candidates/approve` to save into `candidates` table

Optional direct save:

- Set `auto_approve=true` on `/api/v1/candidates/upload` to save immediately when validation passes

To verify files in MinIO:

- Open MinIO Console: `http://localhost:9001`
- Sign in with `hrms` / `hrms_minio_secret`
- Navigate to bucket `hrms-cvs` and folder prefix `cvs/`

## 3. Frontend setup

Open a new terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` (default Vite port).

Other scripts:

```bash
npm run build    # production build
npm run preview  # preview production build
```

## Project structure

```
Aambridge-AI_HRMS/
├── backend/
│   ├── alembic/          # Database migrations
│   ├── app/
│   │   ├── core/         # Config, database connection
│   │   ├── models/       # SQLAlchemy models
│   │   └── main.py       # FastAPI entry point
│   ├── .env.example      # Environment template (copy to .env)
│   └── requirements.txt
├── frontend/             # Vue 3 + Vite + TypeScript
├── docker-compose.yml    # PostgreSQL + MinIO services
└── README.md
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://hrms:hrms@localhost:5433/hrms` | PostgreSQL connection string |
| `DB_ECHO` | `false` | Log SQL queries when `true` |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO API host:port |
| `MINIO_ACCESS_KEY` | `hrms` | MinIO access key |
| `MINIO_SECRET_KEY` | `hrms_minio_secret` | MinIO secret key |
| `MINIO_BUCKET` | `hrms-cvs` | Bucket for uploaded CV PDFs |
| `MINIO_SECURE` | `false` | Use HTTPS for MinIO (`true` in production) |
| `GOOGLE_DRIVE_SYNC_DIR` | empty | Local Google Drive sync folder path for recruiter CV dropbox ingestion |

Set these in `backend/.env` (never commit `.env`).

## Git Workflow

### Pushing code for the first time (new branch)

```powershell
git checkout -b feature/your-feature-name
git add .
git commit -m "describe what you changed"
git push -u origin feature/your-feature-name
```

### Everyday push (existing branch)

```powershell
# 1. Check what has changed
git status

# 2. Stage files — either all changes or specific files
git add .
# or specific files:
git add backend/app/api/routes/candidates.py frontend/src/views/CandidateView.vue

# 3. Commit with a clear message
git commit -m "feat: add candidate approval flow"

# 4. Push to remote
git push
```

### Staying up to date with the main branch

```powershell
git checkout main
git pull origin main

# Switch back to your feature branch and bring in latest main
git checkout feature/your-feature-name
git merge main
```

### Common Git commands

| Command | Purpose |
|---------|---------|
| `git status` | See staged / unstaged / untracked files |
| `git diff` | See unstaged changes line by line |
| `git log --oneline -10` | Last 10 commits |
| `git stash` | Temporarily shelve uncommitted changes |
| `git stash pop` | Restore stashed changes |

### Files that must never be committed

The `.gitignore` already excludes these — double-check before pushing:

- `backend/.env` — contains database credentials and secrets
- `.venv/` — Python virtual environment
- `frontend/node_modules/` — npm packages
- `__pycache__/`, `*.pyc` — Python bytecode

---

## Troubleshooting

**Database connection failed**

- Ensure Docker is running: `docker compose ps`
- Confirm Postgres is healthy before running migrations
- Check `DATABASE_URL` in `backend/.env` matches `docker-compose.yml`

**Port 5433 already in use**

- Stop a local PostgreSQL service, or change the host port in `docker-compose.yml`

**MinIO upload failed (503)**

- Ensure MinIO is running: `docker compose ps`
- Open http://localhost:9001 and confirm bucket `hrms-cvs` exists
- Check `MINIO_*` values in `backend/.env` match `docker-compose.yml`

**Drive link files are not being processed**

- Google Drive links require auth; backend cannot directly crawl folder URLs
- Sync the Drive folder locally using Google Drive for Desktop
- Set `GOOGLE_DRIVE_SYNC_DIR` in `backend/.env` to that local folder path
- Call `POST /api/v1/candidates/drive-sync/process` to ingest synced PDFs into MinIO + parsing pipeline

**`/health/storage` returns 404**

- A stale backend process is running older code
- Stop all old Uvicorn processes and start the backend again from `backend/`
- Verify with `GET /health/storage` before testing uploads

**Alembic command not found**

- Activate the virtual environment and run from the `backend` directory

**Node version error**

- Use Node.js >= 22.12.0 (`node --version`)

## Git ignored files

The following are excluded from version control (see `.gitignore`):

- Python virtual environments (`.venv/`, `venv/`)
- `backend/.env` and other secrets
- `node_modules/`
- Python cache (`__pycache__/`, `*.pyc`)
- Build output and IDE/OS junk files
