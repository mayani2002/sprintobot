<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# AI-Powered Evidence-on-Demand Bot

This project is an AI-driven assistant that instantly fetches and formats required evidence from various systems during audits, compliance checks, or incident investigations.

## Project Architecture
- **Backend**: Python FastAPI for API endpoints and AI processing
- **Frontend**: React for the web UI with natural language input
- **AI Components**: OpenAI/LangChain for natural language processing
- **Integrations**: GitHub API, JIRA API for evidence retrieval
- **Document Processing**: PDF/Excel/CSV parsing for non-API sources
- **Export**: CSV/XLS file generation capabilities

## Development Guidelines
- Use FastAPI for backend API development
- Implement proper error handling and logging
- Follow security best practices for API integrations
- Use environment variables for sensitive configuration
- Implement rate limiting for external API calls
- Use type hints throughout Python code
- Write comprehensive tests for all components

## Core Features
1. Natural language query processing
2. GitHub integration (PR status, approvals)
3. JIRA integration (ticket workflows, approvals)
4. Document parsing (PDF, Excel, CSV)
5. Evidence export functionality
6. Auditor-friendly response formatting

## Project Status
✅ **COMPLETED** - Project workspace successfully created and configured
✅ Backend API running on http://localhost:8000
✅ Frontend React app running on http://localhost:3000
✅ Both development servers are operational

## Quick Start
1. **Backend**: Already running at http://localhost:8000
2. **Frontend**: Already running at http://localhost:3000
3. **API Documentation**: Visit http://localhost:8000/docs

## Configuration Required
To enable full functionality, configure these API keys in `config/.env`:
- `OPENAI_API_KEY`: For AI-powered query processing
- `GITHUB_TOKEN`: For GitHub integration
- `JIRA_API_TOKEN`: For JIRA integration

## Next Steps
1. Configure API keys for external integrations
2. Test sample queries in the web interface
3. Upload sample documents for document parsing
4. Customize AI prompts for your organization
5. Add additional integrations as needed
