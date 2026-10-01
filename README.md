# SecureRAG: Permission-Aware Multi-Tenant Document Intelligence Platform

SecureRAG is a production-oriented Retrieval-Augmented Generation (RAG) system built with **FastAPI**, **Streamlit**, **LangChain**, **FAISS**, **Hugging Face**, and **Groq (Llama 3.3 70B)**.

The platform provides multi-tenant document intelligence with strict **permission-aware retrieval**. It guarantees that users belonging to an organization (tenant) can only search and generate answers from documents authorized for their specific tenant and user role.

---

## 1. Problem Statement
Standard RAG applications store all document embeddings in a shared vector database. When a user asks a question, naive similarity search retrieves top-$k$ relevant chunks across the entire index, regardless of who uploaded the document or who is authorized to view it.

In enterprise multi-tenant environments:
- **Tenant Leakage**: Company A could accidentally retrieve confidential documents belonging to Company B.
- **Privilege Escalation**: An Engineering staff member could retrieve confidential HR salary structures or executive strategy reports.

**SecureRAG solves this by enforcing Role-Based Access Control (RBAC) and Multi-Tenant Isolation directly inside the retrieval layer**, filtering out unauthorized document chunks before they ever reach the LLM prompt.

---

## 2. Key Features

- 🛡️ **Strict Multi-Tenant Isolation**: Hard boundary preventing cross-tenant data leaks (Tenant A vs Tenant B).
- 🔑 **Role-Based Access Control (RBAC)**: Fine-grained document access permissions (`HR`, `ENGINEERING`, `FINANCE`, `ADMIN`).
- ⚡ **High-Speed Inference via Groq**: Uses Groq Llama 3.3 70B for fast grounded generation.
- 🎯 **Zero-Hallucination Fallback**: Returns `"I couldn't find this information in the authorized documents."` when no authorized context is available.
- 📌 **Page-Level Source Citations**: Every answer lists exact supporting source documents and page numbers.
- 🔍 **Debug Chunk Inspector**: Streamlit frontend tab allowing developers to preview retrieved authorized chunks and metadata.
- 📜 **Append-Only Audit Logging**: Records all upload and query actions in a local JSONL audit trail (`data/audit_logs.jsonl`).
- 💾 **Persistent Vector Index**: FAISS vector database persisted on disk (`data/faiss_index`).

---

## 3. Technology Stack

- **Backend Framework**: Python 3.14 + FastAPI
- **LLM Engine**: Groq API (`llama-3.3-70b-versatile`)
- **Embeddings**: Hugging Face `BAAI/bge-small-en-v1.5` (384-dimensional dense vectors)
- **Vector Store**: FAISS (`faiss-cpu`) with local disk persistence
- **RAG Pipeline**: LangChain (`PyPDFLoader`, `RecursiveCharacterTextSplitter`)
- **Frontend Dashboard**: Streamlit
- **Validation & Settings**: Pydantic v2 & `python-dotenv`
- **Testing**: Pytest

---

## 4. RAG Pipeline Architecture

```text
 Upload PDF (Streamlit UI)
            │
            ▼
     FastAPI Backend (/documents/upload)
            │
            ▼
   [PyPDF Document Loader] ──► Extracts page text & attaches metadata (tenant_id, allowed_roles, page)
            │
            ▼
[Recursive Character Splitter] ──► Chunks text (600 chars) retaining parent metadata
            │
            ▼
[HuggingFace BAAI/bge-small-en-v1.5] ──► 384d Dense Embeddings
            │
            ▼
    [FAISS Vector Store] ◄── Saved to disk (`data/faiss_index`)
            │
            ▼
   User Query (/chat)
            │
            ▼
[Permission-Aware Retriever] ──► Over-samples candidates & filters by tenant_id + user role
            │
            ▼
 [Authorized Chunks Only] ──► Formatted into grounded prompt template
            │
            ▼
    [Groq Llama 3.3 70B] ──► Generates factual answer with citations
            │
            ▼
[Grounded Answer + Citations] ──► Rendered on Streamlit Dashboard
```

---

## 5. Permission-Aware Retrieval Logic

Before passing candidate text chunks to the LLM, the backend `PermissionService` enforces two strict filtering rules:

1. **Tenant Isolation Check**: `chunk.metadata.tenant_id == user.tenant_id`. Chunks from other tenants are immediately dropped.
2. **Role Authorization Check**: User passes if `user.role == 'ADMIN'` OR `user.role in chunk.metadata.allowed_roles`.

> **Security Guarantee**: Filtering occurs in the backend service layer *prior* to prompt assembly. Unauthorized chunks are never exposed to the LLM.

---

## 6. Project Structure

