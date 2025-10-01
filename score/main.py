import os
import json
import subprocess
import argparse
import sys
import shutil
from typing import List, Literal
from collections import defaultdict
import requests
from pydantic import BaseModel, Field

# Assuming your Prompter class is in a file named prompter.py
import os
import sys

# Ensure the project root is on sys.path so this file can be run as a script
# (prevents "attempted relative import with no known parent package" errors).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pull_request_generator.prompter import Prompter

# --- Configuration ---
LINE_TOLERANCE = 10  # How many lines apart can a comment be to be considered a location match
GROUND_TRUTH_DIR = "ground_truth_reviews"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
# --- Pydantic Models ---

class ValidationResponse(BaseModel):
    verdict: Literal["MATCH", "PARTIAL", "MISMATCH"] = Field(description="The verdict of the comparison.")

# --- Helper Functions ---

def check_prerequisites():
    """Ensures the GitHub CLI is installed and authenticated."""
    if not shutil.which("gh"):
        print("❌ ERROR: `gh` (GitHub CLI) command not found.")
        sys.exit(1)
    try:
        subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
        print("✅ GitHub CLI is installed and authenticated.")
    except subprocess.CalledProcessError:
        print("❌ ERROR: GitHub CLI is not authenticated. Please run 'gh auth login'.")
        sys.exit(1)

