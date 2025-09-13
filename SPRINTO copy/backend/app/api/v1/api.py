from fastapi import APIRouter
from app.api.v1 import evidence

api_router = APIRouter()

api_router.include_router(evidence.router, prefix="/evidence", tags=["evidence"])

@api_router.get("/")
async def api_root():
    return {
        "message": "Evidence-on-Demand Bot API v1",
        "endpoints": {
            "query": "/evidence/query",
            "evidence": "/evidence/evidence/{query_id}",
            "export": "/evidence/export/{query_id}",
            "upload": "/evidence/documents/upload",
            "health": "/evidence/health"
        }
    }
