#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create stats directory if it doesn't exist
mkdir -p stats

# Generate timestamp for the stats file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
STATS_FILE="stats/build_stats_${TIMESTAMP}.json"

print_status "Starting build with stats generation..."

# Run Vite build with stats enabled
VITE_BUILD_STATS=true npm run build 2>&1 | tee build_output.log

if [ $? -eq 0 ]; then
    print_success "Build completed successfully"
    
    # Move stats file if it exists
    if [ -f "stats.html" ]; then
        mv stats.html "${STATS_FILE%.*}.html"
        print_success "Stats file generated: ${STATS_FILE%.*}.html"
    fi
    
    # Generate additional build information
    {
        echo "{"
        echo "  \"buildTimestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\","
        echo "  \"nodeVersion\": \"$(node -v)\","
        echo "  \"npmVersion\": \"$(npm -v)\","
        echo "  \"buildOutput\": \"$(cat build_output.log | tr '\n' ' ' | sed 's/"/\\"/g')\""
        echo "}" 
    } > "$STATS_FILE"
    
    print_success "Build stats JSON generated: $STATS_FILE"
    
    # Generate bundle size information
    if [ -d "dist" ]; then
        print_status "Generating bundle size information..."
        echo "Bundle sizes:" > "stats/bundle_sizes_${TIMESTAMP}.txt"
        find dist -type f -exec ls -lh {} \; | awk '{print $5, $9}' >> "stats/bundle_sizes_${TIMESTAMP}.txt"
        print_success "Bundle size information generated: stats/bundle_sizes_${TIMESTAMP}.txt"
    fi
    
    # Clean up
    rm -f build_output.log
    
    print_success "All stats generation completed!"
    echo -e "\nStats files generated:"
    echo "- ${STATS_FILE%.*}.html (Detailed build visualization)"
    echo "- $STATS_FILE (Build metadata and output)"
    echo "- stats/bundle_sizes_${TIMESTAMP}.txt (Bundle size information)"
else
    print_error "Build failed! Check build_output.log for details"
    exit 1
fi 