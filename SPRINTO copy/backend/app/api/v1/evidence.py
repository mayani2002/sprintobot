from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import Response
from typing import List, Optional
import uuid
import os
from datetime import datetime

from app.models.schemas import EvidenceQuery, QueryResponse, ExportRequest
from app.services.ai_service import AIService
from app.integrations.github_integration import GitHubIntegration
from app.integrations.jira_integration import JiraIntegration
from app.integrations.document_parser import DocumentParser
from app.services.evidence_service import EvidenceService

router = APIRouter()

# Initialize services
ai_service = AIService()
github_integration = GitHubIntegration()
jira_integration = JiraIntegration()
document_parser = DocumentParser()
evidence_service = EvidenceService()

@router.post("/query", response_model=QueryResponse)
async def submit_query(query: EvidenceQuery):
    """Submit a natural language query for evidence retrieval."""
    try:
        # Generate unique query ID
        query_id = str(uuid.uuid4())

        # Process the query with AI to understand intent
        if query.query_type =="github":
            ai_analysis = await ai_service.process_query_github(query.query)
        else:
            ai_analysis = await ai_service.process_query(query.query)
        
        # Route to appropriate integration based on query type
        evidence_items = []
        
        # Use the explicit query_type if provided, otherwise use AI analysis
        query_type = query.query_type or ai_analysis.get("query_type")
        
        if query_type == "github":
            evidence_items = await _handle_github_query(ai_analysis, query.filters or {})
            print(f"GitHub evidence items: {evidence_items}")  # Debug print
        elif query_type == "jira":
            evidence_items = await _handle_jira_query(ai_analysis, query.filters or {})
        elif query_type == "document":
            evidence_items = await _handle_document_query(ai_analysis, query.filters or {})
        elif query_type == "mixed":
            # Handle queries that require multiple sources
            github_items = await _handle_github_query(ai_analysis, query.filters or {})
            print(github_items)
            jira_items = await _handle_jira_query(ai_analysis, query.filters or {})
            document_items = await _handle_document_query(ai_analysis, query.filters or {})
            evidence_items = github_items + jira_items + document_items

        else:
            # Default to searching all sources including documents
            github_items = await _handle_github_query(ai_analysis, query.filters or {})
            jira_items = await _handle_jira_query(ai_analysis, query.filters or {})
            document_items = await _handle_document_query(ai_analysis, query.filters or {})
            evidence_items = github_items + jira_items + document_items
        
        # Format evidence with AI
        if evidence_items:
            formatted_summary = await ai_service.format_evidence(evidence_items, query.query)
        else:
            formatted_summary = "No evidence found matching your query."
        
        # Store results
        result = await evidence_service.store_query_result(
            query_id, query.query, evidence_items, formatted_summary
        )
        
        return QueryResponse(
            query_id=query_id,
            status="completed",
            message=formatted_summary,
            evidence=evidence_items,
            export_url=f"/api/v1/export/{query_id}",
            created_at=result["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/evidence/{query_id}")
async def get_evidence(query_id: str):
    """Retrieve evidence results for a specific query."""
    try:
        result = await evidence_service.get_query_result(query_id)
        if not result:
            raise HTTPException(status_code=404, detail="Query not found")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve evidence: {str(e)}")

@router.post("/export/{query_id}")
async def export_evidence(query_id: str, export_request: ExportRequest):
    """Export evidence to a file format."""
    try:
        result = await evidence_service.get_query_result(query_id)
        if not result:
            raise HTTPException(status_code=404, detail="Query not found")
        
        file_path = await evidence_service.export_evidence(
            query_id, result["evidence"], export_request.format
        )
        
        return {"download_url": file_path, "format": export_request.format}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/documents/query", response_model=QueryResponse)
async def submit_document_query(query: EvidenceQuery):
    """Submit a natural language query specifically for document search only."""
    try:
        # Generate unique query ID
        query_id = str(uuid.uuid4())
        
        # Process the query with AI to understand intent
        ai_analysis = await ai_service.process_query(query.query)
        
        # Only search documents - no GitHub or JIRA
        evidence_items = await _handle_document_query(ai_analysis, query.filters or {})
        
        # Format evidence with AI
        if evidence_items:
            formatted_summary = await ai_service.format_evidence(evidence_items, query.query)
        else:
            formatted_summary = "No documents found matching your query."
        
        # Store results
        result = await evidence_service.store_query_result(
            query_id, query.query, evidence_items, formatted_summary
        )
        
        return QueryResponse(
            query_id=query_id,
            status="completed",
            message=formatted_summary,
            evidence=evidence_items,
            export_url=f"/api/v1/export/{query_id}",
            created_at=result["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document query processing failed: {str(e)}")

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and parse a document for evidence extraction."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.pdf', '.xlsx', '.xls', '.csv']:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse document
        parsed_data = await document_parser.parse_document(file_path)
        
        return {
            "filename": file.filename,
            "file_path": file_path,
            "parsed_data": parsed_data,
            "message": "Document uploaded and parsed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@router.get("/reports")
async def get_all_reports():
    """Get all stored query results for report generation."""
    try:
        # Get all stored results from evidence service
        results = evidence_service._load_results()
        
        # Convert to report format
        reports = []
        for query_id, result in results.items():
            # Extract sources from evidence items
            sources = set()
            for evidence in result.get("evidence", []):
                source_type = evidence.get("source_type", "unknown")
                if source_type == "document":
                    sources.add("documents")
                elif source_type == "github":
                    sources.add("github")
                elif source_type == "jira":
                    sources.add("jira")
            
            # Generate report title based on query
            query_text = result.get("query", "Unknown Query")
            title = query_text[:50] + "..." if len(query_text) > 50 else query_text
            
            report = {
                "id": query_id,
                "title": title,
                "description": f"Evidence report generated from query: {query_text}",
                "created_at": result.get("created_at"),
                "evidence_count": result.get("evidence_count", 0),
                "sources": list(sources) if sources else ["unknown"],
                "summary": result.get("summary", "No summary available"),
                "queries": [query_text],
                "evidence": result.get("evidence", [])
            }
            reports.append(report)
        
        # Sort by creation date (newest first)
        reports.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"reports": reports, "total": len(reports)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")

@router.post("/reports/{report_id}/export")
async def export_report(report_id: str, format: str = Query("txt", description="Export format: txt or json")):
    """Export a specific report in TXT or JSON format."""
    try:
        print(f"Export request: report_id={report_id}, format={format}")
        
        # Get the report data
        result = await evidence_service.get_query_result(report_id)
        if not result:
            raise HTTPException(status_code=404, detail="Report not found")
        
        print(f"Found report data: {result.get('query', 'Unknown')}")
        
        # Generate report content
        report_content = await _generate_report_content(result)
        print(f"Generated report content with {len(report_content.get('findings', []))} findings")
        
        if format.lower() == "txt":
            # Generate TXT
            print("Generating TXT...")
            txt_content = await _generate_txt_report(report_content)
            print(f"Generated TXT content: {len(txt_content)} characters")
            return Response(
                content=txt_content,
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename=report_{report_id}.txt"}
            )
        elif format.lower() == "json":
            # Generate JSON
            print("Generating JSON...")
            json_content = await _generate_json_report(report_content)
            print(f"Generated JSON content: {len(json_content)} characters")
            return Response(
                content=json_content,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=report_{report_id}.json"}
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'txt' or 'json'")
            
    except Exception as e:
        print(f"Export error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "evidence-api"}

# Helper functions
async def _handle_github_query(ai_analysis: dict, filters: dict) -> List[dict]:
    """Handle GitHub-specific queries using AI-selected function."""
    evidence_items = []
    try:
        function = ai_analysis.get("function")
        parameters = ai_analysis.get("parameters", {})
        # Merge any explicit filters
        parameters = {**parameters, **filters}

        # Route to the correct GitHubIntegration method
        if function == "get_merged_prs_last_n_days":
            n = parameters.get("n", 7)
            merged_prs = github_integration.get_merged_prs_last_n_days(n)
            for pr in merged_prs:
                evidence_items.append({
                    "source": "github",
                    "source_type": "github",
                    "title": f"Merged PR #{pr['number']}: {pr['title']}",
                    "description": f"Merged at: {pr['merged_at']}, Approvers: {', '.join(pr['approvers'])}",
                    "data": pr,
                    "confidence_score": 0.9,
                    "timestamp": pr["merged_at"]
                })
        elif function == "get_prs_waiting_for_review":
            hours = parameters.get("hours", 24)
            waiting_prs = github_integration.get_prs_waiting_for_review(hours)
            for pr in waiting_prs:
                evidence_items.append({
                    "source": "github",
                    "source_type": "github",
                    "title": f"PR #{pr['number']}: {pr['title']}",
                    "description": f"Created at: {pr['created_at']}, Waiting for review",
                    "data": pr,
                    "confidence_score": 0.8,
                    "timestamp": pr["created_at"]
                })
        elif function == "get_pr_details":
            pr_number = parameters.get("pr_number")
            if pr_number is not None:
                pr_data = github_integration.get_pr_details(pr_number)
                evidence_items.append({
                    "source": "github",
                    "source_type": "github",
                    "title": f"PR #{pr_data['number']}: {pr_data['title']}",
                    "description": f"Status: {pr_data['state']}, Author: {pr_data['user']}",
                    "data": pr_data,
                    "confidence_score": 0.95,
                    "timestamp": pr_data["created_at"]
                })
        elif function == "get_prs":
            prs = github_integration.get_prs(**parameters)
            for pr in prs:
                evidence_items.append({
                    "source": "github",
                    "source_type": "github",
                    "title": f"PR #{pr['number']}: {pr['title']}",
                    "description": f"Status: {pr['state']}, Author: {pr['user']['login'] if isinstance(pr['user'], dict) else pr['user']}",
                    "data": pr,
                    "confidence_score": 0.8,
                    "timestamp": pr["created_at"]
                })
        else:
            evidence_items.append({
                "source": "github",
                "source_type": "github",
                "title": "GitHub Integration Error",
                "description": f"Unknown function requested: {function}",
                "data": {"error": f"Unknown function: {function}"},
                "confidence_score": 0.0,
                "timestamp": None
            })
    except Exception as e:
        evidence_items.append({
            "source": "github",
            "source_type": "github",
            "title": "GitHub Integration Error",
            "description": f"Failed to fetch GitHub data: {str(e)}",
            "data": {"error": str(e)},
            "confidence_score": 0.0,
            "timestamp": None
        })
    return evidence_items

async def _handle_jira_query(ai_analysis: dict, filters: dict) -> List[dict]:
    """Handle JIRA-specific queries."""
    evidence_items = []
    
    try:
        parameters = ai_analysis.get("parameters", {})
        
        if "ticket_key" in parameters:
            # Specific ticket query
            ticket_data = await jira_integration.get_ticket(parameters["ticket_key"])
            evidence_items.append({
                "source": "jira",
                "source_type": "jira",
                "title": f"{ticket_data['key']}: {ticket_data['summary']}",
                "description": f"Status: {ticket_data['status']}, Assignee: {ticket_data['assignee']}",
                "data": ticket_data,
                "confidence_score": 0.95,
                "timestamp": ticket_data["created"]
            })
        else:
            # Search query - build JQL
            jql_parts = []
            if "project" in parameters:
                jql_parts.append(f"project = {parameters['project']}")
            if "assignee" in parameters:
                jql_parts.append(f"assignee = {parameters['assignee']}")
            if "status" in parameters:
                jql_parts.append(f"status = '{parameters['status']}'")
            
            jql_query = " AND ".join(jql_parts) if jql_parts else "project is not EMPTY"
            tickets = await jira_integration.search_tickets(jql_query)
            
            for ticket in tickets:
                evidence_items.append({
                    "source": "jira",
                    "source_type": "jira",
                    "title": f"{ticket['key']}: {ticket['summary']}",
                    "description": f"Status: {ticket['status']}, Assignee: {ticket['assignee']}",
                    "data": ticket,
                    "confidence_score": 0.8,
                    "timestamp": ticket["created"]
                })
    
    except Exception as e:
        evidence_items.append({
            "source": "jira",
            "source_type": "jira",
            "title": "JIRA Integration Error",
            "description": f"Failed to fetch JIRA data: {str(e)}",
            "data": {"error": str(e)},
            "confidence_score": 0.0,
            "timestamp": None
        })
    
    return evidence_items

async def _handle_document_query(ai_analysis: dict, filters: dict) -> List[dict]:
    """Handle document-based queries with improved relevance scoring."""
    evidence_items = []
    
    try:
        query_text = ai_analysis.get("intent", "").lower()
        uploads_dir = "uploads"
        
        # Search through uploaded files
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        # Parse the document
                        parsed_data = await document_parser.parse_document(file_path)
                        
                        # Search for relevant data based on query
                        matches = await _search_document_data(parsed_data, query_text)
                        
                        if matches:
                            # Calculate overall confidence based on match quality
                            avg_relevance = sum(match.get("_relevance_score", 0) for match in matches) / len(matches)
                            confidence_score = min(0.95, 0.5 + (avg_relevance * 0.5))  # Scale to 0.5-0.95
                            
                            # Create more descriptive title and description
                            top_matches = matches[:3]  # Get top 3 matches for description
                            match_reasons = [match.get("_match_reason", "Relevant data") for match in top_matches]
                            
                            evidence_items.append({
                                "source": f"documents/{filename}",
                                "source_type": "document",
                                "title": f"Evidence from {filename}",
                                "description": f"Found {len(matches)} relevant records. Top matches: {'; '.join(match_reasons[:2])}",
                                "data": {
                                    "filename": filename,
                                    "matches": matches,
                                    "total_matches": len(matches),
                                    "query": query_text,
                                    "avg_relevance": avg_relevance,
                                    "file_type": parsed_data.get("content_type", "unknown")
                                },
                                "confidence_score": confidence_score,
                                "timestamp": None
                            })
                    except Exception as file_error:
                        # Log file-specific errors but continue with other files
                        print(f"Error processing file {filename}: {str(file_error)}")
                        continue
        
        # Sort evidence items by confidence score (highest first)
        evidence_items.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        
        if not evidence_items:
            evidence_items.append({
                "source": "documents",
                "source_type": "document",
                "title": "No Matches Found",
                "description": f"No documents found matching query: {query_text}",
                "data": {"query": query_text, "searched_files": len(os.listdir(uploads_dir)) if os.path.exists(uploads_dir) else 0},
                "confidence_score": 0.0,
                "timestamp": None
            })
    
    except Exception as e:
        evidence_items.append({
            "source": "documents",
            "source_type": "document",
            "title": "Document Search Error",
            "description": f"Failed to search documents: {str(e)}",
            "data": {"error": str(e)},
            "confidence_score": 0.0,
            "timestamp": None
        })
    
    return evidence_items

def _extract_meaningful_terms(query_text: str, query_intent: str, parameters: dict) -> set:
    """Extract meaningful search terms, filtering out stop words and common words."""
    
    # Common stop words that don't add meaning to search
    stop_words = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it', 
        'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will', 'with', 'would', 'this', 'these', 'they',
        'them', 'their', 'there', 'then', 'than', 'or', 'but', 'if', 'so', 'up', 'out', 'off', 'over',
        'under', 'again', 'further', 'then', 'once', 'here', 'when', 'where', 'why', 'how', 'all', 'any',
        'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'can', 'could', 'should', 'would', 'may', 'might', 'must',
        'shall', 'will', 'do', 'does', 'did', 'have', 'has', 'had', 'having', 'being', 'been'
    }
    
    # Extract terms from query text
    query_terms = set()
    for word in query_text.lower().split():
        # Remove punctuation and check if it's meaningful
        clean_word = word.strip('.,!?;:"()[]{}')
        if clean_word and len(clean_word) > 1 and clean_word not in stop_words:
            query_terms.add(clean_word)
    
    # Extract terms from query intent
    intent_terms = set()
    for word in query_intent.lower().split():
        clean_word = word.strip('.,!?;:"()[]{}')
        if clean_word and len(clean_word) > 1 and clean_word not in stop_words:
            intent_terms.add(clean_word)
    
    # Extract terms from parameters
    param_terms = set()
    for param_value in parameters.values():
        if isinstance(param_value, str):
            for word in param_value.lower().split():
                clean_word = word.strip('.,!?;:"()[]{}')
                if clean_word and len(clean_word) > 1 and clean_word not in stop_words:
                    param_terms.add(clean_word)
    
    # Combine all meaningful terms
    all_terms = query_terms.union(intent_terms).union(param_terms)
    
    # Special handling for common query patterns
    if 'list' in query_text.lower() and 'assigned' in query_text.lower():
        # For "list assets assigned to [person]" queries
        all_terms.add('assigned')
        all_terms.add('asset')
    
    if 'count' in query_text.lower():
        all_terms.add('count')
    
    if 'find' in query_text.lower():
        all_terms.add('find')
    
    return all_terms

async def _search_document_data(parsed_data: dict, query_text: str) -> List[dict]:
    """Search through parsed document data for relevant matches using AI-powered analysis."""
    matches = []
    
    try:
        if not parsed_data or not query_text:
            return matches
        
        content_type = parsed_data.get("content_type", "").lower()
        data = parsed_data.get("data", [])
        
        # Use AI to understand query intent and extract relevant search terms
        ai_analysis = await ai_service.process_query(query_text)
        query_intent = ai_analysis.get("intent", "").lower()
        parameters = ai_analysis.get("parameters", {})
        
        # Extract key search terms from both original query and AI analysis
        # Filter out stop words and focus on meaningful terms
        search_terms = _extract_meaningful_terms(query_text, query_intent, parameters)
        
        # For CSV/Excel data
        if content_type in ["csv", "excel"] and isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    # Calculate relevance score for this row
                    relevance_score = await _calculate_row_relevance(row, query_text, query_intent, search_terms)
                    
                    # Only include rows with meaningful relevance
                    if relevance_score > 0.3:  # Threshold for relevance
                        row_with_score = row.copy()
                        row_with_score["_relevance_score"] = relevance_score
                        row_with_score["_match_reason"] = _get_match_reason(row, query_text, search_terms)
                        matches.append(row_with_score)
        
        # For text-based content (PDFs, etc.)
        elif isinstance(data, str):
            text_relevance = await _calculate_text_relevance(data, query_text, search_terms)
            if text_relevance > 0.3:
                matches.append({
                    "content": data, 
                    "match_type": "text_content",
                    "_relevance_score": text_relevance,
                    "_match_reason": f"Text content matches query terms"
                })
        
        # Sort matches by relevance score (highest first)
        matches.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
        
        # Limit results to most relevant matches (top 20)
        matches = matches[:20]
    
    except Exception as e:
        print(f"Error searching document data: {str(e)}")
    
    return matches

async def _calculate_row_relevance(row: dict, query_text: str, query_intent: str, search_terms: set) -> float:
    """Calculate relevance score for a data row based on query."""
    try:
        # Convert row values to searchable text
        row_text = " ".join(str(value).lower() for value in row.values() if value is not None)
        
        if not row_text:
            return 0.0
        
        # Base score from keyword matches
        keyword_matches = sum(1 for term in search_terms if term in row_text)
        base_score = keyword_matches / len(search_terms) if search_terms else 0
        
        # Boost score for exact phrase matches
        phrase_boost = 0.0
        if query_text.lower() in row_text:
            phrase_boost = 0.3
        
        # Boost score for intent-specific matches
        intent_boost = 0.0
        if query_intent and any(word in row_text for word in query_intent.split()):
            intent_boost = 0.2
        
        # Boost score for common query patterns
        pattern_boost = 0.0
        
        # Handle "assigned to [person]" queries
        if "assigned" in query_text.lower() and "to" in query_text.lower():
            # Look for assignment-related fields
            assignment_fields = ['assigned', 'assignee', 'owner', 'user', 'person', 'employee']
            if any(field in row_text for field in assignment_fields):
                pattern_boost = 0.5
                # Extra boost if we find a name match
                for term in search_terms:
                    if len(term) > 2 and term in row_text:  # Likely a name
                        pattern_boost += 0.3
                        break
        
        # Handle "count" queries
        elif "count" in query_text.lower():
            if any(term in row_text for term in search_terms):
                pattern_boost = 0.4
        
        # Handle "list" queries
        elif "list" in query_text.lower():
            if any(term in row_text for term in search_terms):
                pattern_boost = 0.3
        
        # Handle specific device/asset queries
        elif "laptop" in query_text.lower():
            if "laptop" in row_text:
                pattern_boost = 0.4
        elif "apple" in query_text.lower():
            if "apple" in row_text:
                pattern_boost = 0.4
        elif "office" in query_text.lower():
            if "office" in row_text:
                pattern_boost = 0.3
        
        # Calculate final relevance score
        relevance = min(1.0, base_score + phrase_boost + intent_boost + pattern_boost)
        
        return relevance
        
    except Exception as e:
        print(f"Error calculating row relevance: {str(e)}")
        return 0.0

async def _calculate_text_relevance(text: str, query_text: str, search_terms: set) -> float:
    """Calculate relevance score for text content."""
    try:
        text_lower = text.lower()
        
        # Base score from keyword matches
        keyword_matches = sum(1 for term in search_terms if term in text_lower)
        base_score = keyword_matches / len(search_terms) if search_terms else 0
        
        # Boost for exact phrase matches
        phrase_boost = 0.3 if query_text.lower() in text_lower else 0.0
        
        return min(1.0, base_score + phrase_boost)
        
    except Exception as e:
        print(f"Error calculating text relevance: {str(e)}")
        return 0.0

def _get_match_reason(row: dict, query_text: str, search_terms: set) -> str:
    """Generate a human-readable reason for why a row matched."""
    try:
        row_text = " ".join(str(value).lower() for value in row.values() if value is not None)
        
        # Find which terms matched
        matched_terms = [term for term in search_terms if term in row_text]
        
        # Special handling for assignment queries
        if "assigned" in query_text.lower() and "to" in query_text.lower():
            # Look for name matches in the row
            name_matches = []
            for term in search_terms:
                if len(term) > 2 and term in row_text:
                    name_matches.append(term)
            
            if name_matches:
                return f"Assigned to: {', '.join(name_matches[:2])}"
            elif any(field in row_text for field in ['assigned', 'assignee', 'owner']):
                return "Contains assignment information"
        
        # Special handling for count queries
        elif "count" in query_text.lower():
            if matched_terms:
                return f"Countable items: {', '.join(matched_terms[:2])}"
        
        # Special handling for list queries
        elif "list" in query_text.lower():
            if matched_terms:
                return f"List items: {', '.join(matched_terms[:2])}"
        
        # General matching
        if matched_terms:
            return f"Matches: {', '.join(matched_terms[:3])}"
        else:
            return "Relevant data found"
            
    except Exception as e:
        return "Relevant data found"

# Report generation helper functions
async def _generate_report_content(result: dict) -> dict:
    """Generate structured report content from query result."""
    query = result.get("query", "Unknown Query")
    summary = result.get("summary", "No summary available")
    evidence = result.get("evidence", [])
    created_at = result.get("created_at", "")
    
    # Extract key findings from evidence
    findings = []
    sources = set()
    
    for item in evidence:
        source_type = item.get("source_type", "unknown")
        if source_type == "document":
            sources.add("documents")
        elif source_type == "github":
            sources.add("github")
        elif source_type == "jira":
            sources.add("jira")
        
        title = item.get("title", "Untitled")
        description = item.get("description", "No description")
        confidence = item.get("confidence_score", 0)
        
        findings.append({
            "title": title,
            "description": description,
            "source": item.get("source", "Unknown"),
            "confidence": confidence,
            "data": item.get("data", {})
        })
    
    return {
        "title": f"Evidence Report: {query[:50]}{'...' if len(query) > 50 else ''}",
        "query": query,
        "summary": summary,
        "findings": findings,
        "sources": list(sources),
        "evidence_count": len(evidence),
        "created_at": created_at,
        "generated_at": datetime.now().isoformat()
    }


async def _generate_txt_report(report_content: dict) -> str:
    """Generate TXT report content."""
    lines = []
    lines.append("=" * 80)
    lines.append(report_content["title"])
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("QUERY:")
    lines.append("-" * 40)
    lines.append(report_content["query"])
    lines.append("")
    
    lines.append("SUMMARY:")
    lines.append("-" * 40)
    lines.append(report_content["summary"])
    lines.append("")
    
    lines.append("KEY FINDINGS:")
    lines.append("-" * 40)
    
    if report_content["findings"]:
        for i, finding in enumerate(report_content["findings"], 1):
            lines.append(f"{i}. {finding['title']}")
            lines.append(f"   Source: {finding['source']}")
            lines.append(f"   Description: {finding['description']}")
            lines.append(f"   Confidence: {finding['confidence']:.2f}")
            lines.append("")
    else:
        lines.append("No findings available.")
        lines.append("")
    
    lines.append("REPORT METADATA:")
    lines.append("-" * 40)
    lines.append(f"Generated on: {report_content['generated_at']}")
    lines.append(f"Sources: {', '.join(report_content['sources'])}")
    lines.append(f"Evidence Count: {report_content['evidence_count']}")
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)

async def _generate_json_report(report_content: dict) -> str:
    """Generate JSON report content."""
    import json
    
    # Create a structured JSON report
    json_report = {
        "report_metadata": {
            "title": report_content["title"],
            "query": report_content["query"],
            "generated_at": report_content["generated_at"],
            "created_at": report_content["created_at"],
            "sources": report_content["sources"],
            "evidence_count": report_content["evidence_count"]
        },
        "summary": report_content["summary"],
        "findings": report_content["findings"],
        "export_info": {
            "format": "JSON",
            "version": "1.0",
            "generated_by": "Evidence-on-Demand Bot"
        }
    }
    
    return json.dumps(json_report, indent=2, ensure_ascii=False)
