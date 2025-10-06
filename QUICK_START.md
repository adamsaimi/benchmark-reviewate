# 🚀 Quick Start Guide

## Prerequisites Checklist
- ✅ Python 3.9+ installed
- ✅ Docker and Docker Compose installed
- ✅ Git installed

## Setup in 3 Steps

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Start Database & Run Migrations
```bash
docker-compose up -d postgres
sleep 3
alembic upgrade head
```

### 3️⃣ Run the Application
```bash
uvicorn benchmark.main:app --reload
```

**Or use the all-in-one script:**
```bash
chmod +x start_server.sh
./start_server.sh
```

## Verify Everything Works

### Run Tests
```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Access the API
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000

## Quick Commands

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Stop PostgreSQL  
docker-compose stop

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Run tests
pytest tests/ -v

# Start API server
uvicorn benchmark.main:app --reload --port 8000
```

## Test the API

```bash
# Health check
curl http://localhost:8000

# Create a post
curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "This is my first post content",
    "author_email": "user@example.com"
  }'

# Get all posts
curl http://localhost:8000/posts/

# Get specific post (replace 1 with actual ID)
curl http://localhost:8000/posts/1
```

## Troubleshooting

### Port already in use
```bash
# Check what's using port 5432
lsof -i :5432

# Or use different port in docker-compose.yml
```

### Database connection error
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check logs
docker-compose logs postgres
```

### Migration errors
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

## What's Next?

1. Check out `BENCHMARK.md` for the benchmarking framework
2. Read `IMPLEMENTATION_SUMMARY.md` for architecture details
3. Explore the API docs at http://localhost:8000/docs

---

**Ready to go!** 🎉
