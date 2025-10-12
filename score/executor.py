"""
Executor module for running benchmark evaluations.
"""
import json
import sys
from typing import Dict, List, Any, Literal
from threading import Lock
from pydantic import BaseModel, Field
import requests

# Ensure the project root is on sys.path
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pull_request_generator.prompter import Prompter


# --- Configuration ---
SEVERITY_WEIGHTS = {
    "Critical": 10.0,
    "Major": 5.0,
    "Minor": 2.0,
    "Style": 1.0
}


# --- Pydantic Models ---
class DecomposedRequirement(BaseModel):
    requirement_description: str = Field(description="A single, distinct, and actionable piece of feedback.")
    severity: Literal["Critical", "Major", "Minor", "Style"] = Field(description="The severity of the issue.")


class TriageResponse(BaseModel):
    requirements: List[DecomposedRequirement]


class ScoredRequirement(BaseModel):
    requirement_description: str
    severity: Literal["Critical", "Major", "Minor", "Style"]
    match_score: float = Field(description="Quality of the agent's match (0.0=missed, 1.0=perfect).")
    justification: str = Field(description="Brief reasoning for the match_score.")


class CommentNoiseScore(BaseModel):
    comment: str = Field(description="The exact comment text.")
    noise_score: float = Field(..., ge=0.0, le=1.0, description="How noisy this comment is.")
    noise_type: str | None = Field(default=None, description="Type of noise if noise_score >= 0.4")


class FinalEvaluationResponse(BaseModel):
    scored_requirements: List[ScoredRequirement]
    comment_noise_scores: List[CommentNoiseScore] = Field(description="Noise score for each comment")


