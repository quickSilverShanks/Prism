## Plan

This file contains a rough scratchpad meant to contain the plans and milestones for the development of this project.

The original work is in AWS Bedrock with milvus db, s3 bucket, lambda functions being used. This repo aims to present an open-source alternative of the commercial product with local llm models, postgresql, milvus and a forward looking architecture as compared the original project it takes inspiration from.

### Scratchpad

Input pdf file should be ingested through a script and saved as a structured table with chunked data in postgres and as a vectordb in milvus. This will use docling and other libraries installed, milvus db with local server running, postgres schema created.

Docker compose has below codes that need prepared minimally to begin with:
- backend.main:app
- frontend/app.py

run required models to begin with as below
- docker exec -it prism-ollama ollama pull qwen3:8b

### Milestones

- [] initial/minimal docker setup with local mounts for all type of data
- [] PDF Ingest script (indexing to milvus)
- [] PDF Ingest script (output to postgresql)
- [] Expose FastAPI endpoint to perform chunking
- [] Add Streamlit page to upload file from user and ingest
- [] Add second tab in frontend to view ingested data
- [] Perform basic eda on ingested data and show in streamlit tab
