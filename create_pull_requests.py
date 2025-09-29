#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import re
import shutil
import time

# --- Configuration ---
# The directory where your {issue_id}.json files are stored.
DATA_DIR = "ground_truth_reviews"
# The base branch for the pull requests.
BASE_BRANCH = "main"
# A delay between creating PRs to respect API rate limits.
API_DELAY_SECONDS = 1


def run_command(command: list[str], capture_output=False, check=True):
    """A helper to run shell commands safely."""
    print(f"  > Executing: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=check,
            text=True,
            capture_output=capture_output,
            encoding='utf-8'
        )
        return result.stdout.strip() if capture_output else ""
    except subprocess.CalledProcessError as e:
        print(f"  ❌ ERROR running command: {' '.join(command)}")
        if e.stderr:
            print(f"  Stderr: {e.stderr.strip()}")
        if e.stdout:
            print(f"  Stdout: {e.stdout.strip()}")
        if check:
            raise
        return None


def check_prerequisites():
    """Ensures git and the GitHub CLI are installed and authenticated."""
    print("--- Step 0: Checking prerequisites ---")
    if not shutil.which("gh"):
        print("❌ ERROR: `gh` (GitHub CLI) command not found.")
        print("Please install it from https://cli.github.com/ and then run 'gh auth login'.")
        sys.exit(1)
    
    try:
        run_command(["gh", "auth", "status"])
        print("✅ GitHub CLI is installed and authenticated.")
    except subprocess.CalledProcessError:
        print("❌ ERROR: GitHub CLI is not authenticated.")
        print("Please run 'gh auth login' before running this script.")
        sys.exit(1)


def get_current_repo() -> str:
    """
    Gets the current repository's name in 'OWNER/REPO' format
    using the user's suggested git config method.
    """
    print("\n--- Step 1: Automatically detecting repository name ---")
    try:
        # Get the remote URL (e.g., git@github.com:adamsaimi/benchmark-01.git)
        origin_url = run_command(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True
        )
        
        # Use regex to robustly extract "OWNER/REPO" from either SSH or HTTPS URLs
        match = re.search(r'github\.com[:/]([\w.-]+/[\w.-]+?)(\.git)?$', origin_url)
        if not match:
            raise ValueError(f"Could not parse repository name from URL: {origin_url}")
            
        repo_name = match.group(1)
        print(f"✅ Detected repository: {repo_name}")
        return repo_name
    except Exception as e:
        print(f"❌ ERROR: Could not determine the repository name. {e}")
        sys.exit(1)


def create_all_pull_requests(repo_name: str):
    """Finds all data files and creates a pull request for each one."""
    print(f"\n--- Step 2: Creating Pull Requests on '{repo_name}' ---")
    if not os.path.isdir(DATA_DIR):
        print(f"❌ ERROR: Data directory '{DATA_DIR}' not found. Cannot create PRs.")
        sys.exit(1)

    json_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".json")])
    if not json_files:
        print(f"No .json files found in '{DATA_DIR}'. Nothing to do.")
        return

    total_files = len(json_files)
    print(f"Found {total_files} benchmark cases to process...")
    
    for i, filename in enumerate(json_files):
        issue_id = filename.split('.json')[0]
        branch_name = f"feat/benchmark-{issue_id}"
        
        print(f"\nProcessing PR {i+1}/{total_files}: {issue_id}")

        # Check if a PR for this branch already exists to make the script resumable
        existing_pr = run_command(
            ["gh", "pr", "list", "--repo", repo_name, "--head", branch_name, "--limit", "1"],
            capture_output=True,
            check=False 
        )
        if existing_pr:
            print(f"  ✅ PR for branch '{branch_name}' already exists. Skipping.")
            continue
            
        try:
            file_path = os.path.join(DATA_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            command = [
                "gh", "pr", "create",
                "--repo", repo_name,
                "--base", BASE_BRANCH,
                "--head", branch_name,
                "--title", data['title'],
                "--body", data['body'],
            ]

            pr_url = run_command(command, capture_output=True)
            print(f"  ✅ SUCCESS: PR created at: {pr_url}")

        except Exception as e:
            print(f"  ❌ ERROR: Failed to create PR for {issue_id}. See details above.")
        
        # Be a good citizen and wait a moment before the next API call
        time.sleep(API_DELAY_SECONDS)


def main():
    """Main function to orchestrate the entire setup process."""
    try:
        check_prerequisites()
        current_repo = get_current_repo()
        # The original prompt asked for a single script for everything.
        # Since the user confirmed the branches exist on their remote fork,
        # we can proceed directly to creating PRs.
        # If branch syncing were still needed, that step would go here.
        create_all_pull_requests(current_repo)
        
        print("\n======================================================")
        print("🎉 Benchmark PR creation process is complete!")
        print(f"You can view the newly created pull requests at: https://github.com/{current_repo}/pulls")
        print("======================================================")

    except (subprocess.CalledProcessError, KeyboardInterrupt) as e:
        print("\n❌ A critical error occurred. Aborting script.")
        if isinstance(e, KeyboardInterrupt):
            print("Script interrupted by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()