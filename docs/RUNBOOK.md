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

### Migration errors

- Ensure venv is activated
- Run `alembic upgrade head`
- If two branches added migrations, a merge migration may be required (resolve in Alembic)

### MinIO upload/download issues

- Confirm MinIO is running
- Open MinIO console and verify bucket exists

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

