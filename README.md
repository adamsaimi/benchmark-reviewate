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
- **Dual-Agent LLM Validation**: Triage + Evaluation for accurate semantic matching
- **Decoupled Recall/Precision**: Separates coverage (finding issues) from quality (noise-free comments)
- **Weighted Severity Scoring**: Critical issues weighted 10x more than style nitpicks
- **8-Category Noise Detection**: Identifies verbosity, redundancy, over-engineering, hallucinations, etc.
- **Parallel Processing**: Multi-threaded evaluation for fast benchmark execution (35 concurrent workers)
- **Detailed Stratified Reports**: Analysis by category, difficulty, and noise type
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
1. Fetch all PRs from your repository (parallelized)
2. Extract AI-generated reviews
3. Decompose ground truth into atomic requirements with severity levels
4. Compare with ground truth using dual-agent LLM validation
5. Apply weighted scoring based on severity and quality
6. Calculate precision, recall, and F1 scores
7. Generate detailed reports with token usage statistics

**Performance**: The scoring process uses 70 parallel workers (configurable via `MAX_WORKERS` in `score/main.py`), enabling rapid evaluation of large benchmark suites.

---

## ⚙️ Configuration

### Adjusting Parallelization

The scoring script supports configurable parallelism for optimal performance:

```python
# In score/main.py
MAX_WORKERS = 35  # Number of concurrent evaluation threads
```

**Recommendations:**
- **Local testing**: 5-10 workers to avoid API rate limits
- **Production benchmarks**: 30-50 workers for maximum throughput
- **API constraints**: Adjust based on your Gemini API quota

**Trade-offs:**
- ⬆️ More workers = Faster execution, higher API costs
- ⬇️ Fewer workers = Slower execution, lower risk of rate limiting

### Severity Weight Customization

Modify severity weights to match your priorities:

```python
# In score/main.py
SEVERITY_WEIGHTS = {
    "Critical": 10.0,  # Security, data integrity
    "Major": 5.0,      # Performance, business logic
    "Minor": 2.0,      # Code quality
    "Style": 1.0       # Formatting, conventions
}
```

---

## 📊 Scoring Methodology

### Dual-Agent Evaluation System

The benchmark employs a sophisticated two-agent approach for accurate evaluation:

#### Agent 1: Triage Architect
- **Purpose**: Decomposes ground truth reviews into atomic requirements
- **Output**: List of independent, actionable feedback points with assigned severity
- **Benefit**: Enables fine-grained matching and prevents conflating multiple issues

#### Agent 2: Evaluation Analyst
- **Purpose**: Matches agent comments to requirements and scores noise
- **Process**:
  1. Scores each rubric requirement based on agent's coverage (0.0-1.0 quality score)
  2. Assigns noise score to each comment (0.0=perfect, 1.0=completely noisy)
  3. Categorizes noise into 8 types (Excessive Verbosity, Redundant, Over-Engineering, etc.)
- **Benefit**: Separates recall (finding issues) from precision (comment quality)

### Decoupled Recall/Precision Scoring

This benchmark uses **independent recall and precision metrics** to avoid confusing coverage with quality:

#### Severity Weights
```python
Critical: 10.0  # Security vulnerabilities, data loss risks
Major:     5.0  # Performance issues, incorrect business logic
Minor:     2.0  # Code quality, minor inefficiencies
Style:     1.0  # Formatting, naming conventions
```

#### Recall: Coverage of Ground Truth

Measures **how well the agent found the known issues**:

For each ground truth requirement, the agent receives a **match score** from 0.0 to 1.0:
- **1.0**: Perfect identification with clear, actionable solution
- **0.7-0.9**: Problem mentioned but explanation could be clearer
- **0.3-0.6**: Issue hinted at but not clearly stated
- **0.0**: Completely missed

```
TP_weighted = Σ (match_score × severity_weight)
FN_weighted = Total_Possible_Score - TP_weighted

Recall = TP_weighted / (TP_weighted + FN_weighted)
```

#### Precision: Comment Quality

Measures **how clean and useful the agent's comments are**:

Each comment receives a **noise score** from 0.0 to 1.0:
- **0.0**: Perfect, actionable, on-target feedback
- **0.3-0.5**: Some unnecessary verbosity or metadata
- **0.6-0.8**: Redundant, generic, or slightly off-topic
- **1.0**: Completely irrelevant or hallucinated

```
Avg_Noise = Σ (noise_score) / total_comments

Precision = 1.0 - Avg_Noise
```

**8 Noise Categories Tracked:**
1. **Excessive Verbosity**: Overly long explanations that could be concise
2. **Redundant Comments**: Multiple comments addressing the same issue
3. **Over-Engineering**: Going too deep with unnecessary architectural suggestions
4. **Excessive Metadata**: Comments formatting details, unnecessary metadata in the comment.
5. **Unrelated/Incorrect**: Comments that are factually wrong or irrelevant to the diff
6. **Out-of-Scope Verification Requests**: Asking to verify implementation in other locations not shown in the diff and not present in the current codebase like external api or library.
7. **Hallucinated Warnings**: Vague or speculative warnings without concrete basis in the diff
8. **Generic Advice**: Non-actionable platitudes that don't address specific code

