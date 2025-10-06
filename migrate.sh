#!/bin/bash

# Database Migration Script

echo "🔄 Running database migrations..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic is not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run migrations
alembic upgrade head

echo "✅ Database migrations completed successfully!"
