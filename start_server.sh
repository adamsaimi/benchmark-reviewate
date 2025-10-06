#!/bin/bash

# Benchmark API Startup Script

echo "🚀 Starting Benchmark API..."

# Load environment variables
if [ -f .env ]; then
    echo "� Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found, using default values..."
    cp .env.example .env
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start PostgreSQL with Docker Compose
echo "� Starting PostgreSQL database..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Start the API server
echo "✨ Starting FastAPI server on ${HOST}:${PORT}..."
uvicorn benchmark.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --reload

echo "✅ All tests passed!"

# Start the server
echo "🌐 Starting server on http://127.0.0.1:8000"
echo "📖 API documentation available at http://127.0.0.1:8000/docs"
echo "🛑 Press Ctrl+C to stop the server"

uvicorn app:app --reload --port 8000

echo "✅ All tests passed!"

# Start the server
echo "🌐 Starting server on http://127.0.0.1:8000"
echo "📖 API documentation available at http://127.0.0.1:8000/docs"
echo "🛑 Press Ctrl+C to stop the server"

uvicorn app:app --reload --port 8000