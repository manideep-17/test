from typing import Dict, Any, List, Optional, Union
import json
import os
import subprocess
import tempfile
import shutil
import tarfile
from langchain_core.tools import Tool as LangChainTool

def create_gcp_npm_push_tool() -> LangChainTool:
    """Create a tool for pushing NPM packages to Google Cloud Platform Artifact Registry."""
    
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
                ["gcloud", "auth", "configure-docker", "us-central1-npm.pkg.dev"],
                capture_output=True,
                text=True
            )
            if docker_auth_process.returncode != 0:
                return None
            
            return token
        except Exception as e:
            print(f"Auth setup error: {str(e)}")
            return None

    def configure_npmrc(target_dir: str, repository_path: str, token: str) -> Dict:
        """Configure .npmrc file for GCP Artifact Registry."""
        try:
            npmrc_path = os.path.join(target_dir, ".npmrc")
            original_npmrc = None
            
            # Backup existing .npmrc if it exists
            if os.path.exists(npmrc_path):
                with open(npmrc_path, 'r') as f:
                    original_npmrc = f.read()
            
            # Create new .npmrc with GCP configuration
            with open(npmrc_path, 'w') as f:
                # Add scope-specific registry
                f.write(f"@observability:registry=https://{repository_path}/\n")
                # Add authentication for the specific registry
                f.write(f"//{repository_path}/:_authToken={token}\n")
                f.write(f"//{repository_path}/:always-auth=true\n")
                # Add authentication for npm.pkg.dev in general
                f.write("//npm.pkg.dev/:_authToken=${NPM_TOKEN}\n")
                f.write("//npm.pkg.dev/:always-auth=true\n")
                # Default registry for other packages
                f.write("registry=https://registry.npmjs.org/\n")
            
            return {
                "success": True,
                "original_npmrc": original_npmrc,
                "npmrc_path": npmrc_path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def update_package_version(package_json_path: str) -> Dict:
        """Update package.json version with timestamp."""
        try:
            import time
            
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Store old version
            old_version = package_data.get('version', '0.1.0')
            
            # Generate new version with timestamp
            timestamp = int(time.time())
            new_version = f"0.1.{timestamp}"
            
            # Update version
            package_data['version'] = new_version
            
            # Write back to package.json
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            return {
                "success": True,
                "old_version": old_version,
                "new_version": new_version
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def gcp_npm_push(args_json: str) -> Dict:
        """
        Create a compressed artifact and push it to GCP Artifact Registry.
        
        Args:
            args_json: JSON string with the following keys:
                - source_dir: Directory containing the package to push
                - repository_path: GCP Artifact Registry repository path (e.g., "us-central1-npm.pkg.dev/project-id/repo-name")
                - package_name: (Optional) Override package name in package.json
                - auto_version: (Optional) Whether to auto-generate version with timestamp (default: True)
                - timeout: (Optional) Timeout in seconds (default: 300)
                
        Returns:
            Dict with push results including package details and version
        """
        try:
            # Parse the JSON arguments
            args = json.loads(args_json)
            
            # Extract arguments
            source_dir = args.get("source_dir")
            repository_path = args.get("repository_path")
            package_name = args.get("package_name")
            auto_version = args.get("auto_version", True)
            timeout = args.get("timeout", 300)
            
            # Validate required arguments
            if not source_dir:
                return {"error": "Source directory is required"}
            if not repository_path:
                return {"error": "GCP Artifact Registry repository path is required"}
            
            # Verify package.json exists
            package_json_path = os.path.join(source_dir, "package.json")
            if not os.path.exists(package_json_path):
                return {"error": f"package.json not found in {source_dir}"}
            
            # Create temporary working directory
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Setup GCP authentication
                token = setup_gcp_auth()
                if not token:
                    return {"error": "Failed to authenticate with GCP"}
                
                # Configure .npmrc
                npmrc_result = configure_npmrc(source_dir, repository_path, token)
                if not npmrc_result["success"]:
                    return {"error": f"Failed to configure .npmrc: {npmrc_result['error']}"}
                
                # Set up environment
                env = os.environ.copy()
                env["NPM_TOKEN"] = token
                
                # Update version if auto_version is enabled
                if auto_version:
                    version_result = update_package_version(package_json_path)
                    if not version_result["success"]:
                        return {"error": f"Failed to update version: {version_result['error']}"}
                    print(f"Updated version from {version_result['old_version']} to {version_result['new_version']}")
                
                # If package name override is provided, update package.json
                if package_name:
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                    original_name = package_data.get('name')
                    package_data['name'] = package_name
                    with open(package_json_path, 'w') as f:
                        json.dump(package_data, f, indent=2)
                    print(f"Updated package name from {original_name} to {package_name}")
                
                # Run npm publish
                print("\nPublishing package...")
                publish_process = subprocess.run(
                    ["npm", "publish", "--registry", f"https://{repository_path}/"],
                    cwd=source_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if publish_process.returncode != 0:
                    print(f"Publish stderr: {publish_process.stderr}")
                    return {
                        "success": False,
                        "error": f"Failed to publish package: {publish_process.stderr}"
                    }
                
                # Get final package details
                with open(package_json_path, 'r') as f:
                    final_package = json.load(f)
                
                return {
                    "success": True,
                    "package_name": final_package.get('name'),
                    "version": final_package.get('version'),
                    "repository": repository_path,
                    "output": publish_process.stdout
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
                "error": f"Exception during GCP Artifact Registry NPM push: {str(e)}"
            }
    
    return LangChainTool(
        name="gcp_npm_push",
        func=gcp_npm_push,
        description="Push NPM packages to Google Cloud Platform Artifact Registry."
    ) 