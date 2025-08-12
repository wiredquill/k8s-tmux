#!/bin/bash

# Kubeconfig Helper Script for k8s-tmux terminal
# Usage: source this script in the terminal for kubeconfig management

function set-kubeconfig() {
    if [ -z "$1" ]; then
        echo "Usage: set-kubeconfig <path-to-kubeconfig>"
        echo "   or: set-kubeconfig - (to enter YAML directly)"
        return 1
    fi
    
    if [ "$1" = "-" ]; then
        echo "Paste your kubeconfig YAML (press Ctrl+D when finished):"
        cat > /tmp/kubeconfig.yaml
        export KUBECONFIG="/tmp/kubeconfig.yaml"
        echo "✅ Kubeconfig set from stdin"
    elif [ -f "$1" ]; then
        export KUBECONFIG="$1"
        echo "✅ Kubeconfig set to: $1"
    else
        echo "❌ File not found: $1"
        return 1
    fi
    
    # Verify the kubeconfig works
    if kubectl cluster-info &>/dev/null; then
        echo "🎯 Connected to cluster: $(kubectl config current-context)"
        kubectl get nodes 2>/dev/null | head -5
    else
        echo "⚠️  Kubeconfig set but unable to connect to cluster"
    fi
}

function clear-kubeconfig() {
    unset KUBECONFIG
    rm -f /tmp/kubeconfig.yaml
    echo "✅ Kubeconfig cleared"
}

function show-kubeconfig() {
    if [ -z "$KUBECONFIG" ]; then
        echo "No kubeconfig currently set"
        echo "Use: set-kubeconfig <path> or set-kubeconfig - to set one"
    else
        echo "Current kubeconfig: $KUBECONFIG"
        echo "Current context: $(kubectl config current-context 2>/dev/null || echo 'unknown')"
        echo ""
        echo "Available contexts:"
        kubectl config get-contexts 2>/dev/null || echo "Unable to read contexts"
    fi
}

# Add aliases for convenience
alias kconf='show-kubeconfig'
alias kcset='set-kubeconfig'
alias kcclear='clear-kubeconfig'

echo "🔧 Kubeconfig helper loaded!"
echo "Commands:"
echo "  kconf        - Show current kubeconfig status"  
echo "  kcset <file> - Set kubeconfig from file"
echo "  kcset -      - Set kubeconfig from stdin (paste YAML)"
echo "  kcclear      - Clear kubeconfig"
echo ""