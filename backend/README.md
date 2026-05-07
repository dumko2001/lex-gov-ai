# Lex-Gov AI — Backend

FastAPI backend for the judicial interpretation pipeline.

## Local Setup (without Docker)

### Prerequisites

- Python 3.12+
- PostgreSQL 16+ (running locally or via Docker)
- Redis 7+ (optional for local dev)
- poppler-utils (for `pdf2image`)

### 1. Install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp ../.env.example .env
# Edit .env and set at least:
#   OPENAI_API_KEY=sk-...
#   SARVAM_API_KEY=...
#   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lexgov
```

### 3. Create the database

```bash
createdb lexgov   # or use pgAdmin / psql
```

### 4. Run Alembic migrations

```bash
alembic upgrade head
```

This applies all migrations in `alembic/versions/`.

### 5. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

API docs will be available at `http://localhost:8000/docs`.

---

## Database Migrations with Alembic

Generate a new migration after model changes:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

Downgrade one revision:

```bash
alembic downgrade -1
```

Show current revision:

```bash
alembic current
```

---

## API Endpoints

### Judgments
- `POST /judgments/upload` — Upload PDF, trigger pipeline.
- `GET /judgments/` — List all judgments.
- `GET /judgments/{id}` — Get single judgment.

### Jobs
- `GET /jobs/{id}` — Processing job details.
- `GET /jobs/{id}/status` — Human-readable status with progress description.

### Action Plans
- `GET /action-plans/{id}` — Full action plan with directives.
- `GET /action-plans/judgment/{judgment_id}` — Latest plan for a judgment.
- `POST /action-plans/{id}/directives/{directive_id}/verify` — Officer verification (APPROVE / EDIT / REDO).
- `POST /action-plans/{id}/publish` — Publish verified plan to dashboard.

### Dashboard
- `GET /dashboard/?department=Revenue` — Department-specific directive list.
- `GET /dashboard/alerts?department=Revenue` — Active alerts.
- `POST /dashboard/alerts/mark-read` — Mark alerts as read.

---

## Pipeline Flow

```
Upload PDF
    │
    ▼
┌─────────────────┐
│  PASS 1         │  OpenAI GPT-4o-mini
│  Vision Classify│  Samples first 5, last 20, middle pages
│  Page Categories│  → Preamble / Procedural / Operative / Other
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PDF Slicing    │  pypdf extracts contiguous operative pages
│  (pypdf)        │  → new sliced PDF
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PASS 2         │  Sarvam-105B
│  Extraction     │  Structured JSON: directives, departments,
│  & Reasoning    │  deadlines, confidence scores
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Self-Correction│  OpenAI checks completeness
│  Loop (max 3)   │  Re-runs Pass 1+2 with correction notes if needed
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Needs Review   │  Nodal officer verifies each directive
│  (Human Loop)   │  Approve → Edit → Redo
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Published      │  Dashboard + Alert Engine activated
│  to Dashboard   │  Compliance tracking begins
└─────────────────┘
```

### Key Design Decisions

- **Sampling strategy**: We don't send every page to the vision model. We sample the first 5, last 20, and a few middle pages. This cuts cost and latency by ~80% while maintaining accuracy because operative orders are almost always at the end.
- **Deadline inference**: If a directive lacks an explicit date, the system infers a statutory deadline (30 days for specific appeals, 60 days for general High Court orders, 90 days for constitutional matters) from the `date_of_order`.
- **Conditional directives**: The prompt engineering in Pass 2 explicitly asks Sarvam-105B to extract both branches of conditional language ("If X within N days, then Y within M days").
- **Audit trail**: Every verification action (Approve/Edit/Redo) is recorded with original values, edited values, officer ID, and timestamp.
