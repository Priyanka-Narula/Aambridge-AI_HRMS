# Architecture

## System overview

The system is a classic SPA + API architecture:

- **Frontend**: Vue 3 (Vite) SPA
  - Auth state: Pinia store (`frontend/src/stores/auth.ts`)
  - API layer: Axios client + feature modules (`frontend/src/api/*`)
  - Views: `frontend/src/views/*`
- **Backend**: FastAPI application (`backend/app/main.py`)
  - Routes: `backend/app/api/routes/*`
  - Schemas: Pydantic models in `backend/app/api/schemas/*`
  - Services: business logic in `backend/app/services/*`
  - Persistence: SQLAlchemy models in `backend/app/models/*` with Alembic migrations
- **Data stores**
  - PostgreSQL: primary relational database
  - MinIO (S3-compatible): CV PDF storage

## Major modules

### Authentication & RBAC

- JWT-based authentication
- Role-based access control enforced on:
  - Backend route dependencies (e.g. Owner-only endpoints)
  - Frontend router meta (`roles`) + guards

### Candidates

- CV upload/parse/preview and approval flow
- Candidate list with an expandable detail side panel
- Candidate edit is performed via a draft object -> update payload mapping on the frontend

### Clients

- Client CRUD and contact management
- Client submission template builder (a list of required fields used when submitting candidates)
- Client list with expandable detail side panel

### Recruiters (User management)

- Owner creates and manages recruiter accounts
- Recruiter list with expandable detail side panel
- Recruiter editing updates both the `users` and `recruiters` tables

### Attendance

- Web check-in/out using server time stored in DB
- Status computed based on configured office timezone and late threshold
- Policy is configurable by env vars and exposed via API for UI display

## Data flow (common patterns)

### SPA calling API

1. Frontend calls `frontend/src/api/*.ts`
2. Axios client attaches the JWT token (if present)
3. FastAPI validates token, loads `current_user`, applies role restriction
4. Service layer performs DB logic and returns a schema-compatible response

### Expandable “split panel” UI

The candidates/clients/recruiters views use a shared interaction model:

- Main list (left) is always visible
- Selecting a card loads (or reuses) the full entity and opens a side panel
- Side panel contains tabs + quick actions (Edit / Activate-Deactivate / Links)

## Configuration

Backend uses `pydantic-settings` and reads `.env`. Frontend configuration is mostly compile-time via Vite.

## Operational notes

For operational guidance and production hardening, see `docs/RUNBOOK.md` and `docs/SECURITY.md`.

