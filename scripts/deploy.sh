#!/bin/bash

# SprintoBot Deployment Script
echo "🚀 Deploying SprintoBot..."

# Build frontend
echo "📦 Building React frontend..."
cd frontend
npm run build
cd ..

# Backend deployment preparation
echo "🐍 Preparing backend for deployment..."
cd backend
pip freeze > requirements.txt
cd ..

# Create production environment file
if [ ! -f config/.env.production ]; then
    echo "📝 Creating production environment template..."
    cat > config/.env.production << EOL
# Production API Configuration
OPENAI_API_KEY=
GITHUB_TOKEN=
JIRA_API_TOKEN=
JIRA_SERVER_URL=

# Production Database
DATABASE_URL=

# Security (generate strong keys for production)
SECRET_KEY=

# CORS Settings
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Logging
LOG_LEVEL=INFO
EOL
    echo "⚠️  Please configure config/.env.production with production values"
fi

echo "✅ Deployment preparation complete!"
echo "📋 Manual steps required:"
echo "1. Configure production environment variables"
echo "2. Deploy backend to your hosting platform"
echo "3. Deploy frontend build files to your web server"
echo "4. Configure reverse proxy if needed"
