# Evidence-on-Demand Bot Documentation

## Architecture Overview

The Evidence-on-Demand Bot is built with a modern, scalable architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │  External APIs  │
│                 │    │                 │    │                 │
│  • Query Input  │◄──►│  • AI Processing │◄──►│  • GitHub API   │
│  • Results UI   │    │  • Evidence API  │    │  • JIRA API     │
│  • File Upload  │    │  • File Parsing  │    │  • OpenAI API   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. AI Service (`ai_service.py`)
- Processes natural language queries using OpenAI GPT-4
- Extracts intent and parameters from user questions
- Formats evidence into human-readable summaries

### 2. Integration Services
- **GitHub Integration**: Fetches PR data, reviews, approvals
- **JIRA Integration**: Retrieves tickets, workflows, permissions
- **Document Parser**: Processes PDF, Excel, CSV files

### 3. Evidence Service (`evidence_service.py`)
- Stores and retrieves query results
- Handles evidence export to multiple formats
- Manages evidence metadata and confidence scores

### 4. API Layer (`evidence.py`)
- RESTful endpoints for evidence retrieval
- File upload handling
- Query routing and response formatting

## API Endpoints

### Query Submission
```http
POST /api/v1/evidence/query
Content-Type: application/json

{
  "query": "Why was PR #456 merged without approval?",
  "query_type": "github",
  "filters": {
    "repo": "main-app",
    "pr_number": 456
  }
}
```

**Note:** The API accepts both `query_type` and `source` fields for backward compatibility. If both are provided, `query_type` takes precedence.

### Evidence Retrieval
```http
GET /api/v1/evidence/evidence/{query_id}
```

### Evidence Export
```http
POST /api/v1/evidence/export/{query_id}
Content-Type: application/json

{
  "query_id": "uuid-here",
  "format": "xlsx",
  "include_metadata": true
}
```

### Document Upload
```http
POST /api/v1/evidence/documents/upload
Content-Type: multipart/form-data

file: <binary-data>
```

## Query Processing Flow

1. **Query Analysis**: AI service analyzes the natural language query
2. **Intent Extraction**: Determines query type (github, jira, document, mixed)
3. **Parameter Extraction**: Extracts specific entities (PR numbers, ticket keys, etc.)
4. **Evidence Retrieval**: Routes to appropriate integration services
5. **Evidence Formatting**: AI formats results for audit presentation
6. **Response Generation**: Returns structured evidence with confidence scores

## Evidence Data Structure

```json
{
  "source": "github",
  "source_type": "github",
  "title": "PR #456: Add user authentication",
  "description": "Status: merged, Approval: approved (2 approvals)",
  "data": {
    "number": 456,
    "title": "Add user authentication",
    "state": "merged",
    "approval_status": "approved (2 approvals)",
    "reviews": [...],
    "url": "https://github.com/org/repo/pull/456"
  },
  "confidence_score": 0.95,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Configuration

### Environment Variables
See `config/.env.example` for all configuration options.

### Required API Keys
- **OpenAI API Key**: For natural language processing
- **GitHub Token**: For GitHub API access
- **JIRA Credentials**: For JIRA API access

## Deployment

### Development
```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm start
```

### Production
```bash
# Build frontend
cd frontend && npm run build

# Run with Docker
docker-compose up -d
```

## Security Considerations

1. **API Key Management**: Store in environment variables, never commit to code
2. **Rate Limiting**: Implement rate limiting for external API calls
3. **Input Validation**: Sanitize all user inputs
4. **File Upload Security**: Validate file types and sizes
5. **Access Control**: Implement proper authentication and authorization

## Performance Optimization

1. **Caching**: Cache API responses to reduce external calls
2. **Async Processing**: Use async/await for concurrent operations
3. **Database Indexing**: Index frequently queried fields
4. **File Processing**: Process large files in chunks
5. **API Rate Limits**: Respect external API rate limits

## Monitoring and Logging

1. **Query Logging**: Log all queries for audit trails
2. **Error Tracking**: Track and alert on API failures
3. **Performance Metrics**: Monitor response times and success rates
4. **Usage Analytics**: Track query types and patterns

## Testing

### Unit Tests
```bash
cd backend && python -m pytest tests/unit/
```

### Integration Tests
```bash
cd backend && python -m pytest tests/integration/
```

### Frontend Tests
```bash
cd frontend && npm test
```

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Check API key and rate limits
2. **GitHub Integration Fails**: Verify token permissions
3. **JIRA Connection Issues**: Check URL and credentials
4. **File Upload Errors**: Verify file size and format

### Debug Mode
Set `DEBUG=true` in environment to enable verbose logging.

## Future Enhancements

1. **Slack Integration**: Allow queries via Slack commands
2. **Additional Integrations**: Azure DevOps, Confluence, etc.
3. **Advanced AI Features**: Query clarification, multi-step reasoning
4. **Real-time Notifications**: Alert on specific evidence patterns
5. **Mobile App**: Mobile interface for evidence queries
