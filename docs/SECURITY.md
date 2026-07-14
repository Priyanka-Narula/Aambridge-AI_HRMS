# Security

## Authentication

- JWT bearer tokens are issued by `POST /api/v1/auth/login`
- Tokens are sent by the frontend on every request via the API client interceptor
- Backend validates tokens and loads `current_user` via dependencies

## Authorization (RBAC)

Roles:

- **Owner**: user management and client management
- **Recruiter**: candidates, attendance, and personal settings

Authorization is enforced in two places:

- **Backend**: route dependencies (owner-only endpoints require owner)
- **Frontend**: router `meta.roles` + guard redirects to `/unauthorized`

Backend checks are the source of truth.

## Passwords

- Stored as a secure hash (never plaintext)
- Change password is supported via `POST /api/v1/auth/change-password`

## Secrets management

Never commit secrets. In particular:

- `backend/.env` must not be committed
- JWT secret must be unique per environment

For production, use:

- Environment variables injected by the runtime (container/Kubernetes/VM)
- A secrets manager (Vault/AWS Secrets Manager/GCP Secret Manager/Azure Key Vault)

## Storage security (CVs)

- CV PDFs are stored in MinIO (S3-compatible)
- In production:
  - Use TLS (`MINIO_SECURE=true`)
  - Use non-default access keys and rotate credentials
  - Consider bucket policies / server-side encryption

## CORS

Ensure the backend CORS configuration is restricted appropriately in production (specific origins rather than `*`).

## Audit / compliance considerations (recommended)

For HR systems, common expectations include:

- Audit logging for user management changes
- Access logs and retention policy
- Data retention / deletion policy for CVs and candidate records
- Principle of least privilege (separate service credentials per environment)

