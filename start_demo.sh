#!/bin/bash

# Complete Materials Explorer Demo Startup Script
echo "🚀 Materials Explorer Demo Startup"
echo "==================================="

# Kill any existing processes on the ports we need
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "react-scripts.*3000" 2>/dev/null || true
sleep 2

# Check if we're in the right directory
if [ ! -f "run_backend.sh" ]; then
    echo "❌ Error: Please run this script from the materials-explorer root directory"
    exit 1
fi

echo "📊 Loading sample data (if needed)..."
if [ ! -f "materials_explorer.db" ]; then
    echo "No database found, loading sample materials..."
    python3 load_sample_data.py
else
    echo "Database exists, skipping sample data load"
fi

echo "🔧 Starting backend..."
# Start backend in background
./run_backend.sh &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 8

# Test if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running at http://localhost:8000"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo "🌐 Starting frontend..."
cd frontend

# Start frontend in background
npm start &
FRONTEND_PID=$!

echo ""
echo "🎉 Materials Explorer is starting up!"
echo ""
echo "📍 Available URLs:"
echo "  🌐 Frontend:  http://localhost:3000"
echo "  🔧 Backend:   http://localhost:8000"
echo "  📖 API Docs:  http://localhost:8000/docs"
echo ""
echo "⏳ Frontend is starting... (may take 30-60 seconds)"
echo ""
echo "🔍 To test the 3D viewer:"
echo "  1. Go to http://localhost:3000"
echo "  2. Click on any material (e.g., 'mp-149' for Silicon)"
echo "  3. Scroll down to see the 3D crystal structure"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "react-scripts.*3000" 2>/dev/null || true
    echo "👋 Goodbye!"
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Wait for user to press Ctrl+C
wait