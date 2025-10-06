#!/bin/bash

# Test Runner Script

echo "🧪 Running tests..."

# Load test environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start test database
echo "🐘 Starting test PostgreSQL database..."
docker-compose up -d postgres_test

# Wait for database to be ready
echo "⏳ Waiting for test database to be ready..."
sleep 3

# Run pytest
echo "🔬 Running pytest..."
pytest tests/ -v

# Capture exit code
TEST_EXIT_CODE=$?

# Stop test database
echo "🛑 Stopping test database..."
docker-compose stop postgres_test

# Exit with test result
exit $TEST_EXIT_CODE
