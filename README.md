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
- **Analytics dashboards**
  - Owner Executive Command Center with business KPIs, hiring funnel, recruiter performance, workload, client/job health, activity, and alerts
  - Recruiter performance cockpit with today's priorities, outcome KPIs, personal funnel, team rank and median benchmark, action queue, at-risk jobs, and six-month trends
  - Healthy competition scoring prioritizes placements, interviews, offer acceptance, and hiring speed; candidate-upload volume and attendance are excluded
  - Live refresh through authenticated dashboard WebSocket events
- **Job Requirements**
  - Owner creates job openings linked to a client and assigns them to a recruiter
  - Fields: title, department, employment type, work mode, experience range, salary range, open positions, job description, location, priority, requirement type, status
  - Status lifecycle: `open` → `on_hold` / `closed` / `filled` (Owner-only status patch)
  - Recruiters see only the requirements assigned to them; Owner sees all
  - List view with search, inline edit modal, and status quick-update
  - Click-through to per-requirement **detail view** with Details + Submissions tabs
- **Candidate Pipeline (Submissions)**
  - Recruiters submit candidates to an assigned job requirement via a **2-step modal**: pick candidate → fill client verification form
  - Submission form fields are auto-prefilled from the candidate's profile (name, email, phone, visa, experience, etc.)
  - Mandatory field validation against the client's submission template before saving
  - **Deduplication rules** enforced on submit:
    - Same candidate → same client within 6 months → blocked
    - Same candidate → different client within 3 months while still active → blocked
  - Each submission is placed at the first pipeline stage automatically
  - **Owner approval workflow**: Owner can approve or reject each submission inline
  - **Excel downloads**:
    - Download a single submission as a formatted `.xlsx` using the client's column template
    - Download all submissions for a job requirement as a multi-row `.xlsx` (bulk export)
    - Download all approved submissions for a client across all jobs
  - Owner dashboard: submissions grouped by client → job for a bird's-eye view
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
- MinIO Console: `http://localhost:9001` (login: `hrms` / `hrms_minio_secret`) — API on port `9009`

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
  alembic/
    versions/              # migrations (001–008)
  app/
    api/routes/            # auth, users, clients, candidates, attendance,
                           #   job requirements, submissions, dashboards
    api/schemas/           # Pydantic API contracts, including dashboard responses
    core/                  # config, database, auth deps
    models/                # SQLAlchemy models (incl. job_requirement, pipeline)
    services/              # business logic, analytics, and dashboard aggregates
    main.py                # FastAPI app entry
  .env.example
  requirements.txt
frontend/
  src/
    api/                   # API clients (incl. jobRequirements.ts, submissions.ts)
    assets/                # styling + logo
    components/            # UI, domain components, and dashboard modules
    config/                # navigation
    stores/                # Pinia stores
    types/                 # TS types (incl. jobRequirement.ts)
    views/                 # pages (incl. JobRequirementsView.vue,
                           #   JobRequirementDetailView.vue)
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
  - `MINIO_ENDPOINT` (default: `127.0.0.1:9009`)
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
- `docs/API.md` — API surface and contracts (auth, users, clients, candidates, attendance, job requirements, submissions)
- `docs/SECURITY.md` — authentication, RBAC, secrets handling, and security notes
- `docs/RUNBOOK.md` — operations, troubleshooting, and production checklist
- `docs/DASHBOARD_ANALYTICS.md` — dashboard metric definitions, attribution rules, date semantics, and API behavior

## Contributing / development notes

- Never commit secrets (`backend/.env`, credentials).
- After pulling changes, always run `alembic upgrade head`. The migration chain is: `001_initial_schema` → `002_seed_defaults` → `003_attendance` → `004_*` → `005_add_personal_email_to_users` → `006_job_requirement_assigned_to` → `007_candidate_submission` → `008_submission_data`.
- If the UI and API disagree on fields, first verify the response model in `backend/app/api/schemas/` and the serializer in `backend/app/services/`.
- `openpyxl` is required for Excel export; it is listed in `requirements.txt`. If the package is missing, the download endpoints return HTTP 500.
