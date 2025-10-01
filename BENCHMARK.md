# Benchmark

This project contains a benchmarking framework for evaluating AI-generated code reviews against ground truth reviews. It includes API endpoints, data models, validation rules, and testing instructions.

## Usage

1. **Fork project on GitHub**: Create a personal copy of the repository by forking it on GitHub. (disable copy only main branch).

2. **Clone your fork**: Clone the forked repository to your local machine using:
   ```bash
   git clone https://github.com/your-username/benchmark.git
   ```

3. **Set up a virtual environment**: Navigate to the project directory and create a virtual environment:
   ```bash
    cd benchmark
    python -m venv venv
    source venv/bin/activate
   ``` 

4. **Install dependencies**: Install the required packages using pip:
   ```bash
    pip install -r requirements.txt
    ```

5. **Create the pull requests**: Create pull requests with AI-generated code reviews and ground truth reviews.
   ```bash
   python create_pull_requests.py
   ```

6. **Review your pull requests**: This steps is up to you. It will depend on how you setup your automatic agentic reviews. 

Some people, use reviewers, some people use labels.

7. **Run the benchmark**: Execute the benchmark script to evaluate the AI-generated reviews against the ground truth reviews:
   ```bash
    python score.py {repo_name} 

    # Example
    python score.py your-username/benchmark
   ```

> You need to have a gemini api key setup in your environment variables as `API_KEY` to run the benchmark and a github token as `GITHUB_TOKEN` to create the pull requests and fetch them.

## Methodology

A taxonomy of common issues in code reviews was developed based on an analysis of real-world code reviews. The benchmark evaluates AI-generated reviews based on their ability to identify and address these issues.

From the taxonomy, we created pull requests with ground truth reviews and buggy code snippets.


## Scoring Algorithm

The scoring algorithm compares AI-generated reviews to ground truth reviews based on the following criteria:
- **Precision**: The proportion of relevant issues identified by the AI-generated review.
- **Recall**: The proportion of issues in the ground truth review that were identified by the AI-generated review.
- **F1 Score**: The harmonic mean of precision and recall, providing a single metric for evaluation.

More details on the scoring algorithm can be found in the `SCORE.md` file.