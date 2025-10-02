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
GROUND_TRUTH_DIR = "ground_truth_reviews"
# The GITHUB_TOKEN is now essential for making API calls.
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("❌ ERROR: GITHUB_TOKEN environment variable not set. Please set it to your GitHub Personal Access Token.")
    sys.exit(1)

# --- Pydantic Models ---

# UPDATED Pydantic model to match the new, high-resolution validator prompt's output.
class ValidationResponse(BaseModel):
    total_atomic_requirements: int = Field(description="The total number of distinct reviewable points in the ground truth.")
    matched_atomic_requirements: int = Field(description="The number of atomic requirements successfully identified by the agent.")
    noise_comment_count: int = Field(description="The number of agent comments that were unrelated to the ground truth.")

# --- Helper Functions ---

# check_prerequisites is no longer needed as we're using the REST API directly.
# If you still want to use `gh` for something, you can keep it.

def fetch_pr(repo_name: str) -> list:
    """Fetches all open pull requests from the specified repository."""
    print(f"\n--- Fetching Open Pull Requests for {repo_name} ---")
    all_prs = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo_name}/pulls?state=open&per_page=100&page={page}"
        response = requests.get(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
        if response.status_code == 200:
            pr_list = response.json()
            if not pr_list:
                break
            all_prs.extend(pr_list)
            page += 1
        else:
            print(f"  ❌ ERROR: Could not fetch pull requests. Status: {response.status_code}, Body: {response.text}")
            sys.exit(1)
    print(f"  Found {len(all_prs)} open pull requests.")
    return all_prs

def fetch_pr_reviews_comment(repo_name: str, pr_number: int) -> list:
    """Fetches all review comments for a given pull request."""
    print(f"  -> Fetching reviews for PR #{pr_number}...")
    response = requests.get(f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/comments",
                            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
    if response.status_code == 200:
        reviews = response.json()
        print(f"     Found {len(reviews)} review comments.")
        return [r['body'] for r in reviews] # We only need the text of the comments
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
    """Prints the final, formatted report, now handling floats."""
    print("\n\n======================================================")
    print("          AI Code Review Benchmark Results          ")
    print("======================================================")
    
    # Overall Performance
    overall = calculate_metrics(scores['overall']['tp'], scores['overall']['fp'], scores['overall']['fn'])
    print("\n--- Overall Performance ---")
    print(f"  True Positives:  {scores['overall']['tp']:.2f}") # Format as float
    print(f"  False Positives: {scores['overall']['fp']:.2f}")
    print(f"  False Negatives: {scores['overall']['fn']:.2f}")
    print(f"  ---------------------------")
    print(f"  Precision:       {overall['precision']:.2%}")
    print(f"  Recall:          {overall['recall']:.2%}")
    print(f"  F1-Score:        {overall['f1']:.4f}")

    # Performance by Category
    print("\n--- Performance by Category ---")
    print(f"{'Category':<20} | {'Precision':>10} | {'Recall':>10} | {'F1-Score':>10} | {'TP':>6} | {'FP':>6} | {'FN':>6}")
    print(f"{'-'*20} | {'-'*10} | {'-'*10} | {'-'*10} | {'-'*6} | {'-'*6} | {'-'*6}")
    for category, counts in sorted(scores['category'].items()):
        metrics = calculate_metrics(counts['tp'], counts['fp'], counts['fn'])
        print(f"{category:<20} | {metrics['precision']:>9.1%} | {metrics['recall']:>9.1%} | {metrics['f1']:>9.4f} | {counts['tp']:>6.2f} | {counts['fp']:>6.2f} | {counts['fn']:>6.2f}")

    # Performance by Difficulty
    print("\n--- Performance by Difficulty ---")
    print(f"{'Difficulty':<20} | {'Precision':>10} | {'Recall':>10} | {'F1-Score':>10} | {'TP':>6} | {'FP':>6} | {'FN':>6}")
    print(f"{'-'*20} | {'-'*10} | {'-'*10} | {'-'*10} | {'-'*6} | {'-'*6} | {'-'*6}")
    for difficulty, counts in sorted(scores['difficulty'].items()):
        metrics = calculate_metrics(counts['tp'], counts['fp'], counts['fn'])
        print(f"{difficulty:<20} | {metrics['precision']:>9.1%} | {metrics['recall']:>9.1%} | {metrics['f1']:>9.4f} | {counts['tp']:>6.2f} | {counts['fp']:>6.2f} | {counts['fn']:>6.2f}")
    print("\n======================================================")

def main(repo_name: str):
    """Main script to orchestrate the scoring process."""
    
    # --- Load all necessary data ---
    print("\n--- Loading Benchmark Data ---")
    try:
        with open("pull_request_generator/taxonomy.json", 'r', encoding='utf-8') as f:
            taxonomy = {item['issue_id']: item for item in json.load(f)}
        print(f"Loaded {len(taxonomy)} issues from taxonomy.")
        
        ground_truth_files = [f for f in os.listdir(GROUND_TRUTH_DIR) if f.endswith('.json')]
        issues_data = {}
        for filename in ground_truth_files:
            issue_id = filename.split('.')[0]
            with open(os.path.join(GROUND_TRUTH_DIR, filename), 'r', encoding='utf-8') as f:
                issues_data[issue_id] = json.load(f)
        print(f"Loaded {len(issues_data)} ground truth files.")

    except FileNotFoundError as e:
        print(f"❌ ERROR: A required data file was not found: {e}. Exiting.")
        sys.exit(1)
        
    # --- Initialize ---
    # NOTE: Your Prompter class might need to be updated to accept a model name
    validator_prompter = Prompter(prompt_file="score/validator.txt")
    validator_prompt_template = validator_prompter.get_prompt()
    
    # Use defaultdict for easy counting with floats
    scores = {
        'overall': defaultdict(float),
        'category': defaultdict(lambda: defaultdict(float)),
        'difficulty': defaultdict(lambda: defaultdict(float))
    }

    pull_requests = fetch_pr(repo_name)
    if not pull_requests:
        print("No open pull requests found. Exiting.")
        return

    # --- Main Loop: Iterate through each PR ---
    print("\n--- Starting Evaluation Loop ---")
    for pr in pull_requests:
        pr_branch = pr['head']['ref']
        pr_number = pr['number']
        
        # Find the corresponding issue_id from the branch name
        issue_id = next((k for k in issues_data if k in pr_branch), None)
        if not issue_id:
            print(f"  Skipping PR #{pr_number} ({pr_branch}) - No matching issue ID found in branch name.")
            continue

        print(f"\nProcessing {issue_id} (PR: #{pr_number})...")
        
        # --- NEW ALGORITHM IMPLEMENTATION ---
        ground_truth_comment = issues_data[issue_id]['ground_truth_reviews'][0]['comment']
        agent_comments = fetch_pr_reviews_comment(repo_name, pr_number)
        
        try:
            # Format the list of agent comments as a JSON string for the prompt
            agent_comments_json = json.dumps(agent_comments, indent=2)
            
            prompt = validator_prompt_template.format(
                ground_truth_comment=ground_truth_comment,
                agent_comments_json=agent_comments_json
            )
            
            print(f"     Validating semantics with LLM...")
            validation: ValidationResponse = validator_prompter.call_gemini_api(prompt, ValidationResponse)
            print(f"     -> LLM Verdict: Matched {validation.matched_atomic_requirements}/{validation.total_atomic_requirements} requirements with {validation.noise_comment_count} noise comments.")

            # --- Classification and Counting ---
            tp = float(validation.matched_atomic_requirements)
            fn = float(validation.total_atomic_requirements - validation.matched_atomic_requirements)
            fp = float(validation.noise_comment_count)

            category = taxonomy[issue_id]['category']
            difficulty = taxonomy[issue_id]['difficulty']

            scores['overall']['tp'] += tp
            scores['overall']['fn'] += fn
            scores['overall']['fp'] += fp
            
            scores['category'][category]['tp'] += tp
            scores['category'][category]['fn'] += fn
            scores['category'][category]['fp'] += fp
            
            scores['difficulty'][difficulty]['tp'] += tp
            scores['difficulty'][difficulty]['fn'] += fn
            scores['difficulty'][difficulty]['fp'] += fp

        except Exception as e:
            print(f"     ❌ An error occurred during processing for {issue_id}: {e}")
            # Optionally, you could add to an error count here
            continue

    # --- Final Report ---
    print_report(scores)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score an AI Code Review Agent's performance against the benchmark.")
    parser.add_argument("repo_name", help="The forked repository name in 'OWNER/REPO' format (e.g., 'YourUsername/your-fork-name').")
    args = parser.parse_args()
    
    main(args.repo_name)