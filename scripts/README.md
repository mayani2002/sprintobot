# Scripts Directory

This directory contains utility scripts for SprintoBot setup, development, and deployment.

## Available Scripts

### setup.sh
Initial project setup script that:
- Creates necessary directories
- Sets up Python virtual environment
- Installs backend dependencies
- Installs frontend dependencies
- Creates default configuration files

**Usage:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### start-dev.sh
Development server startup script that:
- Starts FastAPI backend on port 8000
- Starts React frontend on port 3000
- Provides graceful shutdown on Ctrl+C

**Usage:**
```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

### deploy.sh
Production deployment preparation script that:
- Builds React frontend for production
- Generates requirements.txt
- Creates production environment template

**Usage:**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## Windows Users

For Windows users, you can use Git Bash or WSL to run these scripts, or create equivalent `.bat` files:

### setup.bat
```batch
@echo off
echo Setting up SprintoBot...
mkdir logs config uploads exports 2>nul
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
cd ..\frontend
npm install
cd ..
echo Setup complete!
```

### start-dev.bat
```batch
@echo off
echo Starting development servers...
start cmd /k "cd backend && call venv\Scripts\activate && uvicorn main:app --reload --port 8000"
timeout /t 3
start cmd /k "cd frontend && npm start"
echo Servers started!
```

## Script Permissions

Make scripts executable on Unix-like systems:
```bash
chmod +x scripts/*.sh
```
