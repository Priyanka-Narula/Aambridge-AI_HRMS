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
| MinIO Console | http://localhost:9001 (login: `hrms` / `hrms_minio_secret`) |

When done for the day:
```powershell
docker compose down
```

> **Note:** Docker containers are set to `restart: "no"` — they will not start automatically on boot. Always run `docker compose up -d` before starting the backend.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Latest | PostgreSQL and MinIO via Docker Compose |
| [Python](https://www.python.org/downloads/) | 3.11+ | Backend API |
| [Node.js](https://nodejs.org/) | >= 22.12.0 | Frontend |
| [Git](https://git-scm.com/) | Latest | Version control |

## Clone the repository

```bash
git clone https://github.com/Priyanka-Narula/Aambridge-AI_HRMS.git
cd Aambridge-AI_HRMS
```

---

## 1. Infrastructure (PostgreSQL + MinIO)

```powershell
docker compose up -d
docker compose ps   # confirm services are healthy
```

**PostgreSQL**
- Container: `hrms-postgres` · Database: `hrms` · User/password: `hrms`/`hrms`
- Port: `5433` (host) → `5432` (container)

**MinIO (CV object storage)**
- API: http://localhost:9000 · Console: http://localhost:9001
- Bucket: `hrms-cvs` (auto-created) · CVs stored under `cvs/{uuid}/{filename}.pdf`

Data persists in Docker volumes `postgres_data` and `minio_data`.

---

## 2. Backend setup

**Create and activate a virtual environment:**

```powershell
# Windows
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

> **Windows note:** `requirements.txt` includes `tzdata`, which provides IANA timezone data needed by the attendance feature on Windows.

**Configure environment:**

```powershell
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Edit `backend/.env` with your values (see [Environment variables](#environment-variables) below).

**Run migrations and start the server:**

```bash
alembic upgrade head        # creates all tables (runs once, or after pulling new migrations)
uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000` · API docs at `http://127.0.0.1:8000/docs`

Health checks: `GET /` · `GET /health/db` · `GET /health/storage`

---

## 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

```bash
npm run build    # production build
npm run preview  # preview production build
```

---

## Project structure

```
Aambridge-AI_HRMS/
├── backend/
│   ├── alembic/          # Migrations: 001 schema · 002 seed · 003 attendance
│   ├── app/
│   │   ├── api/routes/   # auth, users, candidates, cv, attendance
│   │   ├── core/         # Config, database, auth deps
│   │   ├── models/       # SQLAlchemy models (incl. attendance.py)
│   │   └── main.py       # FastAPI entry point
│   ├── .env.example
│   └── requirements.txt
├── frontend/             # Vue 3 + Vite + TypeScript
├── docker-compose.yml    # PostgreSQL + MinIO
└── README.md
```

---

## Environment variables

Set these in `backend/.env` — never commit `.env`.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://hrms:hrms@localhost:5433/hrms` | PostgreSQL connection string |
| `DB_ECHO` | `false` | Log SQL queries |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO API host:port |
| `MINIO_ACCESS_KEY` | `hrms` | MinIO access key |
| `MINIO_SECRET_KEY` | `hrms_minio_secret` | MinIO secret key |
| `MINIO_BUCKET` | `hrms-cvs` | Bucket for uploaded CV PDFs |
| `MINIO_SECURE` | `false` | Use HTTPS for MinIO (`true` in production) |
| `GOOGLE_DRIVE_SYNC_DIR` | empty | Local Google Drive sync folder for CV ingestion |
| `JWT_SECRET_KEY` | *(required)* | Secret key for signing JWT tokens |
| `OFFICE_TIMEZONE` | `Asia/Dubai` | IANA timezone for attendance date/status |
| `CHECKIN_EXPECTED` | `09:30` | Expected check-in time shown on dashboard |
| `CHECKOUT_EXPECTED` | `18:30` | Expected check-out time shown on dashboard |
| `LATE_THRESHOLD` | `10:00` | Check-ins after this time are marked Late |

---

## CV ingestion flow

1. Open `http://127.0.0.1:8000/test-upload`, upload a `.pdf` CV, click **Extract Candidate Info**
2. Backend saves the PDF to MinIO, extracts text with PyMuPDF, and parses it into a `candidate_preview`
3. `POST /api/v1/candidates/upload` — upload/parse, returns preview
4. `POST /api/v1/candidates/approve` — save approved candidate to the `candidates` table
5. Set `auto_approve=true` on the upload endpoint to skip the review step

**Google Drive dropbox:** sync a Drive folder locally, set `GOOGLE_DRIVE_SYNC_DIR` in `.env`, then call `POST /api/v1/candidates/drive-sync/process` to ingest all PDFs.

---

## Web Check-In

Recruiters log their daily attendance directly from the dashboard — no cron jobs required.

### Recruiter experience

The **Today's Attendance** card appears in the top-right of the dashboard immediately after login.

1. Click **Check In** — time is recorded and a green confirmation badge replaces the button.
2. A **Check Out** button appears below the badge when you are ready to leave.
3. After checking out the card shows both times and is complete for the day.

| Check-in time | Status |
|---------------|--------|
| At or before 10:00 AM | On Time (green) |
| After 10:00 AM | Late (orange) |
| No check-in recorded | Absent (red) |

> Expected in: **9:30 AM** · Grace period until **10:00 AM** · Expected out: **6:30 PM**

### Owner view

The owner sees only the **Team Attendance** table — every active recruiter's check-in time, check-out time, and status for today, with Present / Late / Absent / Total counters in the header.

### Attendance API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/attendance/checkin` | Any | Record today's check-in |
| POST | `/api/v1/attendance/checkout` | Any | Record today's check-out |
| GET | `/api/v1/attendance/today/me` | Any | Get your own today's record |
| GET | `/api/v1/attendance/today` | Owner | Get all recruiters' today records |

---

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
git status
git add .
git commit -m "feat: add candidate approval flow"
git push
```

### Staying up to date

```powershell
git checkout main
git pull origin main
git checkout feature/your-feature-name
git merge main
```

### Common commands

| Command | Purpose |
|---------|---------|
| `git status` | See staged / unstaged / untracked files |
| `git diff` | See unstaged changes |
| `git log --oneline -10` | Last 10 commits |
| `git stash` / `git stash pop` | Shelve and restore uncommitted changes |

### Files that must never be committed

`.gitignore` already excludes these — double-check before pushing:

- `backend/.env` — credentials and secrets
- `.venv/` — Python virtual environment
- `frontend/node_modules/` — npm packages
- `__pycache__/`, `*.pyc` — Python bytecode

---

## Troubleshooting

**Database connection failed**
- Ensure Docker is running: `docker compose ps`
- Check `DATABASE_URL` in `backend/.env` matches `docker-compose.yml`

**Port 5433 already in use**
- Stop a local PostgreSQL service, or change the host port in `docker-compose.yml`

**MinIO upload failed (503)**
- Ensure MinIO is running: `docker compose ps`
- Open http://localhost:9001 and confirm bucket `hrms-cvs` exists

**Drive sync files not processing**
- Set `GOOGLE_DRIVE_SYNC_DIR` to your locally synced Drive folder path
- Call `POST /api/v1/candidates/drive-sync/process` to ingest PDFs

**`/health/storage` returns 404**
- A stale Uvicorn process is running older code — restart the backend

**Alembic command not found**
- Activate the virtual environment and run from the `backend/` directory

**Node version error**
- Use Node.js >= 22.12.0 (`node --version`)

**`ZoneInfoNotFoundError: Asia/Dubai`**
- Run `pip install tzdata` inside the virtual environment, or re-run `pip install -r requirements.txt`
