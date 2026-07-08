# Aambridge AI HRMS

Recruitment/HRMS platform built with **FastAPI + PostgreSQL + MinIO** (backend) and **Vue 3 + Pinia + Vite** (frontend).

This repository contains everything needed to run the system locally for development and to deploy it in a standard environment.

## What this software does (features)

- **Authentication & roles**
  - JWT login
  - Roles: **Owner**, **Recruiter**
  - Route-level access control (Owner-only: Recruiters, Clients; shared: Candidates, Attendance, Settings)
- **Candidates**
  - CV upload + parsing preview + approval/save
  - Candidate management with list + **expandable detail panel** + edit
  - Fields include **Industry** and **UAE experience (years)**
- **Clients**
  - Manage client companies and contacts
  - Build per-client **candidate submission templates** (includes UAE experience)
  - List + **expandable detail panel** + edit
- **Recruiters**
  - Create recruiter accounts (Owner)
  - Update recruiter profiles (Owner)
  - List + **expandable detail panel** + edit
- **Attendance (Web Check-In)**
  - Recruiters check-in/out from dashboard
  - Owner can view team attendance
  - Policy is configurable via environment variables and exposed via API
- **Settings**
  - Users can update their own profile and change password

## Quick start (daily dev workflow)

From the project root, use three terminals.

Terminal 1 (Infrastructure):

```powershell
docker compose up -d
```

Terminal 2 (Backend):

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --reload
```

Terminal 3 (Frontend):

```powershell
cd frontend
npm install
npm run dev
```

Local URLs:

- Frontend: `http://localhost:5173`
- Backend API: `http://127.0.0.1:8000`
- API Docs (Swagger): `http://127.0.0.1:8000/docs`
- MinIO Console: `http://localhost:9001` (login: `hrms` / `hrms_minio_secret`)

When done:

```powershell
docker compose down
```

## Prerequisites

- Docker Desktop (PostgreSQL + MinIO via Compose)
- Python 3.11+
- Node.js 22+
- Git

## Repository structure

```
backend/
  alembic/                 # migrations
  app/
    api/routes/            # auth, users, clients, candidates, cv, attendance
    api/schemas/           # pydantic schemas
    core/                  # config, database, auth deps
    models/                # SQLAlchemy models
    services/              # business logic/services
    main.py                # FastAPI app entry
  .env.example
  requirements.txt
frontend/
  src/
    api/                   # API clients
    assets/                # styling + logo
    components/            # UI + domain components
    config/                # navigation
    stores/                # Pinia stores
    types/                 # TS types
    views/                 # pages
docker-compose.yml
README.md
docs/
```

## Configuration (environment variables)

Set these in `backend/.env` (never commit `.env`).

- **Database**
  - `DATABASE_URL` (default: `postgresql://hrms:hrms@localhost:5433/hrms`)
  - `DB_ECHO` (default: `false`)
- **MinIO / CV storage**
  - `MINIO_ENDPOINT` (default: `localhost:9000`)
  - `MINIO_ACCESS_KEY` (default: `hrms`)
  - `MINIO_SECRET_KEY` (default: `hrms_minio_secret`)
  - `MINIO_BUCKET` (default: `hrms-cvs`)
  - `MINIO_SECURE` (default: `false`)
- **Auth**
  - `JWT_SECRET_KEY` (required)
  - `JWT_ALGORITHM` (default: `HS256`)
  - `ACCESS_TOKEN_EXPIRE_MINUTES` (default: `480`)
- **Attendance**
  - `OFFICE_TIMEZONE` (default: `Asia/Dubai`)
  - `CHECKIN_EXPECTED` (default: `09:00`)
  - `CHECKOUT_EXPECTED` (default: `18:30`)
  - `LATE_THRESHOLD` (default: `09:15`)
- **Optional ingestion**
  - `GOOGLE_DRIVE_SYNC_DIR` (optional)
- **Bootstrap owner (first run)**
  - `BOOTSTRAP_OWNER_EMAIL` (default: `owner@aambridge.ai`)
  - `BOOTSTRAP_OWNER_PASSWORD` (required to create initial owner)
  - `BOOTSTRAP_OWNER_FIRST_NAME`, `BOOTSTRAP_OWNER_LAST_NAME`

## Documentation set (industry-standard)

See `docs/` for the full documentation set:

- `docs/ARCHITECTURE.md` — components, data flow, and key design decisions
- `docs/API.md` — API surface and contracts (auth, users, clients, candidates, attendance)
- `docs/SECURITY.md` — authentication, RBAC, secrets handling, and security notes
- `docs/RUNBOOK.md` — operations, troubleshooting, and production checklist

## Contributing / development notes

- Never commit secrets (`backend/.env`, credentials).
- After pulling changes, always run `alembic upgrade head`.
- If the UI and API disagree on fields, first verify the response model in `backend/app/api/schemas/` and the serializer in `backend/app/services/`.
