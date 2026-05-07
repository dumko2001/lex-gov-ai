from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import judgments, jobs, action_plans, dashboard, auth
from app.core.database import Base, SessionLocal, engine
from app.models.all import User

app = FastAPI(
    title="Lex-Gov AI",
    description="Judicial Interpretation Pipeline for Karnataka High Court judgments",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://lex-gov-frontend-ui.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(judgments.router)
app.include_router(jobs.router)
app.include_router(action_plans.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def init_demo_database():
    """Create SQLite tables and seed the no-login demo officer."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "demo-officer@lex-gov.local").first()
        if not existing:
            db.add(
                User(
                    email="demo-officer@lex-gov.local",
                    full_name="Demo Nodal Officer",
                    employee_id="DEMO-001",
                    department="All",
                    role="ADMIN",
                    hashed_password=None,
                )
            )
            db.commit()
    finally:
        db.close()


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "lex-gov-ai-backend"}
