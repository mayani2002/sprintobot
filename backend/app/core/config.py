from pydantic import BaseModel
from typing import Optional
import os

class Settings(BaseModel):
    # API Configuration
    API_HOST: str = "localhost"
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gpt-4"
    
    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_ORG: Optional[str] = None
    
    # JIRA Integration
    JIRA_URL: Optional[str] = None
    JIRA_USERNAME: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./evidence_bot.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".xlsx", ".xls", ".csv"]
    UPLOAD_DIR: str = "./uploads"

# Load from environment variables
settings = Settings(
    API_HOST=os.getenv("API_HOST", "localhost"),
    API_PORT=int(os.getenv("API_PORT", "8000")),
    FRONTEND_URL=os.getenv("FRONTEND_URL", "http://localhost:3000"),
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
    AI_MODEL=os.getenv("AI_MODEL", "gpt-4"),
    GITHUB_TOKEN=os.getenv("GITHUB_TOKEN"),
    GITHUB_ORG=os.getenv("GITHUB_ORG"),
    JIRA_URL=os.getenv("JIRA_URL"),
    JIRA_USERNAME=os.getenv("JIRA_USERNAME"),
    JIRA_API_TOKEN=os.getenv("JIRA_API_TOKEN"),
    DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///./evidence_bot.db"),
    SECRET_KEY=os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
    ALGORITHM=os.getenv("ALGORITHM", "HS256"),
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    MAX_FILE_SIZE=int(os.getenv("MAX_FILE_SIZE", "10485760")),
    UPLOAD_DIR=os.getenv("UPLOAD_DIR", "./uploads")
)
