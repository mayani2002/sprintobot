"""
GitHub API Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.github_service import GitHubService

router = APIRouter(prefix="/api/github", tags=["github"])

class GitHubQueryRequest(BaseModel):
    query: str

class GitHubQueryResponse(BaseModel):
    query: str
    function_called: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    result: Any
    method: Optional[str] = None
    error: Optional[str] = None

@router.post("/query")
async def process_github_query(request: GitHubQueryRequest):
    """
    Process a natural language query about GitHub repositories, PRs, etc.

    Examples:
    - "Show me PRs merged in the last 7 days"
    - "Which PRs are waiting for review?"
    - "Get details of PR #123"
    - "List repositories for user octocat"
    - "Get all open PRs from my top 5 repositories"
    """
    try:
        service = GitHubService()
        result = await service.process_natural_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint for GitHub integration."""
    return {"status": "healthy", "service": "github"}
