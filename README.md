# Lex-Gov AI — Judicial Interpretation and Verified Action Pipeline

> **PAN IIT Bangalore × Government of Karnataka Hackathon — Theme 11**  
> *From Court Judgments to Verified Action Plans*

An AI system that reads Karnataka High Court judgment PDFs, extracts structured action plans using a two-pass Sarvam AI pipeline, routes directives to responsible departments through mandatory human verification, and presents a deadline-tracked dashboard to government officers.

---

## Live Demo

> **Note for judges:** The demo requires a Sarvam AI API key to run the AI pipeline. A [free key with ₹1,000 credits](https://dashboard.sarvam.ai) takes 60 seconds to get.

```
Frontend  →  http://localhost:5173
Backend   →  http://localhost:8000
API Docs  →  http://localhost:8000/docs
```

### Demo Credentials

| Role | Email | Password | What you see |
|------|-------|----------|--------------|
| System Admin | `admin@lexgov.ai` | `admin123` | Upload PDFs, view all judgments |
| Nodal Officer (Revenue) | `nodal@revenue.gov` | `nodal123` | Verify directives, click-to-cite PDF review |
| Law Officer | `nodal@law.gov` | `nodal123` | Law department verification queue |
| Dept Head (Revenue) | `dept@revenue.gov` | `dept123` | Dashboard with verified directives only |

### How to Navigate the Demo

1. **Login** as `admin@lexgov.ai` → go to **Upload** → upload any PDF from `test-data/judgments/`
2. Watch the pipeline status update in real-time (Pass 1 → Slicer → Pass 2 → Extraction done)
3. **Switch** to `nodal@revenue.gov` → open **Verify** queue
4. See the **split-screen UI**: left panel shows extracted directives with confidence scores; right panel shows the original PDF
5. Click any directive → PDF jumps to the source page
6. Choose **Approve**, **Edit**, or **Redo** (write a correction note → pipeline reruns)
7. After approval, switch to `dept@revenue.gov` → view the **Dashboard** with colour-coded deadlines
8. Visit **Alerts** to see the limitation tracker (contempt flags, appeal deadlines, compliance reminders)

### Test PDFs (included in `test-data/judgments/`)

| File | Case | Directives |
|------|------|------------|
| `WP_2938_2026_Sand_Mining_Home_Mines_3_Weeks.pdf` | Sand mining writ petition | Home + Mines departments, 3-week deadline |
| `Suvarana_vs_State_Revenue_2_Weeks.pdf` | Revenue dispute | Revenue department, 2-week compliance |
| `Dengue_PIL_Health_BBMP_6_Months.pdf` | Public health PIL | Health + BBMP, 6-month action plan |
| `WP_19885_2025_BEML_EPFO_90_Days.pdf` | BEML EPFO case | Labour department, 90-day window |

---

## Quick Start (60 Seconds)

```bash
# 1. Clone or unzip
git clone https://github.com/<your-org>/lex-gov-ai.git
cd lex-gov-ai

# 2. Add your Sarvam API key
cp .env.example .env
# Edit .env and set: SARVAM_API_KEY=your-key-here

# 3. Start everything (creates venv, installs deps, seeds DB, starts both servers)
./start.sh

# 4. Open browser
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

**Only hard requirement:** Python 3.10+, Node.js 18+, a Sarvam AI API key.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.12 preferred |
| Node.js | 18+ | npm included |
| Sarvam AI key | — | Free at [dashboard.sarvam.ai](https://dashboard.sarvam.ai) — ₹1,000 credits |
| Docker | Optional | For PostgreSQL deployment |

### Getting a Sarvam API Key

1. Go to <https://dashboard.sarvam.ai>
2. Sign up with email
3. ₹1,000 free credits are added automatically
4. Copy your API key
5. Set it in `.env`: `SARVAM_API_KEY=your-key-here`

**Estimated cost per judgment:** ₹15–30 (Vision document intelligence + 105B extraction)

---

## Setup Options

### Option A: One-Command Start ✅ (Recommended)

```bash
cd lex-gov-ai
cp .env.example .env          # then edit SARVAM_API_KEY
./start.sh
```

The script:
1. Detects Python 3.10–3.13, creates `backend/venv`
2. Installs all Python dependencies
3. Creates SQLite database (`lexgov.db`) and seeds demo users
4. Starts backend on port 8000 (FastAPI + uvicorn)
5. Installs Node deps (if needed) and starts frontend on port 5173 (Vite + React)

Press `Ctrl+C` to stop both servers cleanly.

### Option B: Manual Setup

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Init database
python3 -c "from app.main import app; from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Seed demo users
python3 -c "
from app.core.database import SessionLocal
from app.models.all import User
from app.core.security import get_password_hash
db = SessionLocal()
if not db.query(User).first():
    db.add_all([
        User(email='admin@lexgov.ai', full_name='System Admin', employee_id='ADM001', department='Admin', role='ADMIN', hashed_password=get_password_hash('admin123')),
        User(email='nodal@revenue.gov', full_name='Revenue Officer', employee_id='REV001', department='Revenue', role='NODAL_OFFICER', hashed_password=get_password_hash('nodal123')),
        User(email='nodal@law.gov', full_name='Law Officer', employee_id='LAW001', department='Law', role='NODAL_OFFICER', hashed_password=get_password_hash('nodal123')),
        User(email='dept@revenue.gov', full_name='Revenue Dept User', employee_id='REV002', department='Revenue', role='DEPT_HEAD', hashed_password=get_password_hash('dept123')),
    ])
    db.commit()
db.close()
"

# Start
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Option C: Docker (with PostgreSQL)

```bash
cp .env.example .env    # set SARVAM_API_KEY
docker-compose up --build
```

---

## Architecture

```
┌──────────────┐    ┌───────────────────────────────┐    ┌──────────────┐
│  PDF Upload  │───▶│  Pass 1: Sarvam Vision (3B)   │───▶│  PDF Slicer  │
│  (CCMS API   │    │  OCR + Structural Mapping     │    │  (10–15 pp   │
│  in prod)    │    │  → Page Index [1-5, 47-53]    │    │  from 90 pp) │
└──────────────┘    └───────────────────────────────┘    └──────┬───────┘
                                                                 │
                                                                 ▼
                                                   ┌────────────────────────┐
                                                   │  Pass 2: Sarvam-105B   │
                                                   │  Extraction + Reasoning│
                                                   │  128K context window   │
                                                   │  22 Indian languages   │
                                                   └────────────┬───────────┘
                                                                │
                              ┌─────────────────────────────────┤
                              │ is_complete_info_present = false │
                              │ → re-run with correction note   │
                              └─────────────────────────────────┘
                                                                │ true
                                                                ▼
                    ┌───────────────────────────────────────────────────────┐
                    │           HUMAN VERIFICATION (Mandatory)              │
                    │  ┌────────────────────┐  ┌─────────────────────────┐ │
                    │  │  Extracted         │  │  Original PDF Viewer    │ │
                    │  │  Directives        │  │  (click-to-cite)        │ │
                    │  │  + Confidence      │  │  Jump to source page    │ │
                    │  └────────────────────┘  └─────────────────────────┘ │
                    │      [Approve]  [Edit]  [Redo + Correction Note]      │
                    └───────────────────────────────────────────────────────┘
                                                                │
                                                                ▼
                    ┌───────────────────────────────────────────────────────┐
                    │       DEPARTMENT DASHBOARD (Verified Only)            │
                    │  🔴 Red < 10 days  🟡 Amber 10–30  🟢 Green 30+      │
                    │  Limitation alerts: 7-day / 15-day / contempt flag    │
                    └───────────────────────────────────────────────────────┘
```

### Pass 1 — Sarvam Vision 3B (Structural Mapping)
Handles scanned pages, Kannada/Indic text, and court stamps. Outputs a **Page Index** (e.g., `[1-5, 47-53]`) identifying the preamble and operative order. Does not interpret meaning.

### PDF Slicer
Builds a temporary PDF from the Page Index. A 90-page judgment becomes a 10–15 page slice, removing procedural noise before Pass 2.

### Pass 2 — Sarvam-105B (Extraction + Reasoning)
Extracts the full action plan schema including conditional directives, responsible departments, calculated limitation deadlines, and source paragraph references for click-to-cite.

### Self-Correction Loop
If `is_complete_info_present = false`, the failure context is appended to the Pass 1 prompt and the pipeline reruns. Incomplete outputs are **never** published to the dashboard.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | Login, returns JWT |
| `GET`  | `/auth/me` | Current user |
| `POST` | `/judgments/upload` | Upload PDF, triggers pipeline |
| `GET`  | `/judgments/` | List all judgments |
| `GET`  | `/jobs/{id}/status` | Pipeline status (poll or stream) |
| `GET`  | `/action-plans/{id}` | Full action plan with directives |
| `GET`  | `/action-plans/judgment/{judgment_id}` | Plan by judgment |
| `POST` | `/action-plans/{id}/directives/{did}/verify` | Approve / Edit / Redo |
| `POST` | `/action-plans/{id}/publish` | Publish to dashboard |
| `GET`  | `/dashboard/?department=Revenue` | Dept-filtered verified view |
| `GET`  | `/dashboard/alerts` | Limitation tracker alerts |

Full interactive docs: `http://localhost:8000/docs`

---

## Project Structure

```
lex-gov-ai/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints (auth, judgments, jobs, action-plans, dashboard)
│   │   ├── core/             # Config, DB, security, JWT
│   │   ├── models/           # SQLAlchemy models (10 tables)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # AI pipeline, PDF slicer, alert engine
│   ├── alembic/              # DB migrations
│   ├── scripts/              # Utility scripts
│   ├── tests/                # Test harness
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── hooks/            # API hooks (TanStack Query)
│   │   ├── routes/           # Screens: login, upload, verify, dashboard, alerts
│   │   └── stores/           # Auth state (Zustand)
│   └── package.json
├── test-data/
│   └── judgments/            # 4 synthetic Karnataka HC judgment PDFs
├── lex-gov-ai-verified-action-pipeline.pptx   # Presentation
├── docker-compose.yml        # Optional PostgreSQL deployment
├── start.sh                  # One-command startup script
├── external_env.sh           # Routes caches to external drive (optional)
├── .env.example              # Copy to .env and set SARVAM_API_KEY
└── README.md
```

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Frontend | Vite + React 19 + TypeScript | Fast dev, type-safe |
| Styling | Tailwind CSS + shadcn/ui | Consistent, accessible |
| State | TanStack Query + Zustand | Server + client state |
| Routing | TanStack Router | Type-safe routing |
| PDF viewer | react-pdf | Page navigation, text extraction |
| Backend | FastAPI + Python 3.12 | Async, auto-docs |
| Database | SQLite (default) / PostgreSQL | Zero setup for demo |
| AI Pass 1 | Sarvam Vision (3B) | Document intelligence, OCR, 22 Indian languages |
| AI Pass 2 | Sarvam-105B | Indian legal language, 128K context, conditional directives |
| Auth | JWT (python-jose) | Stateless, role-based |
| Deployment | Docker Compose | One-command start |

---

## Database Schema (10 Tables)

| Table | Purpose |
|-------|---------|
| `judgments` | Source PDFs and metadata |
| `processing_jobs` | Pipeline job tracking and status |
| `page_indices` | Pass 1 output — page ranges for slicing |
| `action_plans` | Pass 2 output — full structured extraction |
| `directives` | Individual court directives per action plan |
| `verification_actions` | Immutable audit trail (approve/edit/redo) |
| `users` | Officers, admins, role-based access |
| `audit_log` | System-wide immutable log |
| `alerts` | Deadline and limitation notifications |
| `feedback_contexts` | Self-correction loop history |

---

## Testing

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Tests cover: PDF page-range parsing, pipeline state machine, self-correction loop, verification actions (Approve/Edit/Redo), and alert generation.

---

## Why Sarvam AI?

| Dimension | Generic LLM (GPT-4, Claude) | Sarvam AI |
|-----------|-----------------------------|-----------|
| PDF handling | Fails on scanned / Kannada pages | Vision model handles scanned, stamped, mixed-script |
| Legal language | General English | 105B trained on Indian legal text across 22 languages |
| Data sovereignty | Foreign API (US-hosted) | Indian company; on-premise deployment at SDC |
| Cost | $5–10 per 100-page doc | ₹15–30 per judgment |
| Failure mode | Silent hallucination | Self-correction loop + mandatory human sign-off |

> **For production:** Both models deploy on-premise at the Karnataka State Data Centre via vLLM. Pipeline code is identical — only the API endpoint changes.

---

## Deployment Notes (Production Path)

- **On-premise SDC:** Replace `SARVAM_API_KEY` endpoint with internal vLLM instance. No code changes.
- **Database:** Change `DATABASE_URL` in `.env` to PostgreSQL. Alembic migrations are ready (`alembic upgrade head`).
- **File storage:** Replace local `uploads/` path with S3-compatible object store.
- **Auth:** Add Karnataka government SSO (SAML/OAuth) in front of the JWT layer.
- **CCMS integration:** Replace the upload endpoint with the CCMS API webhook handler.

---

## Limitations & Future Work

| Current Prototype | Production Path |
|-------------------|-----------------|
| SQLite database | PostgreSQL at SDC |
| Local file storage | S3-compatible object storage |
| Basic JWT auth | Government SSO integration |
| Page-level PDF jump | Paragraph-level highlight |
| Rule-based alerts | SMS/email gateway (NIC) |
| Manual PDF upload | CCMS API auto-fetch |
| 4 synthetic PDFs | Full CIS/CCMS integration |

---

## Team

**Track:** Theme 11 — From Court Judgments to Verified Action Plans  
**Hackathon:** PAN IIT Bangalore Alumni Association × Government of Karnataka

---

## License

Hackathon prototype. All code is original work created for the Lex-Gov AI submission.
