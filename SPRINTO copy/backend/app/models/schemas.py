from pydantic import BaseModel, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class QueryType(str, Enum):
    GITHUB = "github"
    JIRA = "jira"
    DOCUMENT = "document"
    MIXED = "mixed"

class EvidenceQuery(BaseModel):
    query: str
    query_type: Optional[QueryType] = None
    source: Optional[QueryType] = None  # Backward compatibility field
    filters: Optional[Dict[str, Any]] = None
    
    @model_validator(mode='after')
    def validate_query_type_compatibility(self):
        # Handle backward compatibility: if source is provided but query_type is not, use source as query_type
        if self.source is not None and self.query_type is None:
            self.query_type = self.source
        # Ensure both fields are in sync
        elif self.query_type is not None and self.source is None:
            self.source = self.query_type
        return self

class QueryResponse(BaseModel):
    query_id: str
    status: str
    message: str
    evidence: Optional[List[Dict[str, Any]]] = None
    export_url: Optional[str] = None
    created_at: datetime

class GitHubPullRequest(BaseModel):
    number: int
    title: str
    state: str
    user: str
    created_at: datetime
    merged_at: Optional[datetime]
    approval_status: str
    reviewers: List[str]

class JIRATicket(BaseModel):
    key: str
    summary: str
    status: str
    assignee: Optional[str]
    created: datetime
    updated: datetime
    workflow_history: List[Dict[str, Any]]

class DocumentEvidence(BaseModel):
    filename: str
    content_type: str
    extracted_data: Dict[str, Any]
    relevant_sections: List[str]

class EvidenceItem(BaseModel):
    source: str
    source_type: QueryType
    title: str
    description: str
    data: Dict[str, Any]
    confidence_score: float
    timestamp: datetime

class ExportRequest(BaseModel):
    query_id: str
    format: str  # csv, xlsx, json
    include_metadata: bool = True
