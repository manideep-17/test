#!/bin/bash

# publish.sh - Script to publish the package to GCP Artifact Registry
# This script handles authentication and publishing to GCP Artifact Registry

# Print colorful messages
print_message() {
  echo -e "\033[1;34m>> $1\033[0m"
}

print_success() {
  echo -e "\033[1;32m>> $1\033[0m"
}

print_error() {
  echo -e "\033[1;31m>> $1\033[0m"
}

# Set error handling
set -e

# Welcome message
print_message "Starting package publishing process for @observability/react-app..."

# Check if NPM_TOKEN is set
if [ -z "$NPM_TOKEN" ]; then
  print_error "NPM_TOKEN environment variable is not set."
  print_error "Please set it with: export NPM_TOKEN=your_token"
  print_error "For GCP Artifact Registry, you can get this token from gcloud CLI."
  exit 1
fi

# Check if .npmrc exists
if [ ! -f ".npmrc" ]; then
  print_error ".npmrc file not found. Please create it first."
  exit 1
fi

# Check if package.json is properly configured
NAME=$(node -e "console.log(require('./package.json').name)")
VERSION=$(node -e "console.log(require('./package.json').version)")
REGISTRY=$(node -e "console.log(require('./package.json').publishConfig?.registry)")

if [[ "$NAME" != @*/* ]]; then
  print_error "Package name in package.json should include a scope (e.g., @observability/react-app)."
  exit 1
fi

if [ -z "$REGISTRY" ]; then
  print_error "publishConfig.registry is not set in package.json."
  exit 1
fi

print_message "Publishing $NAME@$VERSION to $REGISTRY"

# Build the package first
print_message "Building the package..."
npm run build

# Check if build was successful
if [ $? -ne 0 ]; then
  print_error "Build failed. Please check the error messages above."
  exit 1
fi

# Publish the package
print_message "Publishing the package..."
npm publish

# Check if publish was successful
if [ $? -ne 0 ]; then
  print_error "Publishing failed. Please check the error messages above."
  exit 1
fi

print_success "Package publishing process completed successfully!"
print_message "Package $NAME@$VERSION has been published to $REGISTRY"

exit 0 