#!/bin/bash

# SprintoBot Setup Script
echo "🚀 Setting up SprintoBot..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p config
mkdir -p uploads
mkdir -p exports

# Backend setup
echo "🐍 Setting up Python backend..."
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create config file if it doesn't exist
if [ ! -f ../config/.env ]; then
    echo "📝 Creating environment configuration..."
    cat > ../config/.env << EOL
# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
GITHUB_TOKEN=your_github_token_here
JIRA_API_TOKEN=your_jira_token_here
JIRA_SERVER_URL=your_jira_server_url_here

# Database
DATABASE_URL=sqlite:///./sprintobot.db

# Security
SECRET_KEY=your_secret_key_here
EOL
fi

cd ..

# Frontend setup
echo "⚛️ Setting up React frontend..."
cd frontend
npm install
cd ..

echo "✅ Setup complete!"
echo "📋 Next steps:"
echo "1. Configure API keys in config/.env"
echo "2. Run 'scripts/start-dev.sh' to start development servers"