def fetch_pr(repo_name: str):
    """Fetches the list of open pull requests from the specified repository."""
    print(f"\n--- Fetching Open Pull Requests for {repo_name} ---")
    response = requests.get(f"https://api.github.com/repos/{repo_name}/pulls?per_page=100",
                            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
    if response.status_code == 200:
        pr_list = response.json()
        print(f"  Found {len(pr_list)} open pull requests.")
        return [pr for pr in pr_list if pr['title'] == 'feat: Add tests for large numbers']
    else:
        print(f"  ❌ ERROR: Could not fetch pull requests. Error: {response.text}")
        sys.exit(1)

def fetch_pr_reviews_comment(repo_name: str, pr_number: int) -> list:
    """Fetches all review comments for a given pull request."""
    print(f"  -> Fetching reviews for PR #{pr_number}...")
    response = requests.get(f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/comments",
                            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
    if response.status_code == 200:
        reviews = response.json()
        print(f"Found {len(reviews)} reviews.")
        return reviews
    else:
        print(f"  ❌ ERROR: Could not fetch reviews for PR #{pr_number}. Error: {response.text}")
        return []

def calculate_metrics(tp, fp, fn):
    """Calculates Precision, Recall, and F1-Score, handling division by zero."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return {"precision": precision, "recall": recall, "f1": f1}

def print_report(scores: dict):
    """Prints the final, formatted report."""
    print("\n\n======================================================")
    print("          AI Code Review Benchmark Results          ")
    print("======================================================")
    
    # Overall Performance
    overall = calculate_metrics(scores['overall']['tp'], scores['overall']['fp'], scores['overall']['fn'])
    print("\n--- Overall Performance ---")
    print(f"  True Positives:  {scores['overall']['tp']}")
    print(f"  False Positives: {scores['overall']['fp']}")
    print(f"  False Negatives: {scores['overall']['fn']}")
    print(f"  ---------------------------")
    print(f"  Precision:       {overall['precision']:.2%}")
    print(f"  Recall:          {overall['recall']:.2%}")
    print(f"  F1-Score:        {overall['f1']:.4f}")

    # Performance by Category
    print("\n--- Performance by Category ---")
    print(f"{'Category':<15} | {'Precision':>10} | {'Recall':>10} | {'F1-Score':>10} | {'TP':>4} | {'FP':>4} | {'FN':>4}")
    print(f"{'-'*15} | {'-'*10} | {'-'*10} | {'-'*10} | {'-'*4} | {'-'*4} | {'-'*4}")
    for category, counts in sorted(scores['category'].items()):
        metrics = calculate_metrics(counts['tp'], counts['fp'], counts['fn'])
        print(f"{category:<15} | {metrics['precision']:>9.1%} | {metrics['recall']:>9.1%} | {metrics['f1']:>9.4f} | {counts['tp']:>4} | {counts['fp']:>4} | {counts['fn']:>4}")

    # Performance by Difficulty
    print("\n--- Performance by Difficulty ---")
    print(f"{'Difficulty':<15} | {'Precision':>10} | {'Recall':>10} | {'F1-Score':>10} | {'TP':>4} | {'FP':>4} | {'FN':>4}")
    print(f"{'-'*15} | {'-'*10} | {'-'*10} | {'-'*10} | {'-'*4} | {'-'*4} | {'-'*4}")
    for difficulty, counts in sorted(scores['difficulty'].items()):
        metrics = calculate_metrics(counts['tp'], counts['fp'], counts['fn'])
        print(f"{difficulty:<15} | {metrics['precision']:>9.1%} | {metrics['recall']:>9.1%} | {metrics['f1']:>9.4f} | {counts['tp']:>4} | {counts['fp']:>4} | {counts['fn']:>4}")
    print("\n======================================================")


def main(repo_name: str):
    """Main script to orchestrate the scoring process."""
    check_prerequisites()
    
    with open("pull_request_generator/taxonomy.json", 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)
    # --- Load all necessary data ---
    print("\n--- Loading Benchmark Data ---")
    # load ground_truth_reviews directory to get list of issue_ids
    issue_ids = [f.split('.')[0] for f in os.listdir(GROUND_TRUTH_DIR) if f.endswith('.json')]
    issues = {}
    for issue_id in issue_ids:
        print(f"  Found ground truth for issue: {issue_id}")
        with open(os.path.join(GROUND_TRUTH_DIR, f"{issue_id}.json"), 'r', encoding='utf-8') as f:
            issues[issue_id] = json.load(f)
        
        # --- Initialize ---
    validator_prompter = Prompter(prompt_file="score/validator.txt", model="gemini-2.5-flash")
    validator_prompt_template = validator_prompter.get_prompt()
    
    # Use defaultdict for easy counting
    scores = {
        'overall': defaultdict(int),
        'category': defaultdict(lambda: defaultdict(int)),
        'difficulty': defaultdict(lambda: defaultdict(int))
    }

    pull_requests = fetch_pr(repo_name)
    if not pull_requests:
        print("No open pull requests found. Exiting.")
        return

    # --- Main Loop: Iterate through each PR ---
    print("\n--- Starting Evaluation Loop ---")
    for pull_request in pull_requests:
        pr_branch = pull_request['head']['ref']

        issue = issues[next(k for k in issues if k in pr_branch)]

        # --- Matching Algorithm ---
        reviews = fetch_pr_reviews_comment(repo_name, pull_request['number'])
        
        total_true_positive = 0

        for _, agent_review in enumerate(reviews):
            prompt = validator_prompt_template.format(
                ground_truth_comment=issue['ground_truth_reviews'][0]['comment'],
                agent_comment=agent_review.get('body')
            )
            try:
                validation = validator_prompter.call_gemini_api(prompt, ValidationResponse)
                if validation.verdict in ["MATCH", "PARTIAL"]:
                    print(f"     -> SEMANTIC MATCH ({validation.verdict})")
                    total_true_positive += 1
                    break
                else:
                    print("     -> Semantic Mismatch")
            except Exception as e:
                print(f"     -> LLM Validation failed: {e}")

        # --- Classification and Counting ---
        tp = total_true_positive
        fn = len(issue['ground_truth_reviews']) - tp
        fp = len(reviews) - total_true_positive
        taxonomy_issue = next(i for i in taxonomy if i["issue_id"] == issue["issue_id"])
        category = taxonomy_issue['category']
        difficulty = taxonomy_issue['difficulty']

        scores['overall']['tp'] += tp
        scores['overall']['fn'] += fn
        scores['overall']['fp'] += fp
        
        scores['category'][category]['tp'] += tp
        scores['category'][category]['fn'] += fn
        scores['category'][category]['fp'] += fp
        
        scores['difficulty'][difficulty]['tp'] += tp
        scores['difficulty'][difficulty]['fn'] += fn
        scores['difficulty'][difficulty]['fp'] += fp

    # --- Final Report ---
    print_report(scores)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score an AI Code Review Agent's performance against the benchmark.")
    parser.add_argument("repo_name", help="The forked repository name in 'OWNER/REPO' format (e.g., 'YourUsername/your-fork-name').")
    args = parser.parse_args()
    
    # It's past 2 AM on a Monday here in Colombes. Time to get some results.
    main(args.repo_name)