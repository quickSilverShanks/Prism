from pathlib import Path
from fastapi import APIRouter

from backend.chunking.document_chunker import DocumentChunker
from backend.vectorstore.vectorize_milvusdb import Vectorizer

router = APIRouter(
    prefix="/vectorstore",
    tags=["Vector Store"],
)


@router.post("/vectorize")
def vectorize(
    project_name:str,
    data_dir:Path = "data/processed",
    export:bool = True,
    db_name:str = "prism",
    replace_collection:bool = False,
    replace_db:bool = False
):

    chunker = DocumentChunker(project_name, data_dir, export)
    final_split_docs = chunker.chunk()

    vectorizer = Vectorizer(data_dir, project_name, db_name, replace_collection, replace_db)
    vectorizer.vectorize(split_docs=final_split_docs)

    return {
        "status": "success",
        "message": "Documents indexed in Milvus."
    }