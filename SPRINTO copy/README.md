# AI-Powered Evidence-on-Demand Bot

An AI-driven assistant that instantly fetches and formats required evidence from various systems during audits, compliance checks, or incident investigations.

## Features

### Core Functionality
- **Natural Language Query Processing**: Accept queries from auditors via web UI input box
- **API-Based Evidence Retrieval**: Integrate with GitHub and JIRA APIs for real-time data
- **Document-Based Evidence Retrieval**: Parse PDF, Excel, and CSV files for non-API sources
- **AI-Powered Query Understanding**: Interpret and clarify vague queries
- **Multi-Format Export**: Generate CSV, XLS, and JSON reports
- **Auditor-Friendly Formatting**: Structured, professional evidence presentation

### Supported Integrations
- **GitHub**: PR status, approval workflows, merge history
- **JIRA**: Ticket workflows, approvals, access management
- **Document Sources**: Office asset registers, invoices, compliance documents

## Architecture

```
evidence-bot/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core business logic
│   │   ├── integrations/   # External API integrations
│   │   ├── models/         # Data models
│   │   └── services/       # Service layer
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── documents/              # Sample documents for testing
├── config/                 # Configuration files
└── docs/                   # Documentation
```

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd evidence-bot
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment variables**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your API keys
   ```

5. **Run the application**
   ```bash
   # Terminal 1: Backend
   cd backend
   uvicorn app.main:app --reload

   # Terminal 2: Frontend
   cd frontend
   npm start
   ```

## Environment Variables

Create a `config/.env` file with the following variables:

```env
# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here
AI_MODEL=gpt-4

# GitHub Integration
GITHUB_TOKEN=your_github_token_here
GITHUB_ORG=your_organization_name

# JIRA Integration
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your_email@company.com
JIRA_API_TOKEN=your_jira_api_token

# Database (optional)
DATABASE_URL=sqlite:///./evidence_bot.db

# API Configuration
API_HOST=localhost
API_PORT=8000
FRONTEND_URL=http://localhost:3000
```

## Usage Examples

### Example Queries

1. **GitHub Integration**
   - "Why was PR #456 merged without approval?"
   - "Show me all PRs merged by John Doe last week"
   - "List pending code reviews for the main branch"

2. **JIRA Integration**
   - "Access was given to Jane to read access to Prod DB"
   - "Show approval workflow for ticket PROJ-123"
   - "List all high-priority tickets assigned to DevOps team"

3. **Document-Based Queries**
   - "Share the current count of laptops in the office and export to XLS"
   - "Find all invoices from vendor XYZ in Q3 2024"
   - "Show asset depreciation report for IT equipment"

## API Endpoints

### Core Endpoints
- `POST /api/v1/query` - Submit natural language query
- `GET /api/v1/evidence/{query_id}` - Retrieve evidence results
- `GET /api/v1/export/{query_id}` - Export evidence to file

### Integration Endpoints
- `GET /api/v1/github/prs` - List GitHub pull requests
- `GET /api/v1/jira/tickets` - List JIRA tickets
- `POST /api/v1/documents/parse` - Parse uploaded documents

## Development

### Backend Development
```bash
cd backend
python -m pytest tests/  # Run tests
uvicorn app.main:app --reload --port 8000  # Development server
```

### Frontend Development
```bash
cd frontend
npm test  # Run tests
npm start  # Development server
npm run build  # Production build
```

### Adding New Integrations
1. Create integration module in `backend/app/integrations/`
2. Implement the integration interface
3. Add configuration variables
4. Write tests
5. Update documentation

## Testing

### Sample Test Queries
The application comes with sample documents and test data for demonstration:
- Asset register with laptop inventory
- Sample GitHub repository with PRs
- JIRA project with approval workflows

### Running Tests
```bash
# Backend tests
cd backend && python -m pytest

# Frontend tests
cd frontend && npm test

# Integration tests
python -m pytest tests/integration/
```

## Security Considerations

- API keys are stored in environment variables
- Rate limiting implemented for external API calls
- Input validation for all user queries
- Secure file upload handling
- Access logging for audit trails

## Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Manual Deployment
1. Build frontend: `cd frontend && npm run build`
2. Configure reverse proxy (nginx)
3. Set up SSL certificates
4. Configure environment variables
5. Start services with process manager (PM2, systemd)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For questions and support, please create an issue in the GitHub repository.
