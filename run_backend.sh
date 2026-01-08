#!/bin/bash

# Materials Explorer Backend Setup & Run Script
# This script sets up SQLite database and starts the FastAPI server

set -e  # Exit on any error

echo "🚀 Materials Explorer Backend Setup"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    echo "❌ Error: Please run this script from the materials-explorer root directory"
    exit 1
fi

# Create/activate virtual environment
echo "📦 Setting up Python environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables
export MP_API_KEY="4qLIaDzBfyUgYLrnh6mu9tOsGbAshwYG"
export DEBUG="true"
export DATABASE_URL="sqlite+aiosqlite:///./materials_explorer.db"

echo "🗄️  Database setup..."

# Remove old database if it exists (for fresh start)
if [ -f "materials_explorer.db" ]; then
    echo "Removing existing database for fresh start..."
    rm materials_explorer.db
fi

# Change to backend directory
cd backend

echo "🔧 Creating database tables..."
# The database tables will be created automatically by the lifespan handler in main.py

echo "🌟 Starting FastAPI development server..."
echo ""
echo "API will be available at:"
echo "  🌐 Main API: http://localhost:8000"
echo "  📖 API Docs: http://localhost:8000/docs"
echo "  📋 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload