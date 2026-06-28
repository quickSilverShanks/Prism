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

| **Feature Area**              | **Capabilities**                                                                                                                                                                                                                                            |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **📄 Document Intelligence**  | PDF ingestion • Markdown support • Semantic chunking • Metadata-aware retrieval                                                                                                                                                                             |
| **💻 Code Intelligence**      | Repository ingestion • Multi-language support • Function-level indexing • Dependency awareness • Code explanation & walkthroughs                                                                                                                            |
| **🤖 Agentic RAG**            | Multi-step reasoning • Context-aware retrieval • Source attribution • Conversational memory • Project-wide knowledge synthesis                                                                                                                              |
| **🏠 Local-First AI**         | Ollama-powered LLMs • Local embeddings • Self-hosted Milvus • No external API dependency                                                                                                                                                                    |
| **🗺️ Future Roadmap**        | Excel & CSV support • Image understanding • Architecture diagram analysis • Automated project reviews • Code annotations & Neo4j graph visualization • Project health dashboards • Multi Agent Pipelines                                                                            |
| **🧠 Multi Agent Pipeline** | **Planner** → Intent understanding<br>**Retriever** → Knowledge source selection<br>**Code Analyst** → Code reasoning<br>**Document Analyst** → Documentation reasoning<br>**Governance** → Validation & review<br>**Report Generator** → Project summaries |

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
├── frontend/                      # Streamlit web application
│   ├── pages/                     # Individual UI pages
│   ├── components/                # Reusable UI components
│   ├── services/                  # Backend API clients
│   ├── utils/                     # Frontend helper functions
│   └── app.py                     # Streamlit entry point
│
├── backend/                       # FastAPI backend
│   ├── api/
│   │   ├── routes/                # API endpoints
│   │   └── dependencies/          # Shared API dependencies
│   │
│   ├── core/
│   │   ├── config.py              # Application configuration
│   │   ├── logging.py             # Logging setup
│   │   └── security.py            # Security utilities
│   │
│   ├── ingestion/
│   │   ├── document_loader/       # Document ingestion
│   │   ├── code_loader/           # Source code ingestion
│   │   ├── excel_loader/          # Excel ingestion
│   │   └── image_loader/          # Image/OCR ingestion
│   │
│   ├── chunking/
│   │   ├── document_chunker.py    # Document chunking
│   │   ├── code_chunker.py        # Code chunking
│   │   └── metadata_extractor.py  # Metadata extraction
│   │
│   ├── embeddings/
│   │   └── embedding_service.py   # Embedding generation
│   │
│   ├── vectorstore/
│   │   └── milvus_client.py       # Milvus operations
│   │
│   ├── database/
│   │   ├── models/                # ORM models
│   │   ├── repositories/          # Data access layer
│   │   └── postgres.py            # PostgreSQL connection
│   │
│   ├── retrieval/
│   │   ├── hybrid_search.py       # Hybrid retrieval
│   │   ├── reranker.py            # Result reranking
│   │   └── context_builder.py     # LLM context assembly
│   │
│   ├── agents/
│   │   ├── project_analyst/       # Project understanding agent
│   │   ├── code_reviewer/         # Code analysis agent
│   │   ├── document_reviewer/     # Document review agent
│   │   └── workflow_graph.py      # LangGraph workflow
│   │
│   ├── llm/
│   │   └── ollama_client.py       # Ollama client
│   │
│   └── main.py                    # FastAPI entry point
│
├── data/                          # Persistent application data
│   ├── uploads/                   # Uploaded project files
│   ├── processed/                 # Processed artifacts & chunks
│   ├── temp/                      # Temporary files
│   ├── etcd/                      # etcd persistent storage
│   ├── milvus/                    # Milvus vector data
│   ├── minio/                     # MinIO object storage
│   ├── ollama/                    # Downloaded Ollama models
│   └── postgres/                  # PostgreSQL database files
│
├── tests/                         # Unit & integration tests
│
├── Dockerfile                     # Python application image
├── docker-compose.yml             # Multi-container orchestration
├── .env                           # Environment variables
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation
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

| **Category**                 | **Example Questions**                                                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **📋 Project Understanding** | • What is the objective of this project?<br>• Summarize the project architecture.<br>• Explain the data flow.                |
| **💻 Code Analysis**         | • Explain the prediction pipeline.<br>• Where is feature engineering implemented?<br>• Which modules call this function?     |
| **🛡️ Governance Review**    | • What assumptions does this model make?<br>• Summarize validation findings.<br>• Are there any documented limitations?      |
| **🔍 Knowledge Discovery**   | • Which files discuss loss forecasting?<br>• Show all references to feature selection.<br>• Summarize business requirements. |

---

## Vision

Prism aims to become an intelligent project companion that transforms fragmented project artifacts into an interactive knowledge system.

Instead of searching through hundreds of files, users can simply ask questions and receive contextual, explainable answers grounded in project evidence.

---

<div align="center">
If you like this project, please consider giving it a ⭐️ <b>star</b> to help others discover it. 

[![GitHub Stars](https://img.shields.io/github/stars/quickSilverShanks/Prism.svg?style=social)](https://github.com/quickSilverShanks/Prism/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/quickSilverShanks/Prism.svg?style=social)](https://github.com/quickSilverShanks/Prism/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/quickSilverShanks/Prism.svg)](https://github.com/quickSilverShanks/Prism/issues)
</div>
<hr>

<div align="center">
Please note this is not open for contributions yet as basic features are still being added in, but feel free to share improvement suggestions or 🍴 <b>fork</b> it and explore the code!
</div>