class Executor:
    """Handles execution of benchmark evaluations for individual PRs."""
    
    def __init__(self, github_token: str):
        """
        Initialize executor with GitHub credentials.
        
        Args:
            github_token: GitHub personal access token
        """
        self.github_token = github_token
    
    def fetch_pr_list(self, repo_name: str) -> List[Dict[str, Any]]:
        """
        Fetch open pull requests from repository.
        
        Args:
            repo_name: Repository in format 'owner/repo'
            
        Returns:
            List of pull request objects
        """
        print(f"\n--- Fetching Open Pull Requests for {repo_name} ---")
        all_prs = []
        page = 1
        while True:
            url = f"https://api.github.com/repos/{repo_name}/pulls?state=open&per_page=100&page={page}"
            response = requests.get(url, headers={"Authorization": f"Bearer {self.github_token}"})
            if response.status_code == 200:
                pr_list = response.json()
                if not pr_list:
                    break
                all_prs.extend(pr_list)
                page += 1
            else:
                print(f"  ❌ ERROR: Could not fetch pull requests. Status: {response.status_code}")
                sys.exit(1)
        print(f"  Found {len(all_prs)} open pull requests.\n")
        return all_prs
    
    def fetch_pr_reviews(self, repo_name: str, pr_number: int) -> List[str]:
        """
        Fetch review comments for a pull request.
        
        Args:
            repo_name: Repository in format 'owner/repo'
            pr_number: Pull request number
            
        Returns:
            List of review comment bodies
        """
        response = requests.get(
            f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/comments",
            headers={"Authorization": f"Bearer {self.github_token}"}
        )
        if response.status_code == 200:
            reviews = response.json()
            return [r['body'] for r in reviews]
        else:
            print(f"  ❌ ERROR: Could not fetch reviews for PR #{pr_number}")
            return []
    
    def fetch_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """
        Fetch code diff for a pull request.
        
        Args:
            repo_name: Repository in format 'owner/repo'
            pr_number: Pull request number
            
        Returns:
            Diff content as string
        """
        url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3.diff"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return ""
    
    def process_single_pr(self, 
                         pr_data: Dict[str, Any],
                         repo_name: str,
                         issues_data: Dict[str, Any],
                         taxonomy: Dict[str, Any],
                         triage_prompt_template: str,
                         evaluator_prompt_template: str,
                         progress_counter: Dict[str, int],
                         progress_lock: Lock,
                         total_prs: int) -> Dict[str, Any]:
        """
        Process a single PR evaluation.
        
        Args:
            pr_data: Dictionary containing PR and issue_id
            repo_name: Repository name
            issues_data: Ground truth data
            taxonomy: Issue taxonomy metadata
            triage_prompt_template: Template for triage agent
            evaluator_prompt_template: Template for evaluation agent
            progress_counter: Shared progress counter
            progress_lock: Thread lock for progress updates
            total_prs: Total number of PRs to process
            
        Returns:
            Dictionary with evaluation results
        """
        pr = pr_data['pr']
        pr_number = pr['number']
        issue_id = pr_data['issue_id']
        
        result = {
            'issue_id': issue_id,
            'success': False,
            'scores': None,
            'token_usage': {'input_tokens': 0, 'output_tokens': 0},
            'noise_types': []
        }
        
        try:
            print(f"\n[Worker] Processing {issue_id} (PR #{pr_number})...")
            
            # Fetch data
            ground_truth_comment = [review['comment'] for review in issues_data[issue_id]['reviews']]
            agent_comments = self.fetch_pr_reviews(repo_name, pr_number)
            code_diff = self.fetch_pr_diff(repo_name, pr_number)
            
            # Create prompter instances
            triage_prompter = Prompter(prompt_file="score/triage.txt")
            evaluator_prompter = Prompter(prompt_file="score/validator.txt")
            
            # Agent 1: Triage Architect
            triage_prompt = triage_prompt_template.format(ground_truth_comment=ground_truth_comment)
            triage_response, input_tokens, output_tokens = triage_prompter.call_gemini_api(
                triage_prompt, TriageResponse
            )
            result['token_usage']['input_tokens'] += input_tokens
            result['token_usage']['output_tokens'] += output_tokens
            
            # Agent 2: Evaluation Analyst
            evaluator_prompt = evaluator_prompt_template.format(
                scoring_rubric_json=json.dumps([r.model_dump() for r in triage_response.requirements], indent=2),
                agent_comments_json=json.dumps(agent_comments, indent=2),
                code_diff=code_diff
            )
            evaluation, input_tokens, output_tokens = evaluator_prompter.call_gemini_api(
                evaluator_prompt, FinalEvaluationResponse
            )
            result['token_usage']['input_tokens'] += input_tokens
            result['token_usage']['output_tokens'] += output_tokens
            
            # Calculate scores
            scores = self._calculate_pr_scores(
                evaluation, 
                triage_response, 
                taxonomy[issue_id]
            )
            
            result['scores'] = scores
            result['noise_types'] = [
                item.noise_type for item in evaluation.comment_noise_scores 
                if item.noise_type
            ]
            result['success'] = True
            
        except Exception as e:
            print(f"     [{issue_id}] ❌ Error: {e}")
        
        # Update progress
        with progress_lock:
            progress_counter['completed'] += 1
            print(f"\n{'='*60}")
            print(f"📊 PROGRESS: {progress_counter['completed']}/{total_prs} PRs evaluated "
                  f"({progress_counter['completed']/total_prs*100:.1f}%)")
            print(f"{'='*60}\n")
        
        return result
    
    def _calculate_pr_scores(self, 
                            evaluation: FinalEvaluationResponse,
                            triage_response: TriageResponse,
                            taxonomy_entry: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate scores for a single PR.
        
        Args:
            evaluation: Evaluation results from LLM
            triage_response: Triage results from LLM
            taxonomy_entry: Category and difficulty metadata
            
        Returns:
            Dictionary with calculated scores
        """
        # RECALL: How well did the agent find ground truth issues?
        total_possible_score = 0
        tp_weighted = 0
        
        for scored_req in evaluation.scored_requirements:
            weight = SEVERITY_WEIGHTS.get(scored_req.severity, 1.0)
            total_possible_score += weight
            tp_weighted += (scored_req.match_score * weight)
        
        fn_weighted = total_possible_score - tp_weighted
        
        # PRECISION: Average usefulness = 1.0 - average noise
        total_comments = len(evaluation.comment_noise_scores)
        total_noise_score = sum(item.noise_score for item in evaluation.comment_noise_scores)
        
        # For backward compatibility
        fp_weighted = total_noise_score
        
        return {
            'tp': tp_weighted,
            'fn': fn_weighted,
            'fp': fp_weighted,
            'total_comments': total_comments,
            'total_noise_score': total_noise_score,
            'category': taxonomy_entry['category'],
            'difficulty': taxonomy_entry['difficulty']
        }
