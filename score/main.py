import os
import json
import argparse
import sys
from typing import List, Literal
from collections import defaultdict
import requests
from pydantic import BaseModel, Field

# Ensure the project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pull_request_generator.prompter import Prompter

# --- Configuration ---
GROUND_TRUTH_DIR = "ground_truth_reviews"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("❌ ERROR: GITHUB_TOKEN environment variable not set.")
    sys.exit(1)

SEVERITY_WEIGHTS = {
    "Critical": 10.0,
    "Major": 5.0,
    "Minor": 2.0,
    "Style": 1.0
}
DISCOVERY_BONUS_WEIGHT = 0.5 # Bonus points for each valid discovery

# --- Pydantic Models ---
class DecomposedRequirement(BaseModel):
    requirement_description: str = Field(description="A single, distinct, and actionable piece of feedback.")
    severity: Literal["Critical", "Major", "Minor", "Style"] = Field(description="The severity of the issue.")

class TriageResponse(BaseModel):
    requirements: List[DecomposedRequirement]

class ScoredRequirement(BaseModel):
    requirement_description: str
    severity: Literal["Critical", "Major", "Minor", "Style"]
    match_score: float = Field(..., ge=0.0, le=1.0, description="Quality of the agent's match (0.0=missed, 0.5=vague, 1.0=perfect).")
    justification: str = Field(description="Brief reasoning for the match_score.")

class ValidDiscovery(BaseModel):
    comment: str = Field(description="The agent's comment that was a valid new finding.")
    justification: str = Field(description="Why this is a relevant and correct suggestion for the code diff.")

class FinalEvaluationResponse(BaseModel):
    scored_requirements: List[ScoredRequirement]
    valid_discoveries: List[ValidDiscovery]
    noise_comment_count: int

# --- Helper Functions ---

def fetch_pr(repo_name: str) -> list:
    # ... (no changes needed)
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
    # ... (no changes needed)
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

# NEW: Function to fetch the code diff
def fetch_pr_diff(repo_name: str, pr_number: int) -> str:
    """Fetches the code diff for a given pull request."""
    print(f"  -> Fetching diff for PR #{pr_number}...")
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"  ❌ WARNING: Could not fetch diff for PR #{pr_number}. Error: {response.text}")
        return ""

def calculate_metrics(tp, fp, fn):
    # ... (no changes needed)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return {"precision": precision, "recall": recall, "f1": f1}


def print_report(scores: dict, token_usage: dict = None):
    # ... (no changes needed, it already handles floats)
    print("\n\n======================================================")
    print("          AI Code Review Benchmark Results          ")
    print("======================================================")
    
    # Overall Performance
    overall = calculate_metrics(scores['overall']['tp'], scores['overall']['fp'], scores['overall']['fn'])
    print("\n--- Overall Performance ---")
    print(f"  True Positives (Weighted):  {scores['overall']['tp']:.2f}") # Format as float
    print(f"  False Positives (Noise):    {scores['overall']['fp']:.2f}")
    print(f"  Unexpected Good Reviews (Weighted): {scores['overall']['fn']:.2f}")
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
    
    # Token Usage Summary (if provided)
    if token_usage:
        print("\n--- Token Usage Summary ---")
        print(f" Prompt Tokens = {token_usage['input_tokens']}, Completion Tokens = {token_usage['output_tokens']}")
    
    print("\n======================================================")

        

