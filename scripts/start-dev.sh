#!/bin/bash

# SprintoBot Development Server Startup
echo "🚀 Starting SprintoBot development servers..."

# Function to check if port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
}

# Start backend server
echo "🐍 Starting FastAPI backend server..."
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "⚛️ Starting React frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Development servers started!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping development servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
