#!/bin/bash

# Claude Container Build Trigger Script
# Usage: ./claude-build.sh ["description of changes"]

set -e

DESCRIPTION="${1:-Container updated via Claude session}"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

echo "🤖 Claude Build Trigger"
echo "Description: $DESCRIPTION"
echo "Timestamp: $TIMESTAMP"
echo ""

# Option 1: Trigger GitHub Action via API
if command -v gh >/dev/null 2>&1; then
    echo "📡 Triggering GitHub Action via gh CLI..."
    gh workflow run claude-trigger.yaml \
        -f trigger_source="claude-session" \
        -f container_changes="$DESCRIPTION"
    echo "✅ GitHub Action triggered successfully"
else
    echo "❌ gh CLI not found. Install with: brew install gh"
fi

echo ""

# Option 2: Direct build with local buildctl (if available)
if command -v buildctl >/dev/null 2>&1; then
    echo "🔨 Building directly with buildctl..."
    export BUILDKIT_HOST=tcp://10.0.10.120:1234
    
    IMAGE_TAG="ghcr.io/wiredquill/k8s-tmux:claude-$TIMESTAMP"
    
    buildctl build \
        --frontend dockerfile.v0 \
        --local context=. \
        --local dockerfile=. \
        --output type=image,name=$IMAGE_TAG,push=true \
        --export-cache type=inline
    
    echo "✅ Container built and pushed: $IMAGE_TAG"
else
    echo "ℹ️  buildctl not available for direct build"
fi

echo ""

# Option 3: Auto-commit trigger (commits changes to trigger workflow)
read -p "🔄 Auto-commit changes to trigger build workflow? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add -A
    git commit -m "feat: $DESCRIPTION

Triggered by Claude session at $TIMESTAMP

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    git push origin main
    echo "✅ Changes committed and pushed - build workflow triggered"
fi

echo ""
echo "🎉 Claude build trigger complete!"