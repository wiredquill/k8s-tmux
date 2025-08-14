# Work Environment Deployment Guide

## Issue: Git URL Parse Error

You're getting this error:
```
Head failure: parse "git@github.com:wiredquill/k8s-tmux.git": first path segment in URL cannot contain colon
```

This happens when your work environment's Helm/Fleet/Rancher is configured to use SSH Git URLs instead of HTTPS.

## Solution Options

### Option 1: Direct YAML Deployment (Recommended)
Use the direct deployment file that bypasses Helm entirely:

```bash
# Create namespace if needed
kubectl create namespace ai-dev

# Deploy directly
kubectl apply -f deployments/work/direct-deploy.yaml

# Check status
kubectl get pods -n ai-dev
kubectl get svc -n ai-dev
```

### Option 2: Fix Helm Repository Configuration
If you need to use Helm, check your repository configuration:

```bash
# Check current helm repos
helm repo list

# Remove any repositories with SSH URLs
helm repo remove [repo-name]

# Add with HTTPS URL
helm repo add k8s-tmux https://wiredquill.github.io/k8s-tmux
helm repo update

# Install from repo
helm install k8s-tmux k8s-tmux/k8s-tmux -n ai-dev --create-namespace
```

### Option 3: Fix Fleet/GitOps Configuration
If using Rancher Fleet or similar GitOps tools:

1. **Check Fleet configuration:**
   ```bash
   kubectl get gitrepos -A
   kubectl describe gitrepo [your-repo] -n [namespace]
   ```

2. **Update GitRepo to use HTTPS:**
   ```yaml
   apiVersion: fleet.cattle.io/v1alpha1
   kind: GitRepo
   metadata:
     name: k8s-tmux
   spec:
     repo: https://github.com/wiredquill/k8s-tmux.git  # Use HTTPS, not SSH
     branch: main
     paths:
     - charts/k8s-tmux
   ```

### Option 4: Local Chart Installation
Install directly from local chart:

```bash
# Clone the repository
git clone https://github.com/wiredquill/k8s-tmux.git
cd k8s-tmux

# Install from local chart
helm install k8s-tmux charts/k8s-tmux -n ai-dev --create-namespace
```

## Quick Start (Recommended for Work)

1. **Use the direct deployment:**
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/wiredquill/k8s-tmux/main/deployments/work/direct-deploy.yaml
   ```

2. **Check deployment:**
   ```bash
   kubectl get pods -n ai-dev
   kubectl get svc -n ai-dev
   ```

3. **Get access URL:**
   ```bash
   kubectl get svc k8s-tmux-service -n ai-dev -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
   ```

## Troubleshooting

### If Git URL errors persist:
1. **Check your Git configuration:**
   ```bash
   git config --list | grep url
   ```

2. **Check for SSH to HTTPS rewrites:**
   ```bash
   git config --global url."https://github.com/".insteadOf "git@github.com:"
   ```

3. **Verify Helm values:**
   ```bash
   helm template k8s-tmux charts/k8s-tmux --debug
   ```

### If deployment fails:
1. **Check image pull:**
   ```bash
   kubectl describe pod [pod-name] -n ai-dev
   ```

2. **Check logs:**
   ```bash
   kubectl logs [pod-name] -n ai-dev
   ```

3. **Verify NFS mounts:**
   ```bash
   kubectl exec -it [pod-name] -n ai-dev -- ls -la /mnt/
   ```

## Environment-Specific Configuration

The work deployment is configured with:
- **Session Name**: "Work AI Terminal" 
- **Session Color**: "#4f46e5" (indigo)
- **Namespace**: ai-dev
- **Container Image**: ghcr.io/wiredquill/k8s-tmux:latest

To customize for your work environment, edit the deployment file and change:
- Environment variables (SESSION_NAME, SESSION_COLOR)
- NFS server addresses (if different)
- Resource limits/requests
- LoadBalancer configuration

## Security Notes for Work Environment

The direct deployment includes basic functionality without advanced security features. For production work environments, consider:

1. **Network Policies**: Restrict pod-to-pod communication
2. **RBAC**: Limit service account permissions
3. **Pod Security Standards**: Enforce security constraints
4. **Image Scanning**: Verify container security
5. **Resource Quotas**: Limit resource consumption

Contact your platform team for environment-specific security requirements.