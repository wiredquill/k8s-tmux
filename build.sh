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

# Build and push to local registry (if available) or build for loading
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=docker,name=k8s-tmux:latest \
    --export-cache type=inline \
    --import-cache type=registry,ref=k8s-tmux:buildcache

echo "Container built successfully using wq-prod buildkit!"
echo "To deploy: kubectl apply -f deployment.yaml"