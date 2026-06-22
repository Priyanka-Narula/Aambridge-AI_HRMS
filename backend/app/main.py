from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.routes import candidates

app = FastAPI(
    title="Aambridge HR Platform API",
    version="1.0",
)


@app.get("/")
def health():
    return {"status": "running"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "running", "database": "connected"}


app.include_router(candidates.router)