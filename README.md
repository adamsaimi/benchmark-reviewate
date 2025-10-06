# Benchmark API

A production-ready FastAPI application for managing blog posts with PostgreSQL database, Alembic migrations, and comprehensive testing.

## 🚀 Features

- **FastAPI Framework**: Modern, fast (high-performance) web framework
- **PostgreSQL Database**: Robust relational database with SQLAlchemy ORM
- **Alembic Migrations**: Database schema version control
- **Dependency Injection**: Clean architecture with proper DI pattern
- **Comprehensive Testing**: Unit and integration tests with pytest
- **Docker Support**: Containerized PostgreSQL for development and testing
- **Type Safety**: Full type hints and Pydantic validation

## Project Structure

```
benchmark/
├── alembic/                  # Database migrations
│   ├── versions/            # Migration files
│   └── env.py               # Alembic environment
├── benchmark/               # Main application package
│   ├── routers/            # API route handlers
│   ├── services/           # Business logic layer
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database connection
│   ├── main.py            # FastAPI app initialization
│   ├── models.py          # SQLAlchemy models
│   └── schemas.py         # Pydantic schemas
├── tests/                  # Test suite
│   ├── conftest.py        # Test fixtures
│   ├── test_api.py        # API endpoint tests
│   └── test_services.py   # Service layer tests
├── docker-compose.yml     # Docker services
├── alembic.ini           # Alembic configuration
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Benchmarking Framework

The benchmarking framework is explained in detail in the `BENCHMARK.md` file. It provides instructions on how to set up the environment, create pull requests with AI-generated and ground truth reviews, and run the benchmark to evaluate performance using precision, recall, and F1 score metrics.

## 📋 Prerequisites

- Python 3.9+
- Docker and Docker Compose
- pip (Python package manager)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd benchmark
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 🐘 Database Setup

1. **Start PostgreSQL with Docker**
   ```bash
   docker-compose up -d postgres
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

   Or use the migration script:
   ```bash
   chmod +x migrate.sh
   ./migrate.sh
   ```

## 🎯 Running the Application

### Option 1: Using the startup script (Recommended)
```bash
chmod +x start_server.sh
./start_server.sh
```

### Option 2: Manual start
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Start the API
uvicorn benchmark.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

When the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🧪 Testing

### Run all tests
```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Run tests manually
```bash
# Start test database
docker-compose up -d postgres_test

# Run pytest
pytest tests/ -v

# Stop test database
docker-compose stop postgres_test
```

## Validation Rules

- **Title**: 3-100 characters
- **Content**: Maximum 10,000 characters  
- **Author Email**: Valid email format (validated by Pydantic)

## 🔧 Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://benchmark_user:benchmark_password@localhost:5432/benchmark_db
TEST_DATABASE_URL=postgresql://benchmark_user:benchmark_password@localhost:5433/benchmark_test_db

# API
API_TITLE=Benchmark API
API_DESCRIPTION=A pristine FastAPI application for managing blog posts
API_VERSION=1.0.0

# Server
HOST=0.0.0.0
PORT=8000
```

## 🔄 Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

## 📝 API Endpoints

### Posts

- `POST /posts/` - Create a new post
- `GET /posts/` - Get all posts
- `GET /posts/{post_id}` - Get a specific post by ID
- `GET /` - Health check endpoint

## 🏗️ Architecture Principles

The application follows clean architecture principles:

1. **Separation of Concerns**: Clear distinction between HTTP layer (routers) and business logic (services)
2. **API Layer** (`routers/`): Handles HTTP requests/responses
3. **Service Layer** (`services/`): Contains business logic
4. **Data Layer** (`models.py`): Database models with SQLAlchemy
5. **Schema Layer** (`schemas.py`): Data validation with Pydantic
6. **Strong Typing**: Comprehensive type hints throughout the codebase
7. **Explicit Contracts**: Pydantic schemas define clear data contracts
8. **Error Handling**: Custom exceptions with proper HTTP status code mapping
9. **Clean Code**: Google-style docstrings, descriptive naming
10. **Testability**: Complete test coverage with unit and integration tests

## 🛡️ Error Handling

- Proper exception handling with custom exceptions
- Pydantic validation for request data
- SQLAlchemy error handling with rollback
- HTTP status codes following REST conventions

## 🧹 Code Quality

- Type hints throughout the codebase
- Comprehensive docstrings
- Separation of concerns
- Dependency injection pattern
- Clean, maintainable code structure

## Development Notes

- The code is designed to be exemplary and serve as a baseline for introducing controlled flaws for testing purposes
- All dependencies are pinned to specific versions for reproducibility

## 📄 License

This project is part of a benchmark suite for review agents.