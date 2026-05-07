from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Lex-Gov AI"
    DEBUG: bool = True
    
    # Database (SQLite for hackathon — zero setup)
    DATABASE_URL: str = "sqlite:///./lexgov.db"
    
    # Security
    SECRET_KEY: str = "hackathon-demo-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    
    # AI APIs — ONLY SARVAM (Vision + 105B)
    SARVAM_API_KEY: str = ""
    SARVAM_MODEL_PASS2: str = "sarvam-105b"
    SARVAM_BASE_URL: str = "https://api.sarvam.ai"
    
    # Pipeline
    MAX_ITERATIONS: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
