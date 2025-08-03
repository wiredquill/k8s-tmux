#!/bin/bash

echo "🔍 GitHub Actions Checker"
echo "========================"
echo ""

# Check if gh CLI is available and authenticated
if command -v gh >/dev/null 2>&1; then
    echo "📡 Checking GitHub Actions status..."
    
    # Check auth
    if gh auth status >/dev/null 2>&1; then
        echo "✅ GitHub CLI authenticated"
        echo ""
        
        echo "📋 Recent workflow runs:"
        gh run list --limit 5
        echo ""
        
        echo "🔴 Recent failed runs:"
        gh run list --status failure --limit 3
        echo ""
        
        # Get the most recent run
        LATEST_RUN=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
        if [ ! -z "$LATEST_RUN" ]; then
            echo "📄 Latest run logs:"
            gh run view $LATEST_RUN --log
        fi
    else
        echo "❌ GitHub CLI not authenticated"
        echo "Run: gh auth login"
    fi
else
    echo "❌ GitHub CLI not installed"
    echo "Install with: brew install gh"
fi

echo ""
echo "🌐 Manual check options:"
echo "1. Visit: https://github.com/wiredquill/k8s-tmux/actions"
echo "2. Look for the most recent 'Build Container' or 'Release Chart' workflow"
echo "3. Click on the failed run to see detailed logs"
echo ""
echo "🔧 Debug workflow:"
echo "The debug.yaml workflow will test a minimal build to isolate issues"