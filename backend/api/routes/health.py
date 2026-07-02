from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health():
    """
    Basic API health check.
    """
    return {
        "application": "Prism API",
        "status": "healthy",
        "services": {
            "backend": "UP",
            "frontend": "UP",
            "postgres": "UNKNOWN",
            "milvus": "UNKNOWN",
            "ollama": "UNKNOWN",
            "minio": "UNKNOWN",
            "cloudbeaver": "UNKNOWN",
            "attu": "UNKNOWN",
            "dozzle": "UNKNOWN",
        },
    }


@router.get("/services")
def services():
    """
    List all services in the Prism stack.
    """
    return {
        "backend": "http://localhost:8000",
        "frontend": "http://localhost:8501",
        "swagger": "http://localhost:8000/docs",
        "postgres": "postgres:5432",
        "milvus": "milvus:19530",
        "ollama": "http://ollama:11434",
        "minio": "http://localhost:9000",
        "cloudbeaver": "http://localhost:8978",
        "attu": "http://localhost:3000",
        "dozzle": "http://localhost:8080",
    }