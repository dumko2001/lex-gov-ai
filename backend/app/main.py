from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import judgments, jobs, action_plans, dashboard, auth

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

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "lex-gov-ai-backend"}
