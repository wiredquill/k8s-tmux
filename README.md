# K8s-TMux Terminal

A Kubernetes-deployed web-based terminal application for long-running tmux sessions, specifically designed for AI model interactions like Claude. Features persistent sessions, remote notifications, file transfer, and a customizable web UI.

## ✨ Features

- 🎯 **Persistent TMux Sessions** - Shared sessions that survive browser disconnections
- 📡 **Remote Mode** - Push notifications via ntfy.sh for AI interactions
- 🌈 **Customizable UI** - Configurable colors, titles, and themes
- 📁 **File Transfer** - Drag-and-drop upload/download functionality
- 🔧 **Pre-installed Tools** - kubectl, helm, k9s, btop, gh, kubectx, and more
- 🎨 **Web Terminal** - Browser-based access with full color support
- 💾 **NFS Storage** - Persistent data storage across pod restarts
- ⚙️ **Configuration UI** - Easy setup of NTFY servers and topics

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster with LoadBalancer support
- NFS server accessible at `10.0.0.10` with paths:
  - `/volume1/k8s/k8s-tmux` 
  - `/volume1/WiredQuill`

### Deploy Production Terminal

```bash
kubectl apply -f deployments/prod/enhanced-terminal.yaml
```

Access the terminal at the assigned LoadBalancer IP on port 80.

## 📋 Repository Structure

```
k8s-tmux/
├── deployments/
│   ├── prod/           # Production-ready deployments
│   │   ├── enhanced-terminal.yaml    # Full-featured terminal with UI
│   │   └── production-terminal.yaml  # Production terminal with secrets
│   └── dev/            # Development and test deployments
├── scripts/            # Build and utility scripts
│   ├── build.sh       # Container build script (uses wq-prod buildkit)
│   ├── claude-build.sh # Claude-specific build script
│   └── check-actions.sh # GitHub Actions checker
├── config/             # Configuration files
│   ├── automation-config.js  # Terminal automation
│   ├── remote-mode-script.sh # Remote mode functionality
│   ├── tmux.conf      # TMux configuration
│   └── init.sh        # Container initialization
├── charts/             # Helm charts
│   └── k8s-tmux/      # Main Helm chart
└── docs/              # Documentation
```

## 🛠️ Configuration

### Remote Mode Setup

1. Click the **⚙️ Config** button in the terminal UI
2. Configure your NTFY server and topic:
   - **Server**: `https://ntfy.wiredquill.com` (or your server)
   - **Topic**: `ai_communication` (or custom topic)
3. Click **Save Configuration**
4. Use **📡 Remote** button to toggle remote mode

### Session Customization

- **Title**: Set a custom session title for identification
- **Colors**: Choose from 7 color themes (Green, Red, Blue, Yellow, Purple, Cyan, Orange)
- **Border**: Colored border wraps the entire application for easy session identification

### File Management

- **Upload**: Drag files to the terminal or use the **📤 Upload** button
- **Download**: Use **📥 Download** button and enter filename
- Files are stored in `/mnt/k8s-tmux/` within the container

## 🔧 Advanced Usage

### Building Custom Images

```bash
# Uses wq-prod cluster buildkit service
./scripts/build.sh
```

### Secrets Management

For GitHub CLI and Claude Code authentication:

```bash
# GitHub token
kubectl create secret generic github-secrets \
  --from-literal=github-token=YOUR_TOKEN -n k8s-tmux

# Claude API key  
kubectl create secret generic claude-secrets \
  --from-literal=claude-api-key=YOUR_KEY -n k8s-tmux
```

### Helm Deployment

```bash
helm install k8s-tmux ./charts/k8s-tmux \
  --namespace k8s-tmux \
  --create-namespace
```

## 🔍 Troubleshooting

### Pod Not Starting
```bash
kubectl get pods -n k8s-tmux
kubectl logs -n k8s-tmux <pod-name>
```

### Storage Issues
Ensure NFS server is accessible and paths exist:
```bash
showmount -e 10.0.0.10
```

### Remote Mode Not Working
Check NTFY configuration in the Config panel and verify server accessibility.

## 🛡️ Security Features

- **Secrets Integration** - Kubernetes secrets for API keys
- **Network Policies** - Optional network isolation
- **RBAC Support** - Role-based access control ready
- **Non-root Options** - Configurable user execution

## 📝 Development

### Testing Locally
```bash
# Quick development deployment
kubectl apply -f deployments/dev/simple-working-terminal.yaml
```

### Contributing
1. Create feature branch
2. Test with development deployments
3. Update documentation
4. Submit pull request

## 🎯 Use Cases

- **AI Development** - Long-running sessions for Claude/ChatGPT interactions
- **Kubernetes Management** - Pre-configured kubectl, helm, k9s access
- **Remote Collaboration** - Shared tmux sessions with notifications
- **DevOps Workflows** - Persistent development environment
- **Multi-Environment Management** - Color-coded session identification

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/wiredquill/k8s-tmux/issues)
- **Notifications**: Configure ntfy.sh for real-time updates
- **Remote Mode**: Enable for AI interaction notifications

---

**Built for AI-enhanced development workflows** 🤖✨

