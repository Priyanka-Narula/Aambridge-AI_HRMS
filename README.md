Activate virtual environment
    source venv/Scripts/activate   # Windows: .venv\Scripts\activate

## Database (PostgreSQL)

Start PostgreSQL with Docker:

    docker compose up -d

Copy environment config:

    copy backend\.env.example backend\.env

Run migrations:

    cd backend
    alembic upgrade head

## Backend

    cd backend
    uvicorn app.main:app --reload

Health check: `GET /` and `GET /health/db`

## Frontend

    cd frontend
    npm run dev
