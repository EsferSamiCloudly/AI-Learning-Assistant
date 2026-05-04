# 🎓 AI Learning Assistant v2.0

A production-grade educational platform powered by **LLaMA 3.3 70B** (via Groq), **LangGraph**, **pgvector**, and a modern **Next.js 15** frontend. Upload PDFs, chat with your documents, generate questions, write essays, summarize content, and evaluate answers — all with built-in AI safety guardrails.

---

## 📚 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Environment Variables](#-environment-variables)
- [Database Setup](#-database-setup)
- [Backend Setup](#-backend-setup)
- [MCP Server Setup](#-mcp-server-setup)
- [Frontend Setup](#-frontend-setup)
- [Running the Project](#-running-the-project)
- [Features](#-features)
- [API Reference](#-api-reference)
- [AI Guardrails](#-ai-guardrails)
- [Authentication System](#-authentication-system)
- [PDF Pipeline](#-pdf-pipeline)
- [Vector Search](#-vector-search)
- [Database Schema](#-database-schema)

---

## 🌟 Overview

The AI Learning Assistant is a full-stack educational platform split into three independently runnable services:

| Service | Port | Description |
|---|---|---|
| **Backend** | `8000` | FastAPI REST API — auth, users, chat, history, orchestration |
| **MCP Server** | `8001` | AI tool server — LangGraph graphs, PDF embedding, vector search |
| **Frontend** | `3000` | Next.js 15 — dark-themed UI with all features |

The communication is strictly **Frontend → Backend → MCP Server → PostgreSQL**. The MCP server is an internal service never exposed publicly.

---

## 🏗️ Architecture

```
┌─────────────────┐        ┌─────────────────────┐        ┌──────────────────────┐
│   Next.js 15    │  HTTP  │   FastAPI Backend    │  HTTP  │  FastMCP + LangGraph │
│   (Port 3000)   │───────▶│     (Port 8000)      │───────▶│    (Port 8001)       │
│                 │        │                      │        │                      │
│  TanStack Query │        │  JWT Auth + Redis    │        │  LLaMA 3.3 70B Groq  │
│  Zustand Store  │        │  Alembic Migrations  │        │  SentenceTransformers│
│  Tailwind CSS   │        │  slowapi Rate Limit  │        │  pgvector Embeddings │
└─────────────────┘        └──────────┬───────────┘        └──────────┬───────────┘
                                      │                               │
                           ┌──────────▼───────────┐                   │
                           │   PostgreSQL 16       │◀──────────────────┘
                           │   + pgvector ext.     │
                           │   3 schemas:          │
                           │   auth / app / vectors│
                           └──────────────────────┘
                                      │
                           ┌──────────▼───────────┐
                           │       Redis           │
                           │  JWT Blacklist        │
                           │  Rate Limit Counters  │
                           │  Refresh Token Cache  │
                           └──────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend (`/backend`)

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | ≥0.115.0 | Async REST framework |
| `uvicorn[standard]` | ≥0.32.0 | ASGI server |
| `sqlalchemy[asyncio]` | ≥2.0.0 | Async ORM |
| `asyncpg` | ≥0.30.0 | PostgreSQL async driver |
| `alembic` | ≥1.14.0 | Database migrations |
| `pydantic` | ≥2.9.0 | Data validation |
| `pydantic-settings` | ≥2.6.0 | Config management |
| `python-jose[cryptography]` | ≥3.3.0 | JWT tokens |
| `passlib[bcrypt]` | ≥1.7.4 | Password hashing |
| `bcrypt` | ==4.0.1 | Pinned for compatibility |
| `httpx` | ≥0.28.0 | Async HTTP client (calls MCP) |
| `redis` | ≥5.2.0 | Token blacklist + rate limiting |
| `slowapi` | ≥0.1.9 | Rate limiting middleware |
| `python-multipart` | ≥0.0.12 | File upload parsing |
| `email-validator` | ≥2.2.0 | Email validation |

### MCP Server (`/mcp-server`)

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | ≥0.115.0 | HTTP wrapper for MCP tools |
| `fastmcp` | ≥2.0.0 | MCP server framework |
| `langgraph` | ≥0.2.0 | AI graph orchestration |
| `langchain` | ≥0.3.0 | LLM framework |
| `langchain-groq` | ≥0.2.0 | Groq API integration |
| `langchain-text-splitters` | ≥0.3.0 | Text chunking |
| `sentence-transformers` | ≥3.3.0 | `all-MiniLM-L6-v2` embeddings |
| `asyncpg` | ≥0.30.0 | pgvector bulk inserts |
| `pgvector` | ≥0.3.0 | Vector type codec |
| `pypdf` | ≥5.1.0 | In-memory PDF parsing |
| `numpy` | ≥2.1.0 | float32 embedding arrays |
| `pydantic-settings` | ≥2.6.0 | Settings management |

### Frontend (`/frontend`)

| Package | Version | Purpose |
|---|---|---|
| `next` | ^15.0.0 | React framework (App Router) |
| `react` | ^19.0.0 | UI library |
| `@tanstack/react-query` | ^5.0.0 | Server state management |
| `zustand` | ^5.0.0 | Client state (auth tokens) |
| `axios` | ^1.7.0 | HTTP client |
| `lucide-react` | ^0.460.0 | Icon library |
| `react-markdown` | ^9.0.0 | Markdown rendering |
| `react-hook-form` | ^7.53.0 | Form management |
| `zod` | ^3.23.0 | Schema validation |
| `tailwindcss` | ^3.4.0 | Utility-first CSS |
| `jose` | ^5.9.0 | JWT handling |
| `clsx` / `tailwind-merge` | latest | Conditional classnames |

---

## 📁 Project Structure

```
AI-Learning_system/
├── backend/
│   ├── src/
│   │   ├── models/
│   │   │   ├── db/              # SQLAlchemy ORM models
│   │   │   │   ├── user.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── document.py
│   │   │   │   └── outputs.py
│   │   │   └── schemas/         # Pydantic request/response schemas
│   │   ├── routers/             # FastAPI route handlers
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   ├── essay.py
│   │   │   ├── summarize.py
│   │   │   ├── questions.py
│   │   │   ├── evaluate.py
│   │   │   └── tasks.py
│   │   ├── services/
│   │   │   ├── auth_service.py  # bcrypt, JWT, refresh tokens
│   │   │   └── mcp_client.py   # httpx calls to MCP server
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py     # get_current_user
│   │   ├── main.py
│   │   └── redis_client.py
│   ├── alembic/
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── run.py
│
├── mcp-server/
│   ├── src/
│   │   ├── graphs/
│   │   │   ├── chatbot_graph.py
│   │   │   ├── essay_graph.py
│   │   │   ├── summarizer_graph.py
│   │   │   ├── question_graph.py
│   │   │   └── evaluator_graph.py
│   │   ├── utils/
│   │   │   ├── pdf_parser.py
│   │   │   ├── text_splitter.py
│   │   │   └── vector_store.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── embeddings.py
│   │   ├── groq_client.py
│   │   ├── guardrails.py
│   │   ├── http_api.py
│   │   └── prompt_templates.py
│   ├── pyproject.toml
│   └── run.py
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── (auth)/
    │   │   │   ├── login/page.tsx
    │   │   │   └── register/page.tsx
    │   │   └── (dashboard)/
    │   │       ├── layout.tsx        # Auth guard
    │   │       ├── chat/
    │   │       │   ├── page.tsx      # PDF/general mode
    │   │       │   └── [sessionId]/page.tsx
    │   │       ├── essay/page.tsx
    │   │       ├── summarize/page.tsx
    │   │       ├── questions/page.tsx
    │   │       ├── evaluate/page.tsx
    │   │       └── profile/page.tsx
    │   ├── components/
    │   │   ├── chat/
    │   │   │   ├── ChatWindow.tsx
    │   │   │   └── ChatHistorySidebar.tsx
    │   │   ├── forms/
    │   │   │   ├── EssayForm.tsx
    │   │   │   ├── SummarizeForm.tsx
    │   │   │   ├── QuestionsForm.tsx
    │   │   │   └── EvaluateForm.tsx
    │   │   └── layout/
    │   │       └── Sidebar.tsx
    │   ├── lib/
    │   │   ├── api.ts             # All axios API calls
    │   │   └── types.ts           # TypeScript interfaces
    │   └── store/
    │       ├── authStore.ts       # Zustand — access token in memory
    │       └── chatStore.ts       # Zustand — active session
    ├── package.json
    └── next.config.ts
```

---

## ✅ Prerequisites

Make sure the following are installed on your system:

- 🐍 **Python 3.12** — `python3 --version`
- 📦 **uv** package manager — [install guide](https://docs.astral.sh/uv/getting-started/installation/)
- 🟢 **Node.js 22 LTS** — `node --version`
- 🐘 **PostgreSQL 16** with **pgvector** extension
- 🔴 **Redis** running on port 6379

### Install PostgreSQL 16 + pgvector (Ubuntu 24)

```bash
sudo apt update
sudo apt install postgresql-16 postgresql-16-pgvector
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Install Redis (Ubuntu 24)

```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Verify Redis is running
redis-cli ping  # should return PONG
```

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env  # or restart terminal
```

---

## 🔐 Environment Variables

### `backend/.env`

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/ai_learning

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379/0

# MCP Server
MCP_SERVER_URL=http://localhost:8001

# App
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000
```

### `mcp-server/.env`

```env
# Database
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/ai_learning

# Groq API — get your key at console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile

# Redis
REDIS_URL=redis://localhost:6379/0

# Optional: LangSmith tracing
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your-langsmith-key
```

### `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> ⚠️ **Special characters in DB password:** If your password contains `#`, `@`, `%`, etc., URL-encode them in `DATABASE_URL`. For example `p@ss#word` → `p%40ss%23word`. The MCP server applies `urllib.parse.quote()` automatically for asyncpg connections.

---

## 🗄️ Database Setup

### 1. Create the database and user

```bash
sudo -u postgres psql << 'EOF'
CREATE USER appuser WITH PASSWORD 'yourpassword';
CREATE DATABASE ai_learning OWNER appuser;
GRANT ALL PRIVILEGES ON DATABASE ai_learning TO appuser;
EOF

# Enable extensions
sudo -u postgres psql -d ai_learning -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d ai_learning -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### 2. Run Alembic migrations

```bash
cd backend
uv venv --python 3.12
uv sync
uv run alembic upgrade head
```

This creates all three schemas and nine tables in a single transaction:

| Schema | Tables |
|---|---|
| `auth` | `users`, `refresh_tokens` |
| `app` | `documents`, `chat_sessions`, `chat_messages`, `essay_outputs`, `question_sets`, `evaluation_results`, `summarization_outputs` |
| `vectors` | `document_chunks` — with `vector(384)` column and IVFFlat cosine index |

### Useful database commands

```bash
# Check migration status
uv run alembic current

# View migration history
uv run alembic history

# Roll back one migration
uv run alembic downgrade -1

# Verify tables were created
sudo -u postgres psql -d ai_learning -c "\dt auth.*"
sudo -u postgres psql -d ai_learning -c "\dt app.*"
sudo -u postgres psql -d ai_learning -c "\dt vectors.*"
```

---

## 🔧 Backend Setup

```bash
cd backend

# Create virtual environment with Python 3.12
uv venv --python 3.12

# Install all dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET_KEY, etc.

# Run database migrations (first time only)
uv run alembic upgrade head

# Start the development server
uv run python run.py
```

✅ Backend is running at **http://localhost:8000**
📖 Interactive API docs at **http://localhost:8000/docs**

---

## 🤖 MCP Server Setup

```bash
cd mcp-server

# Create virtual environment with Python 3.12
uv venv --python 3.12

# Install dependencies
# Note: sentence-transformers downloads ~500MB of model weights on first run
uv sync

# Configure environment
cp .env.example .env
# Edit .env — especially set your GROQ_API_KEY

# Start the server
uv run python run.py
```

✅ MCP Server is running at **http://localhost:8001**

> 💡 **First run note:** `all-MiniLM-L6-v2` (~90MB) is downloaded from HuggingFace and cached locally. Subsequent starts use the cached model. The `HF_TOKEN` warning is cosmetic — you can safely ignore it.

---

## 🎨 Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local — set NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

✅ Frontend is running at **http://localhost:3000**

### Production build

```bash
npm run build
npm start
```

---

## 🚀 Running the Project

Open **three terminals** and run each service:

```bash
# Terminal 1 — Backend API
cd ~/AI-Learning_system/backend
uv run python run.py

# Terminal 2 — MCP AI Server
cd ~/AI-Learning_system/mcp-server
uv run python run.py

# Terminal 3 — Frontend
cd ~/AI-Learning_system/frontend
npm run dev
```

Then open **http://localhost:3000** in your browser. Register a new account and start learning! 🎉

---

## ✨ Features

### 💬 Educational Chatbot
- **General mode** — Ask any educational question, powered by LLaMA 3.3 70B
- **PDF mode** — Upload a PDF, then chat with your document
  - Semantic search retrieves top 8 relevant chunks via pgvector cosine similarity
  - Responses include **page number citations** (`[Page N]: content`)
  - Full conversation history persisted per session
  - Session sidebar with titles — click any session to resume
- Guardrail blocks harmful questions with an inline friendly message

### 📄 PDF Upload & Embedding
- Upload any PDF via drag-and-drop or file picker
- Processed entirely **in memory** — files never saved to disk
- Pages split into 400-char overlapping chunks (100-char overlap)
- Each chunk embedded with `all-MiniLM-L6-v2` (384 dimensions)
- Stored in PostgreSQL via pgvector with IVFFlat index
- Frontend polls embed status every 2 seconds → `Chat` button enables when `done`

### ✍️ Essay Writer
- Choose **topic**, **tone** (academic/casual/professional), **length** (short/medium/long)
- Optional **outline generation** before writing full essay
- Results rendered with **Markdown formatting**
- **History sidebar** — click any past essay to view it, hover to delete
- New essay button takes you back to the form

### 📝 Summarizer
- **Text mode** — paste any content to summarize
- **Document mode** — select any of your uploaded PDFs
- Two output modes: `short` (2–3 sentences) or `bullets` (6–8 bullet points)
- Multi-chunk pipeline: chunks → individual summaries → intelligent merge
- **History sidebar** with past summaries

### ❓ Question Generator
- **Text mode** — paste study material, add optional **domain hint** (e.g., "Biology")
- **Document mode** — generate questions directly from an uploaded PDF (no domain needed)
- Difficulty: **easy**, **medium**, or **hard**
- Count: 1–20 questions
- Expandable cards — click to reveal expected answer
- **History sidebar** showing difficulty and count per set

### 📊 Answer Evaluator
- **Single mode** — one question + student answer + optional reference answer
- **Exam mode** — multiple Q&A pairs evaluated together
- **Three reference sources:**
  - **None** — LLM uses general knowledge
  - **Paste text** — provide your own reference material
  - **From document** — use a previously uploaded PDF as reference
- Scores 0–10 with constructive feedback per answer
- Color-coded scores: 🟢 ≥7, 🟡 ≥4, 🔴 <4
- Total score displayed as average across all pairs
- **History sidebar** with past evaluations

### 👤 User Profile
- View full name and email
- **Update password** — requires current password verification
- Client-side validation: 6+ characters, confirmation match
- Success/error messages inline

---

## 📡 API Reference

### 🔑 Authentication

| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| `POST` | `/auth/register` | 10/min | Register new user, returns access token |
| `POST` | `/auth/login` | 5/min | Login, returns access token + refresh cookie |
| `POST` | `/auth/refresh` | — | Rotate refresh token |
| `POST` | `/auth/logout` | — | Blacklist token, clear refresh cookie |

### 👤 Users

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me` | Get current user profile |
| `PATCH` | `/users/me` | Update full name |
| `PATCH` | `/users/me/password` | Update password (verifies current first) |

### 📁 Documents & Tasks

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/documents/upload` | Upload PDF → async embedding via BackgroundTask |
| `GET` | `/documents/` | List user's documents with embed_status |
| `GET` | `/tasks/{document_id}` | Poll embedding status → `PENDING/STARTED/SUCCESS/FAILURE` |

### 💬 Chat

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/chat/sessions` | List all sessions ordered by last activity |
| `POST` | `/chat/sessions` | Create session (validates embed_status for PDF mode) |
| `GET` | `/chat/sessions/{id}` | Get session with full message history |
| `DELETE` | `/chat/sessions/{id}` | Delete session and all messages |
| `POST` | `/chat/sessions/{id}/message` | Send message, get AI response, persist both |

### ✍️ Essay (all protected)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/essay/generate` | Generate essay → saved to history |
| `GET` | `/essay/history` | List past essays (desc by date) |
| `GET` | `/essay/history/{id}` | Get specific essay |
| `DELETE` | `/essay/history/{id}` | Delete essay |

### 📝 Summarize

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/summarize/text` | Summarize pasted text |
| `POST` | `/summarize/document` | Summarize uploaded PDF |
| `GET` | `/summarize/history` | List past summaries |
| `GET` | `/summarize/history/{id}` | Get specific summary |
| `DELETE` | `/summarize/history/{id}` | Delete summary |

### ❓ Questions

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/questions/generate` | Generate from text or document |
| `GET` | `/questions/history` | List past question sets |
| `GET` | `/questions/history/{id}` | Get specific question set |
| `DELETE` | `/questions/history/{id}` | Delete question set |

### 📊 Evaluate

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/evaluate/answers` | Evaluate answers (optional doc reference) |
| `GET` | `/evaluate/history` | List past evaluations |
| `GET` | `/evaluate/history/{id}` | Get specific evaluation |
| `DELETE` | `/evaluate/history/{id}` | Delete evaluation |

> 📖 Full interactive Swagger UI at **http://localhost:8000/docs**

---

## 🛡️ AI Guardrails

Every AI feature has **two-layer input safety checking** before any LLM call:

### Layer 1 — Keyword Blocklist ⚡ (fast, zero cost)

Instantly rejects inputs containing hardcoded dangerous patterns:

```python
BLOCKED_PATTERNS = [
    "how to make bomb", "how to make weapon", "how to kill",
    "child pornography", "child abuse", "sexual abuse",
    "how to hack", "how to synthesize drugs", "drug synthesis",
    "suicide method", "self harm method", "how to hurt",
    "terrorist", "extremist attack", "mass shooting",
]
```

### Layer 2 — LLM Safety Classifier 🧠 (intelligent)

Sends the first 2000 chars to Groq with a structured safety prompt. Returns `{"safe": bool, "reason": "..."}`.

**Blocked if input:**
- Requests violence, weapons, or harm instructions
- Contains hate speech, racism, or discrimination
- Contains sexually explicit content
- Requests malware or illegal activity
- Has no plausible educational purpose

**Allowed (even if controversial):**
- History of wars, genocides, political movements
- Drug policy debates, capital punishment arguments
- Any legitimate academic or research topic

### Response Behavior Per Feature

| Feature | When Blocked Response |
|---|---|
| **Chatbot** | Inline chat message: `"I cannot process this request: {reason}"` |
| **Essay Writer** | Essay field: `"⚠️ I cannot write this essay: {reason}. Please choose an appropriate educational topic."` |
| **Summarizer** | Summary field: `"⚠️ Content blocked: {reason}. Please provide appropriate educational content."` |
| **Question Generator** | Returns one question card: `"⚠️ Content blocked: {reason}."` |
| **Evaluator** | Returns one result with score 0/10 and blocked feedback message |

> ✅ **Fail open policy:** If the guardrail LLM call itself fails (network error, timeout), the request is allowed through. This prevents safety checks from breaking the service during Groq outages.

---

## 🔑 Authentication System

### Dual-Token Pattern

```
POST /auth/login
    │
    ├── Returns: Access Token (JWT, 15 min, in response body)
    └── Sets:    Refresh Token (64-byte random, 7 days, httpOnly cookie)
                  ↓
              SHA-256 hash stored in DB (auth.refresh_tokens)
              Raw token stored as Redis key with TTL

Every protected request:
    Authorization: Bearer <access_token>
              ↓
    get_current_user dependency:
      1. Decode JWT → extract jti, sub, email
      2. Check Redis: EXISTS blacklist:jti:{jti}  → 401 if found
      3. Load User from DB by sub (UUID)
      4. Return User object

POST /auth/refresh:
    Read httpOnly cookie → hash it → look up in DB
    Delete old refresh token row + Redis key
    Issue new access token + new refresh token (rotation)

POST /auth/logout:
    Extract jti from access token
    SET blacklist:jti:{jti} = "1" EX {remaining_ttl_seconds}
    DELETE refresh token from DB
    DELETE refresh token from Redis
    Clear cookie
```

### Security Properties

| Property | Implementation |
|---|---|
| Password storage | bcrypt hash via passlib (bcrypt==4.0.1 pinned) |
| Refresh token storage | SHA-256 hash only — raw token never in DB |
| Token invalidation | Redis blacklist on jti — instant logout |
| Token rotation | Old refresh token deleted on every refresh |
| Brute force protection | slowapi: 5/min login, 10/min register |
| Data isolation | Every query filtered by `user_id` |
| CORS | Explicit allowed origins list |

---

## 📄 PDF Pipeline

```
User uploads PDF
       │
       ▼
Backend: await file.read() → bytes in memory
       │
       ▼
Base64 encode bytes
       │
       ▼
INSERT INTO app.documents (embed_status='pending')
       │
       ▼
await db.commit()  ← CRITICAL: must commit before BackgroundTask
       │
       ▼
BackgroundTask → POST http://localhost:8001/embed
       │
       └─────────────── MCP Server /embed ───────────────────┐
                                                             │
       base64 decode → io.BytesIO → pypdf.PdfReader         │
                │                                            │
       extract text per page [{page_number, content}]       │
                │                                            │
       RecursiveCharacterTextSplitter                        │
         chunk_size=400, chunk_overlap=100                   │
         skips empty pages and empty chunks                  │
                │                                            │
       SentenceTransformer.encode(texts, batch_size=32)      │
         model: all-MiniLM-L6-v2                             │
         output: numpy array shape (N, 384) float32          │
                │                                            │
       asyncpg: SET search_path TO app, auth, vectors        │
       verify document EXISTS (::uuid cast)                  │
       executemany → INSERT INTO vectors.document_chunks     │
       UPDATE app.documents SET embed_status='done'          │
                                                             │
       └────────────────────────────────────────────────────┘
       │
       ▼
Frontend polls GET /tasks/{document_id} every 2 seconds
  embed_status mapping:
    'done'       → 'SUCCESS'
    'processing' → 'STARTED'
    'pending'    → 'PENDING'
    'failed'     → 'FAILURE'
       │
       ▼
  Status = SUCCESS → Chat button enabled
```

---

## 🔍 Vector Search

### Embedding Model
- **Name:** `all-MiniLM-L6-v2`
- **Library:** SentenceTransformers
- **Dimensions:** 384
- **Type:** float32 numpy array
- **Cached:** `~/.cache/huggingface/` after first download (~90MB)

### pgvector Setup
```sql
-- Extension (enabled in migration)
CREATE EXTENSION IF NOT EXISTS vector;

-- Column type
embedding vector(384)

-- IVFFlat index for approximate nearest-neighbor search
CREATE INDEX ON vectors.document_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

### Similarity Search Query
```sql
SELECT content, page_number,
       1 - (embedding <=> $1::vector) AS similarity
FROM vectors.document_chunks
WHERE document_id = $2::uuid
  AND user_id     = $3::uuid
ORDER BY embedding <=> $1::vector
LIMIT 8;
```

The `<=>` operator is pgvector's **cosine distance**. Results are strictly scoped to the user's own document — cross-user access is architecturally impossible.

### Why IVFFlat?
Without an index, every query scans all rows sequentially. IVFFlat divides the vector space into `lists=100` clusters. At query time only the closest clusters are searched, making retrieval sub-millisecond even for large document collections.

---

## 🗃️ Database Schema

### `auth` Schema

```sql
-- User accounts
auth.users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,          -- bcrypt hash, never plaintext
  full_name     TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
)

-- Refresh token store (hashed)
auth.refresh_tokens (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users ON DELETE CASCADE,
  token_hash  TEXT UNIQUE NOT NULL,     -- SHA-256, raw token never stored
  expires_at  TIMESTAMPTZ NOT NULL      -- checked on every refresh attempt
)
```

### `app` Schema

```sql
-- Uploaded PDF metadata (no file content stored)
app.documents (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES auth.users ON DELETE CASCADE,
  filename     TEXT NOT NULL,
  page_count   INT,
  embed_status TEXT DEFAULT 'pending',  -- pending|processing|done|failed
  created_at   TIMESTAMPTZ DEFAULT NOW()
)

-- Chat conversation sessions
app.chat_sessions (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users ON DELETE CASCADE,
  title       TEXT,                     -- filename for PDF, first 60 chars for general
  document_id UUID REFERENCES app.documents ON DELETE SET NULL,
  mode        TEXT DEFAULT 'general',   -- 'general' | 'pdf'
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
)

-- Individual messages within sessions
app.chat_messages (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES app.chat_sessions ON DELETE CASCADE,
  role       TEXT CHECK (role IN ('user', 'assistant')),
  content    TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
)

-- Generated essays
app.essay_outputs (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID REFERENCES auth.users ON DELETE CASCADE,
  topic      TEXT NOT NULL,
  tone       TEXT,
  length     TEXT,
  content    TEXT NOT NULL,            -- full markdown essay
  created_at TIMESTAMPTZ DEFAULT NOW()
)

-- Generated question sets
app.question_sets (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users ON DELETE CASCADE,
  difficulty  TEXT,
  domain      TEXT,                    -- null when generated from document
  count       INT,
  questions   JSONB NOT NULL,          -- [{question, expected_answer, difficulty}]
  source_text TEXT,                    -- first 500 chars of source for reference
  created_at  TIMESTAMPTZ DEFAULT NOW()
)

-- Answer evaluation results
app.evaluation_results (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users ON DELETE CASCADE,
  mode        TEXT,                    -- 'single' | 'exam'
  results     JSONB NOT NULL,          -- [{question, student_answer, score, feedback}]
  total_score NUMERIC(5,2),            -- average 0.00–10.00
  created_at  TIMESTAMPTZ DEFAULT NOW()
)

-- Summarization outputs
app.summarization_outputs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users ON DELETE CASCADE,
  source_type TEXT,                    -- 'text' | 'pdf'
  mode        TEXT,                    -- 'short' | 'bullets'
  document_id UUID REFERENCES app.documents ON DELETE SET NULL,
  content     TEXT NOT NULL,           -- final merged summary
  created_at  TIMESTAMPTZ DEFAULT NOW()
)
```

### `vectors` Schema

```sql
-- PDF text chunks with embeddings (the vector database)
vectors.document_chunks (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES app.documents ON DELETE CASCADE,
  user_id     UUID REFERENCES auth.users ON DELETE CASCADE,
  chunk_index INT NOT NULL,            -- sequential order within document
  page_number INT,                     -- source PDF page (returned as citation)
  content     TEXT NOT NULL,           -- raw text, max ~400 chars
  embedding   vector(384)              -- pgvector float32, all-MiniLM-L6-v2
)

-- IVFFlat approximate nearest-neighbor index
CREATE INDEX ON vectors.document_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Md Esfer Abdus Sami**

Built with ❤️ using FastAPI, LangGraph, pgvector, and Next.js 15.

> 🔗 API Docs: http://localhost:8000/docs | App: http://localhost:3000