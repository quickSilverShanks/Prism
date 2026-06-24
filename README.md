# Prism

> Agentic RAG for Project Intelligence

Prism is an open-source platform that helps teams understand complex machine learning and software projects through conversational AI.

By ingesting project documentation, source code repositories, validation reports, architecture documents, spreadsheets, and other artifacts, Prism creates a unified knowledge layer that enables users to explore, review, and understand projects through natural language conversations.

Built with local-first AI components, Prism leverages Ollama-powered LLMs, vector search, and agentic workflows to provide contextual answers grounded in project-specific knowledge.

---

## Why Prism?

> [!NOTE]
> The primary usefulness of this project lies in the fact that developers sometimes have to work on projects with massive documentation, codebase and supporting artifacts with no context other than the primary purpose of that project. Its basically the job description of every Model Review Management team in BFSI industry.

Large projects often contain information scattered across:

* Technical documentation
* Source code repositories
* Validation reports
* Model development artifacts
* Architecture diagrams
* Excel spreadsheets
* Operational runbooks

Understanding how these artifacts connect requires significant onboarding effort and domain expertise.

Prism addresses this challenge by creating a conversational interface that enables users to:

* Understand project objectives
* Explore business logic
* Analyze source code
* Review model assumptions
* Investigate dependencies
* Discover implementation details
* Generate project summaries
* Accelerate governance and review workflows

---

## Key Features

### Document Intelligence

* PDF ingestion
* Markdown support
* Semantic chunking
* Metadata-aware retrieval

### Code Intelligence

* Repository ingestion
* Multi-language source code support
* Function-level indexing
* Dependency awareness
* Code explanation and walkthroughs

### Agentic RAG

* Multi-step reasoning workflows
* Context-aware retrieval
* Source attribution
* Conversational memory
* Project-wide knowledge synthesis

### Local-First AI

* Ollama-powered LLMs
* Local embeddings
* Self-hosted vector database
* No external API dependency required

### Future Roadmap

* Excel and CSV intelligence
* Image understanding
* Architecture diagram analysis
* Automated project reviews
* Code Annotations and neo4j graph visualization
* Multi-agent pipelines
  * Planner Agent → understands user intent
  * Retriever Agent → decides which knowledge sources to query
  * Code Analyst Agent → code reasoning
  * Document Analyst Agent → documentation reasoning
  * Governance Agent → validation/model review
  * Report Generator Agent → creates project summaries
* Project health dashboards

---

## Planned Architecture

```text
                    ┌─────────────────────┐
                    │     Streamlit UI    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI Backend  │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼

      ┌───────────┐     ┌─────────────┐    ┌───────────┐
      │ PostgreSQL│     │   Milvus    │    │  Ollama   │
      │ Metadata  │     │ Vector Store│    │  Models   │
      └───────────┘     └─────────────┘    └───────────┘

             ▲                ▲
             │                │
             ▼                ▼

      ┌────────────────────────────────┐
      │  Ingestion & Processing Layer  │
      └────────────────────────────────┘
```

---

## Technology Stack

| Layer               | Technology     |
| ------------------- | -------------- |
| Frontend            | Streamlit      |
| Backend             | FastAPI        |
| LLM Orchestration   | LangChain      |
| Agent Framework     | LangGraph      |
| LLM Serving         | Ollama         |
| Vector Database     | Milvus         |
| Relational Database | PostgreSQL     |
| Containerization    | Docker         |
| Deployment          | Docker Compose |

---

## Project Structure

```text
prism/
│
├── frontend/
│   ├── pages/
│   ├── components/
│   ├── services/
│   ├── utils/
│   └── app.py
│
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   └── dependencies/
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   │
│   ├── ingestion/
│   │   ├── document_loader/
│   │   ├── code_loader/
│   │   ├── excel_loader/
│   │   └── image_loader/
│   │
│   ├── chunking/
│   │   ├── document_chunker.py
│   │   ├── code_chunker.py
│   │   └── metadata_extractor.py
│   │
│   ├── embeddings/
│   │   └── embedding_service.py
│   │
│   ├── vectorstore/
│   │   └── milvus_client.py
│   │
│   ├── database/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── postgres.py
│   │
│   ├── retrieval/
│   │   ├── hybrid_search.py
│   │   ├── reranker.py
│   │   └── context_builder.py
│   │
│   ├── agents/
│   │   ├── project_analyst/
│   │   ├── code_reviewer/
│   │   ├── document_reviewer/
│   │   └── workflow_graph.py
│   │
│   ├── llm/
│   │   └── ollama_client.py
│   │
│   └── main.py
│
├── data/
│   ├── uploads/
│   ├── processed/
│   └── temp/
│
├── tests/
│
|── Dockerfile
├── docker-compose.yml
├── .env
├── requirements.txt
└── README.md
```

---

## Getting Started

### Clone Repository

```bash
git clone https://github.com/quickSilverShanks/Prism.git

cd Prism
```

### Start Services

```bash
docker compose up --build
```

### Access Applications

```text
Streamlit UI    : http://localhost:8501

FastAPI Docs    : http://localhost:8000/docs

Milvus          : localhost:19530

PostgreSQL      : localhost:5432

Ollama          : localhost:11434
```

---

## Example Questions

### Project Understanding

* What is the objective of this project?
* Summarize the project architecture.
* Explain the data flow.

### Code Analysis

* Explain the prediction pipeline.
* Where is feature engineering implemented?
* Which modules call this function?

### Governance Review

* What assumptions does this model make?
* Summarize validation findings.
* Are there any documented limitations?

### Knowledge Discovery

* Which files discuss loss forecasting?
* Show all references to feature selection.
* Summarize business requirements.

---

## Vision

Prism aims to become an intelligent project companion that transforms fragmented project artifacts into an interactive knowledge system.

Instead of searching through hundreds of files, users can simply ask questions and receive contextual, explainable answers grounded in project evidence.
