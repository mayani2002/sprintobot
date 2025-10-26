# Backend Setup Guide

## Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
cd backend
python setup_dependencies.py
```

This script will:
1. Check which packages are installed
2. Install missing packages
3. Verify all critical imports work

### Option 2: Manual Setup

```bash
cd backend
pip install -r requirements.txt
```

## Required Packages

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.104.1 | Web framework |
| uvicorn | 0.24.0 | ASGI server |
| python-dotenv | 1.0.0 | Environment variables |
| PyGithub | 2.1.1 | GitHub API wrapper |
| google-genai | 1.0.0 | Google Gemini AI |
| pydantic | 2.5.0 | Data validation |
| requests | 2.31.0 | HTTP library |
| pandas | 2.1.3 | Data processing |

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'github'`

**Solution:**
```bash
pip install PyGithub
```

### Issue: `ModuleNotFoundError: No module named 'google.genai'`

**Solution:**
```bash
pip install google-genai
```

### Issue: `ModuleNotFoundError: No module named 'dotenv'`

**Solution:**
```bash
pip install python-dotenv
```

## Verify Installation

Run the verification script:
```bash
python setup_dependencies.py
```

Or manually test imports:
```python
python -c "from github import Github; print('PyGithub OK')"
python -c "from google import genai; print('Gemini OK')"
python -c "from fastapi import FastAPI; print('FastAPI OK')"
```

## Running Tests

After installation:
```bash
# Test GitHub integration only (no AI calls)
python test_github_integration_only.py

# Test new AI system
python test_with_new_ai.py

# Test service with AI
python test_github_service.py
```

## Environment Configuration

Make sure `config/.env` exists with:
```properties
GITHUB_TOKEN=your_github_token
GEMINI_API_KEY=your_gemini_key
USE_GEMINI=true
GEMINI_MODEL=gemini-2.0-flash-exp
```

## Starting the Server

```bash
uvicorn app.main:app --reload --port 8000
```

API docs will be available at: http://localhost:8000/docs
