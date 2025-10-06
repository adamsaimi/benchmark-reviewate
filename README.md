# Benchmark - AI Code Review Agent Evaluation Framework

A comprehensive benchmarking framework for evaluating AI-generated code reviews against ground truth reviews. This project includes a production-ready FastAPI application with PostgreSQL, along with a systematic methodology for scoring review agent performance.

## 🎯 Overview

This benchmark evaluates AI code review agents by:
1. Creating pull requests with intentional flaws
2. Collecting AI-generated reviews from your agent
3. Comparing them against ground truth reviews
4. Calculating precision, recall, and F1 scores

**Quick Navigation:**
- 📖 [How to Run the Benchmark](#-running-the-benchmark)
- 📊 [Scoring Methodology](#-scoring-methodology)
- 🗂️ [Issue Taxonomy](#%EF%B8%8F-taxonomy)
- 🏗️ [Architecture](#%EF%B8%8F-architecture)

### 🚀 Key Features

- **Automated PR Generation**: Creates PRs with known flaws across multiple categories
- **Ground Truth Reviews**: Pre-defined correct reviews for each flaw
- **LLM-Based Validation**: Semantic matching of review comments
- **Detailed Scoring**: Precision, recall, F1-score with stratified analysis
- **Comprehensive Taxonomy**: Covers security, performance, business logic, async, testing, and more
- **Production-Ready Baseline**: Clean FastAPI application with PostgreSQL and proper architecture

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

## 📋 Prerequisites

- Python 3.9+
- GitHub account (for benchmarking)
- Gemini API key (for scoring)
- GitHub token (for PR creation)

## 🏗️ Architecture

The baseline application is a production-ready FastAPI project with:

- **Clean Architecture**: Layered design (API → Service → Data)
- **PostgreSQL Database**: SQLAlchemy ORM with Alembic migrations
- **Dependency Injection**: Proper DI pattern throughout
- **Type Safety**: Full type hints and Pydantic validation
- **Comprehensive Tests**: Isolated database fixtures

This provides a pristine codebase against which PRs with flaws are compared.

---

## 🧪 Running the Benchmark

### 1. Fork and Clone

1. **Fork this repository** on GitHub (disable "copy only main branch")
2. **Clone your fork:**
   ```bash
   git clone https://github.com/your-username/benchmark.git
   cd benchmark
   ```

### 2. Set Up Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export API_KEY="your-gemini-api-key"
export GITHUB_TOKEN="your-github-token"
```

### 3. Create Pull Requests

Generate PRs with intentional flaws and ground truth reviews:

```bash
python create_pull_requests.py
```

This creates multiple PRs, each containing:
- Code with intentional flaws (security, performance, business logic, etc.)
- Ground truth reviews in JSON format
- Metadata about the flaw category and difficulty

### 4. Run Your AI Review Agent

Configure your AI code review agent to review the generated PRs. This step depends on your setup:
- **GitHub Actions**: Use workflow triggers
- **Webhooks**: Set up PR event listeners
- **Manual**: Run your agent on each PR

### 5. Score the Results

Compare AI-generated reviews against ground truth:

```bash
python score/main.py your-username/benchmark
```

This will:
1. Fetch all PRs from your repository
2. Extract AI-generated reviews
3. Compare with ground truth using LLM validation
4. Calculate precision, recall, and F1 scores
5. Generate detailed reports

---

## 📊 Scoring Methodology

### Core Metrics

The benchmark uses standard classification metrics:

#### Precision
Measures the reliability of the agent's reviews (low noise):
```
Precision = TP / (TP + FP)
```

#### Recall
Measures the thoroughness of the agent (high coverage):
```
Recall = TP / (TP + FN)
```

#### F1-Score
Harmonic mean providing balanced effectiveness:
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

Where:
- **TP (True Positive)**: Correct flaw identified by agent
- **FP (False Positive)**: Incorrect/irrelevant finding by agent
- **FN (False Negative)**: Missed flaw

### Matching Algorithm

A review is considered a **match** if:

1. **Location Match**: Same file and line (±2 line tolerance)
   ```
   Match_loc(g, a) ⟺ (g.file = a.file) ∧ (|g.line - a.line| ≤ 2)
   ```

2. **Semantic Match**: LLM validates same underlying issue
   ```
   Match_sem(g, a) ⟺ LLM_Validate(g.comment, a.comment) = true
   ```

3. **Overall Match**: Both conditions met
   ```
   Match(g, a) = Match_loc(g, a) ∧ Match_sem(g, a)
   ```

### Stratified Analysis

Beyond overall scores, the benchmark provides granular analysis:

- **By Category**: Security, Performance, Business Logic, Async, etc.
- **By Difficulty**: Easy, Medium, Hard
- **By Context Size**: Small vs. large PRs

This reveals specific strengths and weaknesses of the review agent.

---

## 🗂️ Taxonomy

The benchmark uses a comprehensive taxonomy of code review issues:

| Category | Code | Description | Example Issues |
|----------|------|-------------|----------------|
| **Security** | SEC | Security vulnerabilities | SQL injection, XSS, auth bypass |
| **Performance** | PERF | Performance issues | N+1 queries, memory leaks |
| **Business Logic** | BIZ | Domain logic errors | Calculation errors, workflow bugs |
| **Architecture** | ARCH | Design problems | Tight coupling, missing abstractions |
| **Python Best Practices** | PY | Language-specific | Non-Pythonic code, type hints |
| **Async/Concurrency** | ASYNC | Concurrency issues | Race conditions, deadlocks |
| **Testing** | TEST | Test quality | Missing tests, poor coverage |
| **Logging** | LOG | Observability | Missing logs, sensitive data |
| **Readability** | READ | Code clarity | Complex logic, naming issues |

Each category has multiple difficulty levels (Easy, Medium, Hard) to comprehensively test agent capabilities.

---

## 📈 Example Output

```
Benchmark Results for your-username/benchmark
=============================================

Overall Performance:
  Precision: 0.85
  Recall: 0.78
  F1-Score: 0.81

By Category:
  Security   - P: 0.90, R: 0.80, F1: 0.85
  Performance- P: 0.82, R: 0.75, F1: 0.78
  Business   - P: 0.80, R: 0.70, F1: 0.75
  ...

By Difficulty:
  Easy   - P: 0.95, R: 0.90, F1: 0.92
  Medium - P: 0.85, R: 0.75, F1: 0.80
  Hard   - P: 0.70, R: 0.60, F1: 0.65
```

---

##  License

This project is part of a benchmark suite for evaluating AI code review agents.