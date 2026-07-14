# API Reference (High-level)

This document describes the primary HTTP APIs used by the frontend.

For the live, source-of-truth OpenAPI docs, run the backend and open:

- `GET /docs` (Swagger UI)

## Conventions

- Base path: `/api/v1`
- Auth: Bearer JWT via `Authorization: Bearer <token>`
- Roles:
  - **Owner**: admin user management + clients
  - **Recruiter**: candidates + attendance + settings

## Auth

- `POST /api/v1/auth/login`
  - Request: `{ email, password }`
  - Response: `{ access_token, token_type }`

- `GET /api/v1/auth/me`
  - Response: user profile + role + recruiter profile (if recruiter)

- `PUT /api/v1/auth/me`
  - Updates the logged-in user’s profile (name, email, phone, location, languages)
  - Response: updated `/me` payload

- `POST /api/v1/auth/change-password`
  - Request: `{ current_password, new_password }`
  - Response: `204 No Content`

## Users / Recruiters (Owner only)

- `GET /api/v1/users/`
  - List recruiters

- `POST /api/v1/users/recruiters`
  - Create recruiter user + recruiter profile

- `GET /api/v1/users/{user_id}`
  - Get recruiter details

- `PUT /api/v1/users/{user_id}`
  - Update recruiter details (user + recruiter profile)

- `PATCH /api/v1/users/{user_id}/status`
  - Activate/deactivate recruiter

## Clients (Owner only)

- `GET /api/v1/clients/`
- `POST /api/v1/clients/`
- `GET /api/v1/clients/{client_id}`
- `PUT /api/v1/clients/{client_id}`
- `PATCH /api/v1/clients/{client_id}/status`

Clients include contacts and an optional `submission_format` describing required submission fields.

## Candidates (Owner + Recruiter)

- `GET /api/v1/candidates/`
- `GET /api/v1/candidates/{candidate_id}`
- `POST /api/v1/candidates/`
- `PUT /api/v1/candidates/{candidate_id}`
- `DELETE /api/v1/candidates/{candidate_id}`
- `GET /api/v1/candidates/{candidate_id}/resume`

CV ingestion APIs are provided under the CV/candidates routes (see Swagger).

## Attendance (Owner + Recruiter; owner has extra views)

- `GET /api/v1/attendance/policy`
  - Returns `{ checkin_expected, checkout_expected, late_threshold, timezone }`

- `POST /api/v1/attendance/checkin`
- `POST /api/v1/attendance/checkout`
- `GET /api/v1/attendance/today/me`
- `GET /api/v1/attendance/today` (Owner view of team attendance)

