from pathlib import Path
from fastapi import APIRouter

from backend.chunking.document_chunker import DocumentChunker

router = APIRouter(
    prefix="/chunking",
    tags=["Chunking"],
)


@router.post("/document")
def chunk_document(
    project_name:str,
    data_dir:Path = "data/processed",
    export:bool = True
):

    chunker = DocumentChunker(project_name, data_dir, export)
    final_split_docs = chunker.chunk()

    return {
        "status": "success",
        "chunks_created": len(final_split_docs),
    }