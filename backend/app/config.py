from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration."""
    
    # Database
    database_url: str = "postgresql://veriship_user:veriship_dev_password@localhost:5432/veriship_db"
    redis_url: str = "redis://localhost:6379/0"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    
    # AI/LLM
    openai_api_key: str = ""
    claude_api_key: str = ""
    
    # JWT
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
