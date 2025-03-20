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
OUTPUT_DIR="fetched-package"

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

# Ask user which version to fetch
read -p "Enter the version to fetch (press Enter for latest): " VERSION

# Create temporary directory for package
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Fetch the package
print_message "Fetching package..."
if [ -z "$VERSION" ]; then
    npm pack ${PACKAGE_NAME} --registry=${REGISTRY_URL}
else
    npm pack ${PACKAGE_NAME}@${VERSION} --registry=${REGISTRY_URL}
fi

if [ $? -ne 0 ]; then
    print_error "Failed to fetch package. Please check the error messages above."
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Get the tarball name
TARBALL=$(ls *.tgz)

if [ -z "$TARBALL" ]; then
    print_error "No package tarball found."
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Create output directory
cd - > /dev/null
mkdir -p "$OUTPUT_DIR"

# Extract the package
print_message "Extracting package to $OUTPUT_DIR..."
tar -xzf "$TEMP_DIR/$TARBALL" -C "$OUTPUT_DIR" --strip-components=1

if [ $? -eq 0 ]; then
    print_success "Package fetched and extracted successfully to $OUTPUT_DIR/"
    print_message "You can now modify the package contents and create a new artifact."
    print_message "Package contents:"
    ls -la "$OUTPUT_DIR"
else
    print_error "Failed to extract package."
fi

# Cleanup
rm -rf "$TEMP_DIR" 