#### F1-Score
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

**Key Advantages:**
- ✅ **Decoupled metrics**: High recall + low precision reveals "found everything but too noisy"
- ✅ **Gradient scoring**: Reflects real-world nuance (not binary pass/fail)
- ✅ **Severity-weighted**: Critical issues matter more than style nitpicks
- ✅ **Noise transparency**: Detailed breakdown shows exactly what type of noise was detected

### Performance Optimization

The scoring script uses **parallel processing** to evaluate multiple PRs concurrently:

- **Worker Pool**: 35 concurrent threads (configurable via `MAX_WORKERS`)
- **Thread-Safe Aggregation**: Lock-based score accumulation
- **Progress Tracking**: Real-time completion percentage during evaluation
- **Speedup**: ~35x faster than sequential processing for large benchmark suites

To adjust parallelism, modify `MAX_WORKERS` in `score/main.py`.

### Stratified Analysis

Beyond overall scores, the benchmark provides granular analysis:

- **By Category**: Security, Performance, Business Logic, Async, etc.
- **By Difficulty**: Easy, Medium, Hard

This reveals specific strengths and weaknesses of the review agent, helping identify which types of issues your agent handles well and which need improvement.

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
======================================================
          AI Code Review Benchmark Results          
======================================================

🎯 SIMPLE SCORING SYSTEM:
   • RECALL: % of ground truth requirements matched (weighted by severity)
   • PRECISION: Average comment quality (1.0 - average noise score)

--- Overall Performance ---
  True Positives (Weighted):     342.50
  False Negatives (Missed):      87.50
  Total Agent Comments:          145
  Average Noise per Comment:     15.2%
  ---------------------------
  Recall:     79.65%  ← Coverage of ground truth
  Precision:  84.83%  ← Comment quality
  F1-Score:   0.8210

--- Noise Breakdown by Type ---
  Excessive Metadata                18 ( 40.0%)
  Excessive Verbosity               12 ( 26.7%)
  Redundant Comments                 8 ( 17.8%)
  Generic Advice                     5 ( 11.1%)
  Over-Engineering                   2 (  4.4%)

--- Performance by Category ---
Category             |  Precision |     Recall |   F1-Score |     TP | Comments | Avg Noise |     FN
-------------------- | ---------- | ---------- | ---------- | ------ | -------- | --------- | ------
Security             |      88.2% |      85.2% |     0.8668 |  68.20 |       28 |     11.8% |  11.80
Async/Concurrency    |      86.5% |      82.3% |     0.8435 |  52.20 |       22 |     13.5% |  11.20
Performance          |      85.1% |      81.7% |     0.8337 |  58.60 |       25 |     14.9% |  13.10
Business Logic       |      83.7% |      78.5% |     0.8103 |  48.30 |       21 |     16.3% |  13.20
Architecture         |      81.2% |      75.2% |     0.7809 |  45.50 |       24 |     18.8% |  15.00
Python Practices     |      79.8% |      73.8% |     0.7673 |  38.10 |       19 |     20.2% |  13.50
Testing              |      77.5% |      71.5% |     0.7441 |  31.60 |       16 |     22.5% |  12.70

--- Performance by Difficulty ---
Difficulty           |  Precision |     Recall |   F1-Score |     TP | Comments | Avg Noise |     FN
-------------------- | ---------- | ---------- | ---------- | ------ | -------- | --------- | ------
Easy                 |      91.2% |      92.3% |     0.9174 | 125.40 |       52 |      8.8% |  10.50
Medium               |      84.6% |      78.9% |     0.8168 | 134.80 |       58 |     15.4% |  39.20
Hard                 |      76.3% |      68.5% |     0.7223 |  82.30 |       35 |     23.7% |  37.80

--- Token Usage Summary ---
 Prompt Tokens = 2,458,392, Completion Tokens = 156,847

======================================================
```

**Interpretation:**
- **High Precision (84.83%)**: Agent's comments average 15.2% noise - mostly clean and useful
- **Good Recall (79.65%)**: Agent catches most issues, but misses ~20% of ground truth
- **Decoupled Metrics**: Can achieve high recall with moderate precision (found issues but verbose)
- **Noise Analysis**: 40% of noise is excessive metadata (boilerplate formatting)
- **Security Strength**: Best F1 (86.7%) with low noise (11.8%) and high recall (85.2%)
- **Difficulty Impact**: Precision drops on hard issues (91% → 76%) due to more verbose explanations

---

##  License

This project is part of a benchmark suite for evaluating AI code review agents.