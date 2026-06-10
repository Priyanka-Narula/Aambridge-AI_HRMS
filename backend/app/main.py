from fastapi import FastAPI

app = FastAPI(
    title="Aambridge HR Platform API",
    version="1.0"
)

@app.get("/")
def health():
    return {"status": "running"}