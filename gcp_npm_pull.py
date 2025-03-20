from typing import Dict, Any, List, Optional, Union
import json
import os
import subprocess
import tempfile
import shutil
import base64
import tarfile
import re
from langchain_core.tools import Tool as LangChainTool

def create_gcp_npm_pull_tool() -> LangChainTool:
    """Create a tool for pulling NPM packages from Google Cloud Platform Artifact Registry."""
    
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

    def gcp_npm_pull(args_json: str) -> Dict:
        """
        Pull and extract NPM packages from GCP Artifact Registry.
        
        Args:
            args_json: JSON string with the following keys:
                - package_name: Name of the package to pull (e.g., "@observability/react-app")
                - repository_path: GCP Artifact Registry repository path (e.g., "us-central1-npm.pkg.dev/project-id/repo-name")
                - version: (Optional) Specific version to pull (default: latest)
                - output_dir: Directory to extract the package into (default: "fetched-package")
                - timeout: (Optional) Timeout in seconds (default: 300)
                
        Returns:
            Dict with pull results including package details and extraction path
        """
        try:
            # Parse the JSON arguments
            args = json.loads(args_json)
            
            # Extract arguments
            package_name = args.get("package_name")
            repository_path = args.get("repository_path")
            version = args.get("version", "latest")
            output_dir = args.get("output_dir", "fetched-package")
            timeout = args.get("timeout", 300)
            
            # Validate required arguments
            if not package_name:
                return {"error": "Package name is required"}
            if not repository_path:
                return {"error": "GCP Artifact Registry repository path is required"}
            
            # Create temporary working directory
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Setup GCP authentication
                token = setup_gcp_auth()
                if not token:
                    return {"error": "Failed to authenticate with GCP"}
                
                # Configure .npmrc
                npmrc_result = configure_npmrc(temp_dir, repository_path, token)
                if not npmrc_result["success"]:
                    return {"error": f"Failed to configure .npmrc: {npmrc_result['error']}"}
                
                # Set up environment
                env = os.environ.copy()
                env["NPM_TOKEN"] = token
                
                # Print current configuration for debugging
                print("Current configuration:")
                subprocess.run(["cat", npmrc_result["npmrc_path"]], env=env)
                
                # Get available versions
                print(f"\nFetching versions for {package_name}...")
                versions_process = subprocess.run(
                    ["npm", "view", package_name, "versions", "--registry", f"https://{repository_path}/"],
                    cwd=temp_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if versions_process.returncode != 0:
                    print(f"Versions stderr: {versions_process.stderr}")
                    return {"error": f"Failed to fetch package versions: {versions_process.stderr}"}
                
                print(f"Available versions: {versions_process.stdout}")
                
                # Pack the package
                print(f"\nPacking {package_name}@{version}...")
                package_spec = f"{package_name}@{version}" if version != "latest" else package_name
                pack_process = subprocess.run(
                    ["npm", "pack", package_spec, "--registry", f"https://{repository_path}/"],
                    cwd=temp_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if pack_process.returncode != 0:
                    print(f"Pack stderr: {pack_process.stderr}")
                    return {
                        "success": False,
                        "error": f"Failed to pack package: {pack_process.stderr}"
                    }
                
                # Find the generated tarball
                tarballs = [f for f in os.listdir(temp_dir) if f.endswith('.tgz')]
                if not tarballs:
                    return {"error": "No package tarball found after npm pack"}
                
                tarball_path = os.path.join(temp_dir, tarballs[0])
                
                # Create output directory
                os.makedirs(output_dir, exist_ok=True)
                
                # Extract the tarball
                with tarfile.open(tarball_path, 'r:gz') as tar:
                    tar.extractall(path=output_dir)
                
                # Move contents from package directory to output directory
                package_dir = os.path.join(output_dir, "package")
                if os.path.exists(package_dir):
                    for item in os.listdir(package_dir):
                        shutil.move(
                            os.path.join(package_dir, item),
                            os.path.join(output_dir, item)
                        )
                    os.rmdir(package_dir)
                
                return {
                    "success": True,
                    "package_name": package_name,
                    "version": version,
                    "output_dir": output_dir,
                    "files": os.listdir(output_dir),
                    "stdout": pack_process.stdout
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
                "error": f"Exception during GCP Artifact Registry NPM pull: {str(e)}"
            }
    
    return LangChainTool(
        name="gcp_npm_pull",
        func=gcp_npm_pull,
        description="Pull and extract NPM packages from Google Cloud Platform Artifact Registry."
    ) 