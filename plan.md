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

Updates to be done later:
- At initial stage, create json outputs instead of directly writing to postgresdb. Once chunking and vectorizing works fine, start adding postgres elements for every relevant output. Until then, schema and db initialization codes reamin unused.
- For now, use smaller pdf files and insert entire chunked data into milvus collection at once. Add batch mode later.
- Also, all the classes/methods need refinement as in the parameters that should be there for init and the ones that should be moved to methods.
- The initialization parameter `self.auto_id` will be removed from vectorize_milvusdb.py later when chunk ids will be obtained from postgres db directly.
- Add dozzle in the container to view logs for now, later replace it with logstash + something appropriate to capture agentic logs separately.
- The vectoprize router of fastapi does chunking before indexing in milvus. After chunks are available in postgres, this won't be required.

### Milestones

* [ ] Initial Docker setup with persistent local mounts
* [ ] PDF ingestion pipeline (Milvus indexing)
* [ ] PDF ingestion pipeline (PostgreSQL metadata)
* [ ] FastAPI endpoint for document chunking
* [ ] Streamlit page for document upload & ingestion
* [ ] Streamlit page to browse ingested documents
* [ ] Basic EDA dashboard for ingested data
* [ ] Streamlit page with general chat interface
* [ ] Add postgres db with interaction logs
* [ ] Hybrid search (Dense + Sparse retrieval) with reranking
* [ ] Langchain based conversational RAG over PDFs
* [ ] LangGraph based agentic rag workflow
* [ ] Add required test scripts
* [ ] Release v1.0 (MVP)

### Milestones (Future Updates)

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

## Developer Notes

When user uploads the document:
> load_document() → chunk_document() → save_chunks_to_postgres() → generate_embeddings() → store_in_milvus() → save_metadata_to_postgres()

- uploaded document: data/uploads/project.pdf
- ingestion/document_loader/pdf2md.py (output stored in data/processed)
- [optional, planned for later use] ingestion/document_loader/pdf2md_multimodal.py (output stored in data/processed)
- chunking/document_chunker.py
- embeddings/generate_embeddings.py
- vectorstore/milvus_client.py (will have the milvus specific helper codes)

sample usage for later

```python
# ingestion/document_loader/pdf2md.py
from backend.ingestion.document_loader.pdf_parser import PDFParser

parser = PDFParser(
    filename="model_validation",
    input_path="data/uploads/",
    output_root="data/processed"
)

docs = parser.parse()


# chunking/document_chunker.py
from backend.chunking.document_chunker import DocumentChunker

chunker = DocumentChunker(
    project_name="model_validation",
    data_dir="data/processed"    
)

final_split_docs = chunker.chunk()


# vectorstore/vectorize_milvusdb.py
from backend.vectorstore.vectorize_milvusdb import Vectorizer

vectorizer = Vectorizer(
    data_dir="data/processed",
    project_name="model_validation",
    db_name="prism",
    replace_collection=False,
    repalce_db=False
)

vectorizer.vectorize(split_docs=final_split_docs)
```

```sql
-- since metadata is JSONB, below would be possible
SELECT *
FROM document_chunks
WHERE metadata ->> 'page' = '15';
```

```bash
# executing db initialization from within docker
docker exec -it prism-postgres \
psql -U prism -d postgres -f /path/to/init.sql
```

### Docker Compose GPU Issue

#### `docker compose build` command returns error: `Error response from daemon: could not select device driver "nvidia" with capabilities: [[gpu]]`

**Solution:**
First check if wsl has access to GPU and nvidia driver is installed:
```bash
nvidia-smi
```
If nvidia driver is installed within wsl, check for runtime visibility
```bash
docker info | grep -i runtime
```
Its expected to see `Runtimes: nvidia runc`. If only `Runtimes: runc` is visible, toolkit is not configured/installed.
Use below command to see if toolkit is installed. If it gives no output then toolkit is not installed.
```bash
dpkg -l | grep -i nvidia-container
```
If it gives these in the output then toolkit is installed:
`nvidia-container-toolkit`, `libnvidia-container1`, `libnvidia-container-tools`

Below command can also be used. If it gives a version number then toolkit is installed. Otherwise, needs to be installed:
```bash
nvidia-ctk --version
```

If toolkit is not installed, follow below steps to get it installed and configured to be used in docker:
```bash
# STEP 1 — Remove broken NVIDIA repo file (if it was created wrong, like in my case it was created as an html file)
sudo rm /etc/apt/sources.list.d/nvidia-container-toolkit.list

# STEP 2 — Verify your Linux distribution string (used for repo compatibility checks)
. /etc/os-release
echo $ID$VERSION_ID
# Expected output example: ubuntu22.04

# STEP 3 — Add NVIDIA GPG key (modern keyring method, replaces deprecated apt-key)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
| sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
# This stores the trusted key used to verify NVIDIA packages

# STEP 4 — Add NVIDIA container toolkit repository (stable universal repo)
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
| sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
| sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
# This registers the package source with signed-by keyring validation

# STEP 5 — Update apt package index (should complete without <!doctype> errors)
sudo apt update
# Expected: NVIDIA repo fetched successfully, no source list errors

# STEP 6 — Install NVIDIA Container Toolkit (enables Docker GPU runtime)
sudo apt install -y nvidia-container-toolkit
# Installs nvidia-container-runtime and supporting libraries

# STEP 7 — Configure Docker to use NVIDIA runtime + restart service
sudo nvidia-ctk runtime configure --runtime=docker
sudo service docker restart
# Registers NVIDIA runtime inside Docker daemon

# HOW TO CONFIRM FIX — Verify repo file contains valid deb entries (not HTML)
cat /etc/apt/sources.list.d/nvidia-container-toolkit.list
# Expected: Lines starting with "deb [signed-by=...] https://nvidia.github.io/..."

# HOW TO CONFIRM FIX — Verify Docker detects NVIDIA runtime
docker info | grep -i runtime
# Expected output should include: "nvidia" alongside "runc"

# HOW TO CONFIRM FIX — Test GPU access inside a container (did not work for me as i did not have cuda toolkit installed)
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
# Expected: GPU table output showing driver, CUDA, and device utilization
```

