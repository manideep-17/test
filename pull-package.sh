#!/bin/bash

# Color codes for output
BLUE='\033[1;34m'
GREEN='\033[1;32m'
RED='\033[1;31m'
NC='\033[0m' # No Color

# Print colorful messages
print_message() {
    echo -e "${BLUE}>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}>> $1${NC}"
}

print_error() {
    echo -e "${RED}>> $1${NC}"
}

# Configuration
REGISTRY_URL="https://us-central1-npm.pkg.dev/observability-306006/test-npm-repo/"
PACKAGE_NAME="@observability/react-app"

# Create or update .npmrc
print_message "Setting up .npmrc configuration..."
cat > .npmrc << EOL
@observability:registry=${REGISTRY_URL}
//us-central1-npm.pkg.dev/observability-306006/test-npm-repo/:_authToken=\${NPM_TOKEN}
EOL

# Get GCP token and set NPM_TOKEN
print_message "Getting GCP authentication token..."
export NPM_TOKEN=$(gcloud auth print-access-token)

if [ $? -ne 0 ]; then
    print_error "Failed to get GCP token. Please make sure you're logged in with: gcloud auth login"
    exit 1
fi

# View available versions
print_message "Checking available versions..."
npm view ${PACKAGE_NAME} versions --registry=${REGISTRY_URL}

if [ $? -ne 0 ]; then
    print_error "Failed to fetch package versions. Please check your authentication and package name."
    exit 1
fi

# Ask user which version to install
read -p "Enter the version to install (press Enter for latest): " VERSION

# Install the package
print_message "Installing package..."
if [ -z "$VERSION" ]; then
    npm install ${PACKAGE_NAME} --registry=${REGISTRY_URL}
else
    npm install ${PACKAGE_NAME}@${VERSION} --registry=${REGISTRY_URL}
fi

if [ $? -eq 0 ]; then
    print_success "Package installed successfully!"
    print_message "You can now import the package in your code:"
    echo -e "${GREEN}import { YourComponent } from '${PACKAGE_NAME}';${NC}"
else
    print_error "Failed to install package. Please check the error messages above."
    exit 1
fi 