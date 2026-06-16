# Aambridge AI HRMS

HR platform with a FastAPI backend, Vue 3 frontend, and PostgreSQL database.

## Prerequisites

Install the following before setup:

| Tool | Version | Purpose |
|------|---------|---------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Latest | PostgreSQL via Docker Compose |
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

## 1. Database (PostgreSQL with Docker)

Start PostgreSQL in the background:

```bash
docker compose up -d
```

This creates:

- Container: `hrms-postgres`
- Database: `hrms`
- User / password: `hrms` / `hrms`
- Port: `5432`

Check that Postgres is healthy:

```bash
docker compose ps
```

Stop the database when finished:

```bash
docker compose down
```

Data persists in the Docker volume `postgres_data`.

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
├── docker-compose.yml    # PostgreSQL service
└── README.md
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://hrms:hrms@localhost:5432/hrms` | PostgreSQL connection string |
| `DB_ECHO` | `false` | Log SQL queries when `true` |

Set these in `backend/.env` (never commit `.env`).

## Troubleshooting

**Database connection failed**

- Ensure Docker is running: `docker compose ps`
- Confirm Postgres is healthy before running migrations
- Check `DATABASE_URL` in `backend/.env` matches `docker-compose.yml`

**Port 5432 already in use**

- Stop a local PostgreSQL service, or change the host port in `docker-compose.yml`

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
