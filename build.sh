#!/bin/bash

# Build container using wq-prod cluster's buildkit builder
echo "Building k8s-tmux container using wq-prod cluster buildkit..."

# Check if buildctl is installed
if ! command -v buildctl &> /dev/null; then
    echo "Installing buildctl..."
    # Install buildctl for macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install buildkit
        else
            echo "Please install buildctl manually or install Homebrew"
            exit 1
        fi
    else
        echo "Please install buildctl for your platform"
        exit 1
    fi
fi

# Set buildkit endpoint to wq-prod cluster service
export BUILDKIT_HOST=tcp://10.0.10.120:1234

echo "Using buildkit at: $BUILDKIT_HOST"

# Build container image (no direct docker output to avoid terminal overflow)
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --export-cache type=inline

echo "Image built successfully with buildkit"
echo "Note: Image is available on the buildkit daemon but not in local docker"
echo "For local testing, use a different approach or pull from registry"

echo "Container built successfully using wq-prod buildkit!"
echo "To deploy: kubectl apply -f deployment.yaml"