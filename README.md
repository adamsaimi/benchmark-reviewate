# Benchmark API

A pristine, exemplary FastAPI application for managing blog posts. This project serves as a "golden copy" baseline with clean architecture, strong typing, and modern best practices.

## Project Structure

```
benchmark/
├── benchmark/                    # Main application package
│   ├── __init__.py
│   ├── main.py                  # FastAPI application instance
│   ├── config.py               # Configuration constants
│   ├── schemas.py              # Pydantic models
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   └── posts.py           # Post-related routes
│   └── services/              # Business logic
│       ├── __init__.py
│       └── post_service.py    # Post service implementation
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Test configuration and fixtures
│   ├── test_api.py           # API integration tests
│   └── test_services.py      # Service unit tests
├── app.py                    # Application entry point
├── requirements.txt          # Dependencies
├── pyproject.toml           # Project configuration
├── create_pull_requests.py  # Script to create the pull requests
├── SCORE.md                 # Scoring methodology document
├── BENCHMARK.md             # Benchmarking framework document
└── README.md                # This file
```

## Benchmarking Framework

The benchmarking framework is explained in detail in the `BENCHMARK.md` file. It provides instructions on how to set up the environment, create pull requests with AI-generated and ground truth reviews, and run the benchmark to evaluate performance using precision, recall, and F1 score metrics.

## Features

- **REST API** for managing posts with full CRUD operations
- **Strong typing** throughout with Pydantic models
- **Clean architecture** with separation of concerns (router vs service)
- **Robust error handling** with custom exceptions
- **Email validation** using Pydantic's EmailStr
- **Comprehensive field validation** with length constraints
- **Automatic API documentation** via FastAPI's OpenAPI integration
- **Complete test suite** with pytest

## Technology Stack

- **Python 3.12+** (compatible with 3.11+)
- **FastAPI 0.117.1** - Modern, fast web framework
- **Pydantic 2.11.9** - Data validation using Python type annotations
- **Uvicorn 0.37.0** - ASGI server implementation
- **Pytest 8.3.3** - Testing framework

## Quick Start

### 2. Manual Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Start the server
uvicorn app:app --reload --port 8000
```

## Validation Rules

- **Title**: 3-100 characters
- **Content**: Maximum 10,000 characters  
- **Author Email**: Valid email format (validated by Pydantic)

## Testing

The project includes comprehensive tests:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py

# Run with coverage (after installing pytest-cov)
pytest --cov=benchmark
```

## API Documentation

When the server is running, you can access:
- **Interactive API docs**: http://127.0.0.1:8000/docs
- **ReDoc documentation**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

## Architecture Principles

1. **Separation of Concerns**: Clear distinction between HTTP layer (routers) and business logic (services)
2. **Strong Typing**: Comprehensive type hints throughout the codebase
3. **Explicit Contracts**: Pydantic schemas define clear data contracts
4. **Error Handling**: Custom exceptions with proper HTTP status code mapping
5. **Clean Code**: Google-style docstrings, descriptive naming, and Black formatting standards
6. **Testability**: Complete test coverage with unit and integration tests

## Development Notes

- This application uses an in-memory database for simplicity
- In production, integrate with a real database using SQLAlchemy or similar ORM
- The code is designed to be exemplary and serve as a baseline for introducing controlled flaws for testing purposes
- All dependencies are pinned to specific versions for reproducibility