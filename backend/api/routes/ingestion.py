from pathlib import Path
from fastapi import APIRouter

from backend.ingestion.document_loader.pdf2md import PDFParser

router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


@router.post("/pdf2md")
def pdf_to_markdown(
    filename:str,
    input_path: Path = "data/uploads",
    output_root: Path = "data/processed"
):
    
    parser = PDFParser(filename, input_path, output_root)
    docs = parser.parse()

    return {
        "status": "success",
        "message": "PDF parsed successfully.",
        "paragraphs_imported ": len(docs[0].page_content),
    }