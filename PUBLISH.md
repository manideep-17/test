# Publishing to GCP Artifact Registry

This guide explains how to publish packages to the GCP Artifact Registry for the Observability project.

## Prerequisites

1. Google Cloud SDK (gcloud) installed and configured
2. Node.js and npm installed
3. Access to the GCP project: `observability-306006`
4. Access to the Artifact Registry repository: `test-npm-repo`

## Setup Instructions

1. **Configure gcloud authentication**:
   ```bash
   gcloud auth login
   gcloud config set project observability-306006
   ```

2. **Configure npm authentication**:
   ```bash
   # Get authentication token from gcloud
   gcloud auth print-access-token
   
   # Set the token as an environment variable
   export NPM_TOKEN="your-gcloud-token"
   ```

3. **Verify your .npmrc configuration**:
   The `.npmrc` file should contain:
   ```
   @observability:registry=https://us-central1-npm.pkg.dev/observability-306006/test-npm-repo/
   //us-central1-npm.pkg.dev/observability-306006/test-npm-repo/:_authToken=${NPM_TOKEN}
   ```

4. **Verify your package.json configuration**:
   ```json
   {
     "name": "@observability/react-app",
     "publishConfig": {
       "registry": "https://us-central1-npm.pkg.dev/observability-306006/test-npm-repo/"
     }
   }
   ```

## Publishing Options

1. **Using the publish script**:
   ```bash
   # Make the script executable
   chmod +x publish.sh
   
   # Run the script
   ./publish.sh
   ```

2. **Manual publishing**:
   ```bash
   # Build the package
   npm run build
   
   # Publish (with dry-run first)
   npm publish --dry-run
   
   # Publish for real
   npm publish
   ```

## Verification

1. **Verify authentication**:
   ```bash
   npm whoami --registry=https://us-central1-npm.pkg.dev/observability-306006/test-npm-repo/
   ```

2. **List published packages**:
   ```bash
   npm search @observability --registry=https://us-central1-npm.pkg.dev/observability-306006/test-npm-repo/
   ```

## Troubleshooting

1. **Authentication Issues**:
   - Ensure your GCP token is valid: `gcloud auth print-access-token`
   - Check project permissions in GCP Console
   - Verify the NPM_TOKEN environment variable is set

2. **Publishing Issues**:
   - Check the package version in package.json (must be unique)
   - Ensure all files are included in the package (check .npmignore)
   - Verify the build process completed successfully

3. **Registry Issues**:
   - Confirm the registry URL is correct
   - Check Artifact Registry permissions in GCP Console
   - Verify repository exists in the specified location

## Support

For additional support:
- GCP Console: https://console.cloud.google.com/artifacts?project=observability-306006
- Artifact Registry documentation: https://cloud.google.com/artifact-registry/docs/npm
- Contact the DevOps team for access issues

## Notes

- Always use `--dry-run` first to verify the publishing process
- Keep your authentication token secure and never commit it to version control
- Update the package version before publishing new changes
- Consider using semantic versioning for version numbers 