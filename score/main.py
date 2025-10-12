import os
import json
import argparse
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Ensure the project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pull_request_generator.prompter import Prompter
from score.executor import Executor
from score.reporter import Reporter

# --- Configuration ---
GROUND_TRUTH_DIR = "ground_truth_reviews"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("❌ ERROR: GITHUB_TOKEN environment variable not set.")
    sys.exit(1)

# Parallelization configuration
MAX_WORKERS = 35  # Number of parallel workers


def main(repo_name: str):
    """Main script to orchestrate the scoring process with parallelization."""
    
    # Initialize components
    executor = Executor(github_token=GITHUB_TOKEN)
    reporter = Reporter()
    
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
    
    triage_prompter = Prompter(prompt_file="score/triage.txt")
    triage_prompt_template = triage_prompter.get_prompt()
    
    evaluator_prompter = Prompter(prompt_file="score/validator.txt")
    evaluator_prompt_template = evaluator_prompter.get_prompt()
    
    scores = {
        'overall': defaultdict(float),
        'category': defaultdict(lambda: defaultdict(float)),
        'difficulty': defaultdict(lambda: defaultdict(float))
    }
    token_usage = {"input_tokens": 0, "output_tokens": 0}
    noise_breakdown = defaultdict(int)
    
    # Async progress tracking
    scores_lock = Lock()
    progress_counter = {'completed': 0}
    progress_lock = Lock()

    # Fetch and filter PRs
    pull_requests = executor.fetch_pr_list(repo_name)
    if not pull_requests:
        print("No open pull requests found. Exiting.")
        return

    prs_to_process = []
    for pr in pull_requests:
        pr_branch = pr['head']['ref']
        issue_id = next((k for k in issues_data if k in pr_branch), None)
        if issue_id:
            prs_to_process.append({'pr': pr, 'issue_id': issue_id})
    
    print(f"\n--- Starting Parallel Evaluation ({len(prs_to_process)} PRs, {MAX_WORKERS} workers) ---")
    total_prs = len(prs_to_process)
    
    # Process PRs in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as thread_executor:
        future_to_pr = {
            thread_executor.submit(
                executor.process_single_pr,
                pr_data, repo_name, issues_data, taxonomy,
                triage_prompt_template, evaluator_prompt_template,
                progress_counter, progress_lock, total_prs
            ): pr_data for pr_data in prs_to_process
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_pr):
            pr_data = future_to_pr[future]
            try:
                result = future.result()
                
                # Aggregate results with thread safety
                with scores_lock:
                    token_usage['input_tokens'] += result['token_usage']['input_tokens']
                    token_usage['output_tokens'] += result['token_usage']['output_tokens']
                    
                    if result['success'] and result['scores']:
                        s = result['scores']
                        
                        # Aggregate overall
                        for key in ['tp', 'fn', 'fp', 'total_comments', 'total_noise_score']:
                            scores['overall'][key] += s[key]
                        
                        # Aggregate by category
                        for key in ['tp', 'fn', 'fp', 'total_comments', 'total_noise_score']:
                            scores['category'][s['category']][key] += s[key]
                        
                        # Aggregate by difficulty
                        for key in ['tp', 'fn', 'fp', 'total_comments', 'total_noise_score']:
                            scores['difficulty'][s['difficulty']][key] += s[key]
                        
                        # Aggregate noise types
                        for noise_type in result['noise_types']:
                            noise_breakdown[noise_type] += 1
                        
            except Exception as e:
                print(f"     ❌ Error processing {pr_data['issue_id']}: {e}")

    # Print final report
    reporter.print_report(scores, token_usage, noise_breakdown)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Score an AI Code Review Agent's performance against the benchmark."
    )
    parser.add_argument(
        "repo_name", 
        help="The forked repository name in 'OWNER/REPO' format (e.g., 'YourUsername/your-fork-name')."
    )
    args = parser.parse_args()
    
    main(args.repo_name)