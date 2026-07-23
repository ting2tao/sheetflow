#!/bin/bash

# SheetFlow Development Startup Script

echo "🚀 Starting SheetFlow Development Environment"
echo "=============================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip3 install -r requirements.txt -q

# Install Playwright browsers if needed
if ! playwright install --dry-run 2>/dev/null; then
    echo "🌐 Installing Playwright Chromium..."
    playwright install chromium
fi

# Start backend in background
echo "🔧 Starting backend server..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install -q

# Start frontend
echo "🎨 Starting frontend server..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ SheetFlow is running!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
