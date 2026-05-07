# Lex-Gov AI Backend

FastAPI backend for the judicial interpretation and verified action pipeline.

## Local Setup

Prerequisites:

- Python 3.10+
- `poppler-utils` for PDF rendering helpers
- Sarvam AI API key in the project-root `.env`

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create SQLite tables
python3 -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Start the API
uvicorn app.main:app --reload --port 8000
```

The backend reads environment variables from `../.env` first, then `backend/.env`.
The default database is SQLite:

```bash
DATABASE_URL=sqlite:///./rupai.db
```

API docs are available at `http://localhost:8000/docs`.

## API Endpoints

### Judgments
- `POST /judgments/upload` - Upload PDF and trigger the async pipeline.
- `GET /judgments/` - List judgments.
- `GET /judgments/{id}` - Get one judgment.
- `GET /judgments/{id}/pdf` - Serve the original uploaded PDF.

### Jobs
- `GET /jobs/{id}` - Processing job details.
- `GET /jobs/judgment/{judgment_id}` - Latest job for an uploaded judgment.
- `GET /jobs/{id}/status` - Human-readable status.

### Action Plans
- `GET /action-plans/{id}` - Full action plan with directives.
- `GET /action-plans/judgment/{judgment_id}` - Latest plan for a judgment.
- `POST /action-plans/{id}/directives/{directive_id}/verify` - Approve, edit, or redo.
- `POST /action-plans/{id}/publish` - Publish verified directives.

### Dashboard
- `GET /dashboard/?department=Revenue` - Department-specific verified directives.
- `GET /dashboard/?department=All` - All verified directives.
- `GET /dashboard/alerts?department=Revenue` - Active alerts.
- `POST /dashboard/alerts/mark-read` - Mark alerts as read.

## Pipeline Flow

1. Upload a real judgment PDF.
2. Store file metadata in SQLite.
3. Create a visible async `processing_jobs` row.
4. Extract page text with `pdfplumber`.
5. Score and slice operative pages.
6. Send sliced text to Sarvam-105B for structured directive extraction.
7. Store action plans and directives.
8. Route directives to human verification before dashboard publication.

If `SARVAM_API_KEY` is missing or invalid, the job is marked `FAILED` with a visible error message.
