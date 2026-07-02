from fastapi import FastAPI

from backend.api.routes import (
    health,
    ingestion,
    chunking,
    vectorize,
    retrieval,
)

app = FastAPI(
    title="Prism API",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "application": "Prism API",
        "version": "0.1.0",
        "message": "Welcome to Prism. Visit /docs for API documentation."
    }

app.include_router(health.router)
app.include_router(ingestion.router)
app.include_router(chunking.router)
app.include_router(vectorize.router)
app.include_router(retrieval.router)