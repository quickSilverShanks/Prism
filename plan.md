## Plan

This file has a scratchpad meant to contain the working plans and thoughts, milestones to track the development of this project and a section on developer notes that mentions frequently used code snippets, design choices and their rationale for future reference.

The original work is in AWS Bedrock with milvus db, s3 bucket, lambda functions being used. This repo aims to present an open-source alternative of the commercial product with local llm models, postgresql, milvus and a forward looking architecture as compared the original project it takes inspiration from.

### Scratchpad

Input pdf file should be ingested through a script and saved as a structured table with chunked data in postgres and as a vectordb in milvus. This will use docling and other libraries installed, milvus db with local server running, postgres schema created.

Docker compose has below codes that need prepared minimally to begin with:
- backend.main:app
- frontend/app.py

run required models to begin with as below
- docker exec -it prism-ollama ollama pull qwen3:8b

### Milestones

- [] Initial Docker setup with persistent local mounts
- [] PDF ingestion pipeline (Milvus indexing)
- [] PDF ingestion pipeline (PostgreSQL metadata)
- [] FastAPI endpoint for document chunking
- [] Streamlit page for document upload & ingestion
- [] Streamlit page to browse ingested documents
- [] Basic EDA dashboard for ingested data
- [] Streamlit page with general chat interface
- [] Add postgres db with interaction logs
- [] Hybrid search (Dense + Sparse retrieval) with reranking
- [] Langchain based conversational RAG over PDFs
- [] LangGraph based agentic rag workflow
- [] Add required test scripts
- [] Release v1.0

## Milestones (Future Updates)

* [ ] Multi-document project understanding and metadata filter update
* [ ] Codebase ingestion
* [ ] Conversational RAG over source code
* [ ] LangGraph agent workflow update
* [ ] Excel ingestion support
* [ ] Image/OCR ingestion support (multimodal rag)
* [ ] Project analytics dashboard
* [ ] Docker production optimization
* [ ] Unit & integration tests
* [ ] CI/CD pipeline
* [ ] Release v2.0

### Developer Notes

When user uploads the document:
> load_document() → chunk_document() → save_chunks_to_postgres() → generate_embeddings() → store_in_milvus() → save_metadata_to_postgres()

- uploaded document: data/uploads/project.pdf
- ingestion/document_loader/pdf2markdown.py (output stored in data/processed)
- chunking/document_chunker.py
- embeddings/embedding_service.py
- vectorstore/milvus_client.py
