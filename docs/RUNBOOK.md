# Runbook (Operations)

## Local environment

### Start

1. `docker compose up -d`
2. Backend:
   - Activate venv
   - `alembic upgrade head`
   - `uvicorn app.main:app --reload`
3. Frontend:
   - `npm install`
   - `npm run dev`

### Stop

- `docker compose down`

## Common issues

### Backend cannot connect to database

- Confirm Docker is running
- Confirm Postgres container is up: `docker compose ps`
- Confirm `DATABASE_URL` matches `docker-compose.yml` port mapping (host port is `5433`)

### pgAdmin cannot see the HRMS database

Docker Postgres is **not** on the default port `5432`. Use these settings when registering a server in pgAdmin (desktop or `http://localhost:5050` after `docker compose up -d`):

| Field | Value |
| --- | --- |
| Host | `localhost` (desktop pgAdmin) or `postgres` (pgAdmin container) |
| Port | `5433` (desktop) or `5432` (pgAdmin container) |
| Maintenance database | `hrms` |
| Username | `hrms` |
| Password | `hrms` |

After a fresh Postgres volume, run migrations before starting the API:

```powershell
cd backend
.\venv\Scripts\alembic.exe upgrade head
```

Without migrations you will see an empty `hrms` database or API errors like `relation "roles" does not exist`.

To reset the database completely:

```powershell
docker compose down -v
docker compose up -d
cd backend
.\venv\Scripts\alembic.exe upgrade head
```

### Migration errors

- Ensure venv is activated
- Run `alembic upgrade head`
- If two branches added migrations, a merge migration may be required (resolve in Alembic)

### Docker / compose hangs (Windows)

If `docker compose down` or `docker compose up` freezes with no output:

1. Press **Ctrl+C** in the stuck terminal.
2. **Quit Docker Desktop** completely (tray icon → Quit), wait 10 seconds, start it again.
3. From the project root, run:

```powershell
.\scripts\docker-recover.ps1
```

This force-removes HRMS containers (including old orphans `hrms-backend`, `hrms-frontend`) and starts a clean Postgres + MinIO stack.

If it still hangs, open **Task Manager** and end any stuck `com.docker.*` or `docker` processes, then restart Docker Desktop.

### MinIO upload/download issues

- Confirm MinIO is running: `docker compose ps`
- Check MinIO health: `http://127.0.0.1:9000/minio/health/live` should return `200`
- Check API health: `http://127.0.0.1:8000/health/storage`
- Confirm `MINIO_ENDPOINT` in `backend/.env` is `127.0.0.1:9000` (matches `docker-compose.yml` port `9000:9000`)
- If `minio-init` exited with an error, recreate the stack:

```powershell
docker compose down --remove-orphans
docker compose up -d
docker compose logs minio-init
```

- MinIO console: `http://localhost:9001` (login: `hrms` / `hrms_minio_secret`)
- If the container shows "Up" but health fails, force-recreate MinIO:

```powershell
docker compose up -d --force-recreate minio minio-init
```

- If a resume returns 503, MinIO was down when requested — restart Docker services and retry. Re-upload the CV if the object was never stored.

### Pipeline / share by email

Hiring flow:

1. Recruiter submits candidate → **Submissions** (owner review)
2. Owner approves → **Download Approved** or **Share by Email** to client
3. After client shortlist feedback → **Add to Pipeline** (stage = Shortlisted)
4. Recruiters update stages on **Pipeline**: Screening → Interview → Offer → Joined

Email sharing needs SMTP in `backend/.env`:

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=talent@aambridge.ai
SMTP_USE_TLS=true
```

Without SMTP, use **Download Approved** and send the Excel manually.

### Frontend “Unauthorized” redirect issues

- Verify user role returned from `/api/v1/auth/me`
- Verify router meta roles match the intended access

## Production checklist (baseline)

- Use a real secret for `JWT_SECRET_KEY`
- Set `MINIO_SECURE=true` and use TLS
- Configure CORS to allowed origins only
- Use a managed PostgreSQL with backups enabled
- Enable structured logs and centralize them
- Add monitoring/alerts for:
  - API latency and error rates
  - Database connectivity
  - Object storage connectivity

