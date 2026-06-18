
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

Start PostgreSQL and MinIO in the background:

```bash
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

Default `DATABASE_URL` in `.env.example`:

```
postgresql://hrms:hrms@localhost:5432/hrms
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

Set these in `backend/.env` (never commit `.env`).

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
