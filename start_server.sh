#!/bin/bash

# Benchmark API Startup Script
# This script sets up and runs the FastAPI application

set -e

echo "🚀 Starting Benchmark API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

#!/bin/bash

# Benchmark API Startup Script
# This script sets up and runs the FastAPI application

set -e

echo "🚀 Starting Benchmark API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
pytest tests/

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