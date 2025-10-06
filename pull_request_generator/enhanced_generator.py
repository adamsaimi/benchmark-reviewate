import os
import json
import subprocess
from typing import List, Dict, Any
from pathlib import Path

from pydantic import BaseModel, Field
from jinja2 import Template

from prompter import Prompter

# --- 0. Configuration ---
# These four files will always be included in the prompt to provide core context to the LLM.
CORE_CONTEXT_FILES = [
    "benchmark/config.py",
    "benchmark/models.py",
    "benchmark/routers/posts.py",
    "benchmark/services/post_service.py"
]

# --- 1. Pydantic Models for Enhanced Generator Response ---

class ModifiedFile(BaseModel):
    filename: str = Field(description="The path to the modified file.")
    content: str = Field(description="The complete, rewritten source code for this file.")

class GroundTruthReview(BaseModel):
    file: str = Field(description="The file path where the flaw exists.")
    line_number: int = Field(description="The approximate line number of the introduced flaw.")
    comment: str = Field(description="The detailed, senior-engineer-style code review comment.")

class EnhancedCodeResponse(BaseModel):
    modified_files: List[ModifiedFile] = Field(description="Array of all modified files with their complete content.")
    ground_truth_reviews: List[GroundTruthReview] = Field(description="Array of code review comments for the flaws.")

# --- 2. Helper Functions for Git and File Operations ---

