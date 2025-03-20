from typing import Dict, Any, List, Optional, Union
import json
import os
import subprocess
import tempfile
import shutil
import tarfile
import datetime
from langchain_core.tools import Tool as LangChainTool

def create_gcp_artifact_push_tool() -> LangChainTool:
    """Create a tool for pushing compressed artifacts to Google Cloud Platform Artifact Registry."""
    
    def setup_gcp_auth() -> Optional[str]:
        """Setup GCP authentication and return the token."""
        try:
            # Get GCP token first
            token_process = subprocess.run(
                ["gcloud", "auth", "print-access-token"],
                capture_output=True,
                text=True
            )
            if token_process.returncode != 0:
                return None
            
            token = token_process.stdout.strip()
            
            # Configure docker auth for Artifact Registry
            docker_auth_process = subprocess.run(
                ["gcloud", "auth", "configure-docker", "us-central1-docker.pkg.dev"],
                capture_output=True,
                text=True
            )
            if docker_auth_process.returncode != 0:
                return None
            
            return token
        except Exception as e:
            print(f"Auth setup error: {str(e)}")
            return None

    def create_compressed_artifact(source_dir: str, output_dir: str, artifact_name: str) -> Dict:
        """Create a compressed tar.gz artifact from source directory."""
        try:
            # Generate timestamp for versioning
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create artifact filename with timestamp
            artifact_filename = f"{artifact_name}_{timestamp}.tar.gz"
            artifact_path = os.path.join(output_dir, artifact_filename)
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Create tar.gz archive
            with tarfile.open(artifact_path, "w:gz") as tar:
                tar.add(source_dir, arcname=os.path.basename(source_dir))
            
            return {
                "success": True,
                "artifact_path": artifact_path,
                "artifact_name": artifact_filename,
                "timestamp": timestamp
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def push_to_artifact_registry(artifact_path: str, repository_path: str, artifact_name: str, token: str) -> Dict:
        """Push the compressed artifact to GCP Artifact Registry."""
        try:
            # Parse repository path components
            # Expected format: us-central1-docker.pkg.dev/project-id/repository-name
            parts = repository_path.split('/')
            if len(parts) < 3:
                return {
                    "success": False,
                    "error": "Invalid repository path format. Expected: region-docker.pkg.dev/project-id/repository-name"
                }
            
            project_id = parts[1]
            repository_name = parts[2]
            
            # Generate version based on current timestamp
            version = datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
            
            # Use gcloud command to upload the artifact using generic repository
            push_process = subprocess.run([
                "gcloud", "artifacts", "generic", "upload",
                "--location=us-central1",
                f"--repository={repository_name}",
                f"--project={project_id}",
                f"--package={artifact_name}",
                f"--version={version}",
                "--source=" + artifact_path
            ], capture_output=True, text=True)
            
            if push_process.returncode != 0:
                print(f"Command failed with error: {push_process.stderr}")
                return {
                    "success": False,
                    "error": f"Failed to push artifact: {push_process.stderr}"
                }
            
            return {
                "success": True,
                "repository_url": f"https://{repository_path}",
                "artifact_path": artifact_path,
                "package": artifact_name,
                "version": version,
                "output": push_process.stdout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def gcp_artifact_push(args_json: str) -> Dict:
        """
        Create a compressed artifact and push it to GCP Artifact Registry.
        
        Args:
            args_json: JSON string with the following keys:
                - source_dir: Directory containing the files to compress
                - repository_path: GCP Artifact Registry repository path
                - artifact_name: Name for the artifact (will be appended with timestamp)
                - output_dir: (Optional) Directory to store compressed artifact (default: "artifacts")
                - timeout: (Optional) Timeout in seconds (default: 300)
                
        Returns:
            Dict with push results including artifact details and location
        """
        try:
            # Parse the JSON arguments
            args = json.loads(args_json)
            
            # Extract arguments
            source_dir = args.get("source_dir")
            repository_path = args.get("repository_path")
            artifact_name = args.get("artifact_name")
            output_dir = args.get("output_dir", "artifacts")
            timeout = args.get("timeout", 300)
            
            # Validate required arguments
            if not source_dir:
                return {"error": "Source directory is required"}
            if not repository_path:
                return {"error": "GCP Artifact Registry repository path is required"}
            if not artifact_name:
                return {"error": "Artifact name is required"}
            
            # Create temporary working directory
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Setup GCP authentication
                token = setup_gcp_auth()
                if not token:
                    return {"error": "Failed to authenticate with GCP"}
                
                # Create compressed artifact
                print(f"\nCreating compressed artifact from {source_dir}...")
                compress_result = create_compressed_artifact(source_dir, output_dir, artifact_name)
                if not compress_result["success"]:
                    return {"error": f"Failed to create compressed artifact: {compress_result['error']}"}
                
                print(f"Created artifact: {compress_result['artifact_path']}")
                
                # Push to Artifact Registry
                print(f"\nPushing artifact to GCP Artifact Registry...")
                push_result = push_to_artifact_registry(
                    compress_result["artifact_path"],
                    repository_path,
                    compress_result["artifact_name"],
                    token
                )
                
                if not push_result["success"]:
                    return {"error": f"Failed to push artifact: {push_result['error']}"}
                
                return {
                    "success": True,
                    "artifact_name": compress_result["artifact_name"],
                    "artifact_path": compress_result["artifact_path"],
                    "repository": repository_path,
                    "timestamp": compress_result["timestamp"],
                    "package": push_result["package"],
                    "version": push_result["version"],
                    "output": push_result["output"]
                }
                
            finally:
                # Cleanup
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception during GCP Artifact Registry push: {str(e)}"
            }
    
    return LangChainTool(
        name="gcp_artifact_push",
        func=gcp_artifact_push,
        description="Push compressed artifacts to Google Cloud Platform Artifact Registry."
    ) 