import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True, env_file=".env")
    
    PROJECT_NAME: str = "Multi-Hospital Post-Discharge Outreach Platform"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Database
    ENV: str = "development"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./postcare.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # JWT & Auth
    SECRET_KEY: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production-healthcare-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # CORS & Public Base URL
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    
    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS
    
    # AI Config
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "mock")
    AI_FALLBACK_TO_MOCK: bool = os.getenv("AI_FALLBACK_TO_MOCK", "false").lower() == "true"
    GEMINI_RPM_LIMIT: int = int(os.getenv("GEMINI_RPM_LIMIT", "5"))
    GEMINI_RPM_SAFETY_LIMIT: int = int(os.getenv("GEMINI_RPM_SAFETY_LIMIT", "4"))
    
    # Consensus Policy
    CONSENSUS_POLICY: str = os.getenv("CONSENSUS_POLICY", "STRICT_CONSERVATIVE")
    
    # Default Outbound Capacity per hospital
    DEFAULT_HOSPITAL_CAPACITY: int = 10

settings = Settings()