def main(repo_name: str):
    """Main script to orchestrate the scoring process."""
    
    print("\n--- Loading Benchmark Data ---")
    try:
        with open("taxonomy.json", 'r', encoding='utf-8') as f:
            taxonomy = {item['issue_id']: item for item in json.load(f)}
        ground_truth_files = [f for f in os.listdir(GROUND_TRUTH_DIR) if f.endswith('.json')]
        issues_data = {}
        for filename in ground_truth_files:
            issue_id = filename.split('.')[0]
            with open(os.path.join(GROUND_TRUTH_DIR, filename), 'r', encoding='utf-8') as f:
                issues_data[issue_id] = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ ERROR: A required data file was not found: {e}. Exiting.")
        sys.exit(1)
        
    token_usage = {"input_tokens": 0, "output_tokens": 0}
        
    # --- Initialize TWO Prompters for our two agents ---
    triage_prompter = Prompter(prompt_file="score/triage.txt")
    triage_prompt_template = triage_prompter.get_prompt()
    
    evaluator_prompter = Prompter(prompt_file="score/validator.txt")
    evaluator_prompt_template = evaluator_prompter.get_prompt()
    
    scores = {
        'overall': defaultdict(float),
        'category': defaultdict(lambda: defaultdict(float)),
        'difficulty': defaultdict(lambda: defaultdict(float))
    }

    pull_requests = fetch_pr(repo_name)
    if not pull_requests:
        print("No open pull requests found. Exiting.")
        return

    print("\n--- Starting Evaluation Loop ---")
    for pr in pull_requests:
        pr_branch = pr['head']['ref']
        pr_number = pr['number']
        
        issue_id = next((k for k in issues_data if k in pr_branch), None)
        if not issue_id:
            continue

        print(f"\nProcessing {issue_id} (PR: #{pr_number})...")

        ground_truth_comment = [review['comment'] for review in issues_data[issue_id]['reviews']]
        agent_comments = fetch_pr_reviews_comment(repo_name, pr_number)
        code_diff = fetch_pr_diff(repo_name, pr_number)
        
        try:
            # --- AGENT 1: Triage Architect ---
            print("     [Agent 1] Decomposing ground truth and assigning severity...")
            triage_prompt = triage_prompt_template.format(ground_truth_comment=ground_truth_comment)
            triage_response, input_tokens, output_tokens = triage_prompter.call_gemini_api(triage_prompt, TriageResponse)
            print(f"     -> Triage complete: Found {len(triage_response.requirements)} atomic requirements.")

            token_usage['input_tokens'] += input_tokens
            token_usage['output_tokens'] += output_tokens

            # --- AGENT 2: Evaluation Analyst ---
            print("     [Agent 2] Matching comments, scoring quality, and analyzing discoveries...")
            evaluator_prompt = evaluator_prompt_template.format(
                scoring_rubric_json=json.dumps([r.model_dump() for r in triage_response.requirements], indent=2),
                agent_comments_json=json.dumps(agent_comments, indent=2),
                code_diff=code_diff
            )
            evaluation, input_tokens, output_tokens = evaluator_prompter.call_gemini_api(evaluator_prompt, FinalEvaluationResponse)
            print(f"     -> Evaluation complete.")
            token_usage['input_tokens'] += input_tokens
            token_usage['output_tokens'] += output_tokens

            # --- NEW WEIGHTED SCORING ALGORITHM ---
            total_possible_score = 0
            tp_weighted = 0
            
            # 1. Calculate weighted scores from rubric
            for scored_req in evaluation.scored_requirements:
                weight = SEVERITY_WEIGHTS.get(scored_req.severity, 1.0)
                total_possible_score += weight
                tp_weighted += (scored_req.match_score * weight)

            # 2. Add bonus points for valid discoveries
            discovery_bonus = len(evaluation.valid_discoveries) * DISCOVERY_BONUS_WEIGHT
            tp_weighted += discovery_bonus

            # 3. Calculate final TP, FN, FP
            fn_weighted = total_possible_score - (tp_weighted - discovery_bonus) # Don't let bonus reduce FN
            fp = float(evaluation.noise_comment_count)

            # --- Aggregate scores ---
            category = taxonomy[issue_id]['category']
            difficulty = taxonomy[issue_id]['difficulty']

            scores['overall']['tp'] += tp_weighted
            scores['overall']['fn'] += fn_weighted
            scores['overall']['fp'] += fp
            
            scores['category'][category]['tp'] += tp_weighted
            scores['category'][category]['fn'] += fn_weighted
            scores['category'][category]['fp'] += fp
            
            scores['difficulty'][difficulty]['tp'] += tp_weighted
            scores['difficulty'][difficulty]['fn'] += fn_weighted
            scores['difficulty'][difficulty]['fp'] += fp

        except Exception as e:
            print(f"     ❌ An error occurred during processing for {issue_id}: {e}")
            continue

    print_report(scores, token_usage)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score an AI Code Review Agent's performance against the benchmark.")
    parser.add_argument("repo_name", help="The forked repository name in 'OWNER/REPO' format (e.g., 'YourUsername/your-fork-name').")
    args = parser.parse_args()
    
    main(args.repo_name)