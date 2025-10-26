from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from config/.env
config_path = Path(__file__).parent.parent.parent / "config" / ".env"
load_dotenv(dotenv_path=config_path)

from app.routers import github

app = FastAPI(
    title="SprintoBot API",
    description="AI-Powered Evidence-on-Demand Bot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(github.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to SprintoBot API",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": {
            "github_token_configured": bool(os.getenv("GITHUB_TOKEN")),
            "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY"))
        }
    }
