from typing import Dict, Any
import json
import os
import subprocess
from langchain_core.tools import Tool as LangChainTool

def create_gcp_npm_publish_tool() -> LangChainTool:
    """Create a tool for publishing NPM packages to Google Cloud Platform Artifact Registry."""
    
    def gcp_npm_publish(args_json: str) -> Dict:
        """
        Package and publish an NPM package to GCP Artifact Registry using publish.sh.
        
        Args:
            args_json: JSON string with the following keys:
                - project_dir: Directory containing the npm package to publish
                - dry_run: (Optional) If true, adds --dry-run flag to npm publish (default: False)
                
        Returns:
            Dict with publish results including package details and version
        """
        try:
            # Parse the JSON arguments
            args = json.loads(args_json)
            
            # Extract required arguments
            project_dir = args.get("project_dir")
            dry_run = args.get("dry_run", False)
            
            # Validate required arguments
            if not project_dir:
                return {"error": "Project directory is required"}
            if not os.path.exists(project_dir):
                return {"error": f"Project directory does not exist: {project_dir}"}
            
            # Verify publish.sh exists
            publish_script = os.path.join(project_dir, "publish.sh")
            if not os.path.exists(publish_script):
                return {"error": f"publish.sh not found in {project_dir}"}
            
            # Make sure publish.sh is executable
            try:
                os.chmod(publish_script, 0o755)
            except Exception as e:
                return {"error": f"Failed to make publish.sh executable: {str(e)}"}
            
            # Get GCP token and set NPM_TOKEN
            try:
                token_process = subprocess.run(
                    ["gcloud", "auth", "print-access-token"],
                    capture_output=True,
                    text=True
                )
                if token_process.returncode != 0:
                    return {"error": "Failed to get GCP access token"}
                
                # Set up environment with the token
                env = os.environ.copy()
                env["NPM_TOKEN"] = token_process.stdout.strip()
                
                # If dry run is requested, modify the publish.sh content temporarily
                if dry_run:
                    # Read the current content
                    with open(publish_script, 'r') as f:
                        content = f.read()
                    
                    # Add --dry-run to npm publish command
                    modified_content = content.replace('npm publish', 'npm publish --dry-run')
                    
                    # Write modified content
                    with open(publish_script, 'w') as f:
                        f.write(modified_content)
                
                # Execute publish.sh
                publish_process = subprocess.run(
                    ["./publish.sh"],
                    cwd=project_dir,
                    env=env,
                    capture_output=True,
                    text=True
                )
                
                # If we modified publish.sh for dry run, restore it
                if dry_run:
                    with open(publish_script, 'w') as f:
                        f.write(content)
                
                if publish_process.returncode == 0:
                    return {
                        "success": True,
                        "output": publish_process.stdout,
                        "dry_run": dry_run
                    }
                else:
                    return {
                        "success": False,
                        "error": "Publishing failed",
                        "stdout": publish_process.stdout,
                        "stderr": publish_process.stderr,
                        "dry_run": dry_run
                    }
                
            except subprocess.CalledProcessError as e:
                return {
                    "success": False,
                    "error": f"Command failed: {str(e)}",
                    "stderr": e.stderr if hasattr(e, 'stderr') else None
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Exception during publish: {str(e)}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception during GCP Artifact Registry NPM publish: {str(e)}"
            }
    
    return LangChainTool(
        name="gcp_npm_publish",
        func=gcp_npm_publish,
        description="Publish NPM packages to Google Cloud Platform Artifact Registry using publish.sh script."
    ) 