from pathlib import Path
from fastapi import APIRouter

from backend.vectorstore.vectorize_milvusdb import Vectorizer

router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval"],
)


@router.get("/search")
def search(
    project_name:str,
    query: str,
    top_k: int = 5,
    data_dir:Path = "data/processed",
    db_name:str = "prism"):

    vectorizer = Vectorizer(data_dir, project_name, db_name)
    results = vectorizer.search(query, top_k)

    return {
            "status": "success",
            "retrieved_docs": results
        }