def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Runs a command and optionally raises an exception if it fails."""
    print(f"Executing: {' '.join(command)}")
    return subprocess.run(command, check=check, text=True, capture_output=True)

def create_and_checkout_branch(branch_name: str):
    """Resets to main and creates a new branch."""
    print("\n--- Resetting to clean state and creating new branch ---")
    run_command(["git", "fetch", "origin"])
    run_command(["git", "reset", "--hard", "origin/main"])
    # Delete branch if it exists
    run_command(["git", "branch", "-D", branch_name], check=False)
    run_command(["git", "checkout", "-b", branch_name])

def reset_to_main(branch_name: str):
    """Resets the current branch to match origin/main."""
    print("\n--- Resetting to main branch ---")
    run_command(["git", "checkout", "main"])
    run_command(["git", "branch", "-D", branch_name], check=False)
    run_command(["git", "reset", "--hard", "origin/main"])

def commit_and_push(branch_name: str, commit_message: str):
    """Commits all changes and pushes the branch."""
    print("\n--- Committing and pushing changes ---")
    run_command(["git", "add", "."])
    run_command(["git", "commit", "-m", commit_message])
    run_command(["git", "push", "-f", "-u", "origin", branch_name])

def create_merge_request(issue_id: str, pr_info: dict):
    """Creates a merge request using the GitHub CLI."""
    print("\n--- Creating Pull Request ---")
    title = pr_info.get("title", f"feat: {issue_id}")
    body = pr_info.get("body", f"Implements {issue_id}")

    try:
        run_command(["gh", "pr", "create", "--title", title, "--body", body, "--base", "main"])
        print(f"✅ Pull request created: {title}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("****************************************************************")
        print("WARNING: Failed to create Pull Request automatically.")
        print("Please ensure the GitHub CLI ('gh') is installed and configured.")
        print("You may need to create the PR manually for this branch.")
        print(f"Error: {e}")
        print("****************************************************************")

# --- 3. Load Project Files ---

def load_project_files() -> Dict[str, str]:
    """
    Loads all necessary Python files from the project.
    Returns a dict mapping relative file paths to their content.
    """
    project_files = {}
    
    # Define all files to load
    files_to_load = [
        "benchmark/__init__.py",
        "benchmark/config.py",
        "benchmark/database.py",
        "benchmark/main.py",
        "benchmark/models.py",
        "benchmark/schemas.py",
        "benchmark/routers/__init__.py",
        "benchmark/routers/posts.py",
        "benchmark/services/__init__.py",
        "benchmark/services/post_service.py",
    ]
    
    for file_path_str in files_to_load:
        full_path = Path(file_path_str)
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                project_files[file_path_str] = content
                print(f"✓ Loaded: {file_path_str}")
            except Exception as e:
                print(f"✗ Failed to load {file_path_str}: {e}")
        else:
            print(f"⚠ File not found: {file_path_str}")
    
    return project_files

def apply_modified_files(modified_files: List[ModifiedFile]):
    """
    Writes the modified files back to the filesystem.
    """
    for modified_file in modified_files:
        file_path = Path(modified_file.filename)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_file.content)
        
        print(f"✓ Applied changes to: {modified_file.filename}")

# --- 4. Main Workflow Logic ---

def load_prompt_template(prompt_file: str) -> Template:
    """
    Loads the prompt template from a file and returns a Jinja2 Template object.
    """
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    return Template(prompt_content)

def format_enhanced_prompt(taxonomy_entry: dict, context_files: Dict[str, str], template: Template) -> str:
    """
    Formats the enhanced prompt with taxonomy entry and curated context files using Jinja2.
    """
    return template.render(
        taxonomy_entry=taxonomy_entry,
        project_files=context_files
    )

def main():
    """
    Main workflow to generate benchmark merge requests using enhanced prompt.
    """
    print("=" * 80)
    print("Starting Enhanced Benchmark Generation Workflow")
    print("=" * 80)
    
    # Initialize prompter
    prompt_file = "pull_request_generator/enhanced_code_generator.txt"
    prompter = Prompter(
        prompt_file=prompt_file,
        model="gemini-2.5-flash"
    )

    # STEP 1: Load the prompt template
    print("\n--- Loading Prompt Template ---")
    prompt_template = load_prompt_template(prompt_file)
    print(f"✓ Loaded prompt template from {prompt_file}")

    # STEP 2: Read the taxonomy file
    print("\n--- Loading Taxonomy ---")
    taxonomy = prompter.get_taxonomy()
    print(f"Loaded {len(taxonomy)} issues from taxonomy")
    
    # STEP 3: Load all project files once into memory
    print("\n--- Loading All Project Files ---")
    all_project_files = load_project_files()
    print(f"Loaded {len(all_project_files)} project files")

    # STEP 4: For each issue in the taxonomy...
    for i, taxonomy_entry in enumerate(taxonomy):
        if i > 0:
            break  # TEMPORARY: Process only the first issue for testing
        
        # Skip if already generated
        if taxonomy_entry.get("generated", False):
            print(f"\n⏭  Skipping [{taxonomy_entry['issue_id']}] - Already generated.")
            continue

        issue_id = taxonomy_entry['issue_id']
        branch_name = f"feat/benchmark-{issue_id}"
        
        print("\n" + "=" * 80)
        print(f"Processing Issue {i+1}/{len(taxonomy)}: {issue_id} - {taxonomy_entry['issue_name']}")
        print("=" * 80)
        
        try:
            # STEP 4.1: Create branch and checkout
            create_and_checkout_branch(branch_name)

            # STEP 4.2: Prepare curated context and format prompt
            print("\n--- Preparing curated prompt context ---")
            prompt_context_files = {}
            # Add core context files first
            for core_file in CORE_CONTEXT_FILES:
                if core_file in all_project_files:
                    prompt_context_files[core_file] = all_project_files[core_file]
            print(f"Added {len(prompt_context_files)} core files to context.")

            # Add the specific target file for the issue (if not already included)
            target_file = taxonomy_entry.get("file_target")
            if target_file and target_file not in prompt_context_files and target_file in all_project_files:
                 prompt_context_files[target_file] = all_project_files[target_file]
                 print(f"Added target file to context: {target_file}")

            prompt = format_enhanced_prompt(taxonomy_entry, prompt_context_files, prompt_template)
            with open(f"{issue_id}_enhanced_prompt.txt", 'w', encoding='utf-8') as f:
                f.write(prompt)
            print(f"Prompt size: ~{len(prompt)} characters")
            print("Calling Gemini API...")
            
            # Call Gemini with the enhanced prompt
            generated_data: EnhancedCodeResponse = prompter.call_gemini_api(
                prompt, 
                EnhancedCodeResponse
            )
            
            print(f"✅ Received response:")
            print(f"   - Modified files: {len(generated_data.modified_files)}")
            print(f"   - Reviews: {len(generated_data.ground_truth_reviews)}")

            # STEP 4.3: Apply the generated changes to files
            print("\n--- Applying changes to files ---")
            apply_modified_files(generated_data.modified_files)

            # STEP 4.4: Commit and push
            pr_info = taxonomy_entry.get("generation_strategy", {}).get("pr_info", {})
            commit_message = pr_info.get("title", f"feat(benchmark): Introduce {issue_id}")
            
            commit_and_push(branch_name, commit_message)
            create_merge_request(issue_id, pr_info)
            
            # STEP 4.5: Save ground truth reviews
            print("\n--- Saving ground truth ---")
            os.makedirs("ground_truth_reviews", exist_ok=True)
            ground_truth_path = f"ground_truth_reviews/{issue_id}.json"
            
            ground_truth_data = {
                "issue_id": issue_id,
                "issue_name": taxonomy_entry["issue_name"],
                "category": taxonomy_entry["category"],
                "reviews": [review.model_dump() for review in generated_data.ground_truth_reviews],
                "title": taxonomy_entry.get("generation_strategy", {}).get("pr_info", {}).get("title", ""),
                "body": taxonomy_entry.get("generation_strategy", {}).get("pr_info", {}).get("body", ""),
            }
            
            with open(ground_truth_path, 'w', encoding='utf-8') as f:
                json.dump(ground_truth_data, f, indent=2)
            print(f"✅ Ground truth saved to {ground_truth_path}")
            
            # Mark as generated
            taxonomy_entry["generated"] = True
            
        except Exception as e:
            print(f"\n❌ ERROR for {issue_id}:")
            print(f"   {type(e).__name__}: {str(e)}")
            taxonomy_entry["generated"] = False
            taxonomy_entry["error"] = str(e)
            
            # Reset to main to ensure clean state
            reset_to_main(branch_name)
        
        finally:
            # Always return to main branch
            run_command(["git", "checkout", "main"])
            
            # Save updated taxonomy with generation status
            with open("taxonomy.json", 'w', encoding='utf-8') as f:
                json.dump(taxonomy, f, indent=2)
            print(f"Updated taxonomy with generation status")

    print("\n" + "=" * 80)
    print("Enhanced Workflow Finished!")
    print("=" * 80)

if __name__ == "__main__":
    main()
