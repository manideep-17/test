#!/bin/bash

# build.sh - Build script for React application
# This script handles the build process for a freshly cloned React application

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

# Function to check if a command exists
command_exists() {
  command -v "$1" &> /dev/null
}

# Set error handling
set -e

# Welcome message
print_message "Starting build process for React application..."
print_message "This script will install dependencies and build the application."

# Check if Node.js and npm are installed
if ! command_exists node || ! command_exists npm; then
  print_error "Node.js and npm are required but not installed."
  print_error "Please install Node.js (https://nodejs.org/) and try again."
  exit 1
fi

# Display versions
NODE_VERSION=$(node -v)
NPM_VERSION=$(npm -v)
print_message "Using Node.js $NODE_VERSION and npm $NPM_VERSION"

# Install dependencies
print_message "Installing dependencies (this may take a few minutes)..."
npm install

# Check if installation was successful
if [ $? -ne 0 ]; then
  print_error "Failed to install dependencies. Please check the error messages above."
  exit 1
fi
print_success "Dependencies installed successfully!"

# Build the application
print_message "Building the application..."
npm run build

# Check if build was successful
if [ $? -ne 0 ]; then
  print_error "Build failed. Please check the error messages above."
  exit 1
fi

print_success "Build completed successfully!"
print_message "The built files are available in the 'dist' directory."
print_message "To preview the production build, run: npm run preview"

exit 0 