```text
SecureRAG/
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Environment & settings configuration
│   ├── routes/
│   │   ├── health.py            # /health monitoring endpoint
│   │   ├── documents.py         # /documents/upload & /documents
│   │   ├── chat.py              # /chat RAG query endpoint
│   │   └── users.py             # /users demo identity endpoints
│   ├── schemas/
│   │   ├── document.py          # Pydantic document models
│   │   ├── chat.py              # Pydantic chat request/response models
│   │   └── user.py              # Pydantic user context & demo users
│   ├── services/
│   │   ├── document_service.py  # PDF processing & index manager
│   │   ├── embedding_service.py # Hugging Face model wrapper
│   │   ├── retrieval_service.py # Prompt context builder & citation extractor
│   │   ├── llm_service.py       # Groq API client with Llama fallback
│   │   ├── permission_service.py# Security & RBAC evaluation engine
│   │   └── audit_service.py     # JSONL audit logger
│   ├── rag/
│   │   ├── ingestion.py         # PDF text extraction & metadata attachment
│   │   ├── chunking.py          # RecursiveCharacterTextSplitter wrapper
│   │   └── retriever.py         # Permission-filtered similarity search
│   └── vectorstore/
│       └── faiss_store.py       # FAISS index persistence & search
├── frontend/
│   └── app.py                   # Streamlit UI dashboard
├── tests/
│   ├── test_health.py           # API health tests
│   ├── test_phase1.py           # Ingestion & FAISS pipeline tests
│   ├── test_phase2.py           # Prompting & fallback tests
│   ├── test_permission.py       # Role-based access control tests
│   └── test_tenant_isolation.py # Multi-tenant boundary tests
├── data/                        # Local persistent files (ignored by git)
│   ├── faiss_index/             # Persisted FAISS vector database files
│   ├── uploads/                 # Uploaded PDF files
│   └── audit_logs.jsonl         # Append-only audit log
├── .env.example                 # Environment variable template
├── requirements.txt             # Python project dependencies
└── README.md                    # System documentation
```

---

## 7. Pre-Configured Demo Users

| User ID | Name | Tenant ID | Role | Access Scope |
| :--- | :--- | :--- | :--- | :--- |
| `rahul` | Rahul | `company_a` | `HR` | Company A documents marked `HR` or `ADMIN` |
| `amit` | Amit | `company_a` | `ENGINEERING` | Company A documents marked `ENGINEERING` or `ADMIN` |
| `admin_a` | Admin A | `company_a` | `ADMIN` | All Company A documents |
| `neha` | Neha | `company_b` | `HR` | Company B documents marked `HR` or `ADMIN` |
| `admin_b` | Admin B | `company_b` | `ADMIN` | All Company B documents |

---

## 8. Setup & Installation Instructions

### Prerequisites
- Python 3.10+
- Groq API Key (Sign up at [console.groq.com](https://console.groq.com/))

### Step 1: Clone & Navigate to Project
```bash
cd d:\SecureRAG
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` and set your Groq API key:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5
VECTOR_STORE_DIR=data/faiss_index
DEFAULT_TOP_K=4
```

### Step 3: Install Dependencies
```bash
python -m pip install -r requirements.txt
```

---

## 9. How to Run the Application

### Running the Backend (FastAPI)
Start the FastAPI server on port 8000:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Swagger UI Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Running the Frontend (Streamlit)
In a separate terminal window, launch the Streamlit dashboard:
```bash
python -m streamlit run frontend/app.py
```
- Open your browser at [http://localhost:8501](http://localhost:8501)

---

## 10. API Endpoints Reference

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API status info |
| `GET` | `/health` | Backend & vector store health check |
| `GET` | `/users` | List all available demo user profiles |
| `GET` | `/users/{user_id}` | Get identity context for a specific user |
| `POST` | `/documents/upload` | Upload PDF file with metadata and index into FAISS |
| `GET` | `/documents` | List indexed documents accessible to current user |
| `POST` | `/chat` | Query RAG pipeline with permission-aware filtering |

---

## 11. Running Automated Tests

Run the full pytest suite (10 automated unit & integration tests):
```bash
python -m pytest tests/ -v
```

Tests cover:
- Health check endpoints
- PDF loading, chunking, and metadata propagation
- Embeddings and FAISS local persistence
- Grounded prompt context formatting & zero-hallucination fallback
- Role-based access control (RBAC) filtering
- Strict multi-tenant isolation (Tenant A cannot retrieve Tenant B data)

---

## 12. Security & Compliance Design

1. **Secrets Management**: Secrets are managed via `.env` and excluded from version control via `.gitignore`.
2. **Zero-Hallucination System Prompt**: Enforces strict boundaries preventing the LLM from synthesizing outside facts.
3. **Defense in Depth**: Permissions are checked in `backend/services/permission_service.py` before prompt construction, not in client-side code.
4. **Audit Trail**: Append-only log file (`data/audit_logs.jsonl`) captures every upload, query, and user interaction.

---

## 13. Future Improvements

- PostgreSQL + `pgvector` or Qdrant integration for cloud multi-node vector deployment.
- OAuth2 / JWT authentication integration.
- Document level re-ranking using Hugging Face Cross-Encoders (`bge-reranker-small`).
