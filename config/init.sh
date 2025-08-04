#!/bin/bash

# Initialize development environment
echo "Initializing AI development environment..."

# Install tmux plugin manager if not exists
if [ ! -d ~/.tmux/plugins/tpm ]; then
    git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi

# Check for kubeconfig in multiple locations
mkdir -p ~/.kube

# Priority order: shared storage, WiredQuill, then any config files in k8s-tmux
if [ -f /mnt/k8s-tmux/.kube/config ]; then
    cp /mnt/k8s-tmux/.kube/config ~/.kube/config
    echo "Kubeconfig loaded from k8s-tmux shared storage"
elif [ -f /mnt/WiredQuill/.kube/config ]; then
    cp /mnt/WiredQuill/.kube/config ~/.kube/config
    echo "Kubeconfig loaded from WiredQuill shared storage"
elif [ -f /mnt/k8s-tmux/config ]; then
    cp /mnt/k8s-tmux/config ~/.kube/config
    echo "Kubeconfig loaded from k8s-tmux root"
elif [ -f /mnt/WiredQuill/config ]; then
    cp /mnt/WiredQuill/config ~/.kube/config
    echo "Kubeconfig loaded from WiredQuill root"
else
    echo "No kubeconfig found. You can:"
    echo "  1. Copy your kubeconfig to /mnt/k8s-tmux/.kube/config"
    echo "  2. Copy your kubeconfig to /mnt/WiredQuill/.kube/config"
    echo "  3. Run: kubectl config set-cluster/set-credentials/set-context commands"
fi

# Set proper permissions
if [ -f ~/.kube/config ]; then
    chmod 600 ~/.kube/config
    echo "Kubeconfig permissions set to 600"
fi

# Show welcome message with system info
echo "===================="
echo "k8s-tmux Environment"
echo "===================="
echo "Available tools:"
echo "  - kubectl (k), kubectx (kx), kubens (kn)"
echo "  - helm, k9s, mc, btop, fastfetch"
echo "  - vim, nano, git, tree"
echo ""
if command -v fastfetch >/dev/null 2>&1; then
    fastfetch --config none --structure Title:Separator:OS:Kernel:Uptime:Memory:Separator
fi

# Create default tmux session if not exists
tmux has-session -t ai-dev 2>/dev/null || {
    tmux new-session -d -s ai-dev -c /mnt/k8s-tmux
    tmux new-window -t ai-dev -n "claude" -c /mnt/k8s-tmux
    tmux new-window -t ai-dev -n "files" -c /mnt/WiredQuill
    tmux select-window -t ai-dev:0
}

# Start ttyd with tmux session
exec ttyd -p 7681 -W /mnt/k8s-tmux tmux attach -t ai-dev