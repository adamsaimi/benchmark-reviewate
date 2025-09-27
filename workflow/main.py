import os
import json
import subprocess
from typing import List, Optional

from pydantic import BaseModel, Field

from prompter import Prompter 

# --- 1. Pydantic Models for a Typed Gemini API Response ---
# These models define the exact JSON structure we expect from the LLM.
# This is crucial for the `response_schema` feature in your Prompter class.

class GroundTruthReview(BaseModel):
    line_number: int = Field(description="The approximate line number of the introduced flaw.")
    comment: str = Field(description="The detailed, senior-engineer-style code review comment.")

class GeneratedCodeResponse(BaseModel):
    buggy_code: str = Field(description="The complete, rewritten source code with the bug introduced.")
    ground_truth_reviews: List[GroundTruthReview] = Field(description="A list containing the ground truth review comments.")
    title: Optional[str] = Field(default=None, description="A plausible Merge Request title.")
    body: Optional[str] = Field(default=None, description="A plausible Merge Request body.")

# --- 2. Helper Functions for Git and File Operations ---

def run_command(command: list[str]):
    """Runs a command and raises an exception if it fails."""
    print(f"Executing: {' '.join(command)}")
    subprocess.run(command, check=True, text=True)

def create_and_checkout_branch(branch_name: str):
    """Resets to main and creates a new branch."""
    print("\n--- Resetting to clean state and creating new branch ---")
    run_command(["git", "fetch", "origin"])
    run_command(["git", "reset", "--hard", "origin/main"])
    run_command(["git", "checkout", "-b", branch_name])

def reset_to_main(branch_name: str):
    """Resets the current branch to match origin/main."""
    print("\n--- Resetting to main branch ---")
    run_command(["git", "branch", "-D", branch_name])
    run_command(["git", "reset", "--hard"])
    run_command(["git", "checkout", "main"])

def commit_and_push(branch_name: str, commit_message: str):
    """Commits all changes and pushes the branch."""
    print("\n--- Committing and pushing changes ---")
    run_command(["git", "add", "."])
    run_command(["git", "commit", "-m", commit_message])
    run_command(["git", "push", "-u", "origin", branch_name])

def create_merge_request(title: str, body: str):
    """Creates a merge request using the GitHub CLI."""
    print("\n--- Creating Merge Request ---")
    # This requires the GitHub CLI (`gh`) to be installed and authenticated.
    # The command might differ slightly for GitLab (`glab`).
    try:
        run_command(["gh", "pr", "create", "--title", title, "--body", body])
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("****************************************************************")
        print("WARNING: Failed to create Merge Request automatically.")
        print("Please ensure the GitHub CLI ('gh') is installed and configured.")
        print("You may need to create the MR manually for this branch.")
        print(f"Error: {e}")
        print("****************************************************************")

# --- 3. Main Workflow Logic ---

def format_prompt(bug_details: dict, biz_prompter: Prompter, standard_prompter: Prompter) -> tuple[str, Prompter, str]:
    target_file = bug_details["file_target"]
    with open(target_file, 'r', encoding='utf-8') as f:
        clean_code = f.read()

    if bug_details['issue_id'].startswith("BIZ-"):
        prompter_to_use = biz_prompter
        prompt_template = prompter_to_use.get_prompt()
        prompt = prompt_template.format(
            requirement=bug_details['requirement'],
            taxonomy_entry_json=json.dumps(bug_details, indent=2),
            target_filename=target_file,
            clean_code=clean_code
        )
    else:
        prompter_to_use = standard_prompter
        prompt_template = prompter_to_use.get_prompt()
        prompt = prompt_template.format(
            taxonomy_entry_json=json.dumps(bug_details, indent=2),
            target_filename=target_file,
            clean_code=clean_code
        )
        
    return prompt, prompter_to_use, target_file

def main():
    """
    Main workflow to generate benchmark merge requests.
    """
    print("Starting benchmark generation workflow...")
    
    # Initialize prompters for both types of bugs
    standard_prompter = Prompter(prompt_file="workflow/code_generator.txt")
    biz_prompter = Prompter(prompt_file="workflow/biz_code_generator.txt")

    # STEP 1: Read the taxonomy file
    taxonomy = standard_prompter.get_taxonomy()
    
    all_generated_outputs = []

    # STEP 2: For each issue in the taxonomy...
    for i, bug_details in enumerate(taxonomy):
        if i > 0:
            break  # TEMPORARY: Process only the first issue for testing
        
        # State tracking: skip if already generated
        if bug_details.get("generated", False):
            print(f"\nSkipping [{bug_details['issue_id']}] - Already generated.")
            continue

        branch_name = f"feat/benchmark-{bug_details['issue_id']}"
        print(f"\n========================================================")
        print(f"Processing Issue {i+1}/{len(taxonomy)}: {bug_details['issue_id']} - {bug_details['issue_name']}")
        print(f"========================================================")
        
        try:
            # WORKFLOW STEP 2.1: Create branch and checkout
            create_and_checkout_branch(branch_name)

            # WORKFLOW STEP 2.2: Call Gemini using the prompter and the prompt
            print("\n--- Preparing prompt and calling Gemini API ---")

            prompt, prompter_to_use, target_file = format_prompt(bug_details, biz_prompter, standard_prompter)
            print(f"Using prompt from: {prompter_to_use.prompt_file}")
            print(f"Target file to modify: {target_file}")
            
            # The magic happens here!
            generated_data: GeneratedCodeResponse = prompter_to_use.call_gemini_api(
                prompt, 
                GeneratedCodeResponse
            )
            print("Successfully received and parsed response from Gemini.")

            # Apply the generated change to the file
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(generated_data.buggy_code)
            
            # WORKFLOW STEP 3: Commit to branch and create merge request
            commit_message = f"feat(benchmark): Introduce {bug_details['issue_id']} - {bug_details['issue_name']}"
            commit_and_push(branch_name, commit_message)

            mr_title = generated_data.title
            mr_body = generated_data.body
            create_merge_request(mr_title, mr_body)            
        except Exception as e:
            print(f"\n---!!! AN ERROR OCCURRED for {bug_details['issue_id']} !!!---")
            print(str(e))
            bug_details["generated"] = False
            bug_details["error"] = str(e)
            # Reset to main to ensure the next loop starts clean
            reset_to_main(branch_name)
        
        finally:
            # Update the state in our local taxonomy object
            run_command(["git", "checkout", "main"])
            bug_details["generated"] = True
            
            # WORKFLOW STEP 4: Save the Gemini output (ground truth)
            
            output = generated_data.model_dump(exclude={"buggy_code"})  # Exclude code for brevity
            output["issue_id"] = bug_details["issue_id"]
            
            # Create a directory for ground truth reviews if it doesn't exist
            os.makedirs("ground_truth_reviews", exist_ok=True)
            ground_truth_path = f"ground_truth_reviews/{output['issue_id']}.json"
            with open(ground_truth_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2)
            print(f"Ground truth saved to {ground_truth_path}")
            
            # Add the full output to our summary list
            all_generated_outputs.append(output) 

            with open("workflow/taxonomy.json", 'w', encoding='utf-8') as f:
                json.dump(taxonomy, f, indent=2)

            
    # WORKFLOW STEP 5: Save all Gemini outputs into a single summary file
    with open("all_generated_outputs.json", 'w', encoding='utf-8') as f:
        json.dump(all_generated_outputs, f, indent=2)
        
    print("\n========================================================")
    print("Workflow finished!")
    print("========================================================")

if __name__ == "__main__":
    main()
