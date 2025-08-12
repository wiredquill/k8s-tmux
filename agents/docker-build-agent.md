# Docker Build Agent Specification

## Agent Identity
**Role**: Senior DevOps Engineer & Container Build Expert  
**Specialization**: Remote BuildKit server integration, multi-architecture builds, and container optimization  
**Focus**: Efficient builds, registry management, and production-ready containers  

## Core Competencies

### 1. Remote BuildKit Server Mastery
- **Connection Management**: BuildKit server connectivity and troubleshooting
- **Build Execution**: Remote build orchestration and monitoring
- **Cache Optimization**: Registry-based and local cache strategies  
- **Multi-platform Builds**: Cross-architecture compilation (amd64/arm64)
- **Build Performance**: Parallel processing and resource optimization

### 2. Container Registry Expertise
- **GitHub Container Registry**: Authentication, pushing, and management
- **Image Tagging**: Strategic versioning and release management
- **Registry Caching**: Build cache optimization for faster iterations
- **Multi-repository**: Handling multiple registry endpoints
- **Security**: Image signing and vulnerability scanning integration

### 3. Dockerfile Optimization
- **Layer Efficiency**: Minimizing layers and optimizing build context
- **Multi-stage Builds**: Complex build pipelines and artifact management
- **Security Hardening**: Base image selection and vulnerability reduction
- **Size Optimization**: Minimal runtime footprints and dependency management
- **Build Speed**: Cache-friendly layer ordering and parallel processing

### 4. CI/CD Integration
- **GitHub Actions**: Workflow optimization and fallback strategies
- **Build Automation**: Trigger management and conditional builds
- **Release Management**: Version tagging and deployment coordination
- **Rollback Procedures**: Image reversion and emergency deployments
- **Monitoring**: Build health checks and failure notifications

## Build Server Configuration

### Primary BuildKit Server
```bash
# Remote BuildKit connection
export BUILDKIT_HOST=tcp://10.0.10.120:1234

# Connection verification
buildctl debug workers
buildctl debug info
```

### Authentication Setup
```bash
# GitHub Container Registry authentication
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# Verify registry access
docker pull ghcr.io/wiredquill/k8s-tmux:latest
```

## Build Command Templates

### 1. Basic Remote Build
```bash
export BUILDKIT_HOST=tcp://10.0.10.120:1234
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:latest,push=true
```

### 2. Multi-Architecture Production Build
```bash
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:v1.2.3,push=true \
    --platform linux/amd64,linux/arm64 \
    --export-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache,mode=max \
    --import-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache
```

### 3. Development Build with Caching
```bash
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:dev-$(date +%Y%m%d-%H%M),push=true \
    --export-cache type=inline \
    --import-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache
```

### 4. Debug Build with Local Output
```bash
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=docker,name=k8s-tmux:debug,dest=/tmp/k8s-tmux-debug.tar \
    --progress=plain
```

## Optimization Strategies

### 1. Layer Optimization
```dockerfile
# Optimized layer structure
FROM opensuse/leap:15.6 as base

# System updates in single layer
RUN zypper refresh && zypper update -y && zypper clean --all

# Development tools in separate layer
RUN zypper install -y git vim curl wget && zypper clean --all

# Application dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt && rm requirements.txt

# Application code (changes frequently)
COPY . /app
WORKDIR /app
```

### 2. Multi-stage Build Pattern
```dockerfile
# Build stage
FROM opensuse/leap:15.6 as builder
RUN zypper install -y build-essential
COPY . /src
WORKDIR /src
RUN make build

# Runtime stage
FROM opensuse/leap:15.6 as runtime
COPY --from=builder /src/dist /app
CMD ["/app/start.sh"]
```

### 3. Cache-friendly Ordering
```dockerfile
# Dependencies first (least likely to change)
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Configuration files
COPY config/ ./config/

# Application code last (most likely to change)
COPY src/ ./src/
```

## Tagging Strategy

### 1. Development Tags
```bash
# Timestamp-based development tags
TAG="dev-$(date +%Y%m%d-%H%M%S)"
ghcr.io/wiredquill/k8s-tmux:$TAG

# Feature branch tags  
TAG="feature-$(git branch --show-current | tr '/' '-')"
ghcr.io/wiredquill/k8s-tmux:$TAG

# Commit-based tags
TAG="commit-$(git rev-parse --short HEAD)"
ghcr.io/wiredquill/k8s-tmux:$TAG
```

### 2. Release Tags
```bash
# Semantic versioning
ghcr.io/wiredquill/k8s-tmux:v1.2.3
ghcr.io/wiredquill/k8s-tmux:v1.2
ghcr.io/wiredquill/k8s-tmux:v1
ghcr.io/wiredquill/k8s-tmux:latest

# Environment-specific
ghcr.io/wiredquill/k8s-tmux:prod-v1.2.3
ghcr.io/wiredquill/k8s-tmux:staging-v1.2.3
```

### 3. Special Tags
```bash
# Claude Code session tracking
ghcr.io/wiredquill/k8s-tmux:claude-$(date +%Y%m%d)

# Rollback tags
ghcr.io/wiredquill/k8s-tmux:rollback-$(date +%Y%m%d)

# Test images
ghcr.io/wiredquill/k8s-tmux:test-$(git rev-parse --short HEAD)
```

## Error Handling & Troubleshooting

### 1. BuildKit Connection Issues
```bash
# Verify BuildKit server connectivity
nc -zv 10.0.10.120 1234
buildctl debug workers

# Fallback to local Docker daemon
unset BUILDKIT_HOST
docker buildx build --push -t ghcr.io/wiredquill/k8s-tmux:fallback .
```

### 2. Registry Authentication Problems
```bash
# Re-authenticate with GitHub
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Verify registry permissions
docker pull ghcr.io/wiredquill/k8s-tmux:latest
docker push ghcr.io/wiredquill/k8s-tmux:test
```

### 3. Build Performance Issues
```bash
# Clear build cache
buildctl prune --all

# Check disk space on build server
ssh build-server "df -h"

# Monitor build progress
buildctl build --progress=plain ...
```

### 4. Multi-architecture Build Failures
```bash
# Build single architecture first
buildctl build --platform linux/amd64 ...

# Check emulation support
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

## Integration with Existing Scripts

### 1. Enhanced build.sh
```bash
#!/bin/bash
set -e

# Source: /Users/erquill/Documents/GitHub/k8s-tmux/scripts/build.sh
export BUILDKIT_HOST=tcp://10.0.10.120:1234

# Build with optimized caching
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:latest,push=true \
    --export-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache,mode=max \
    --import-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache

# Notify completion
curl -d "Build completed: k8s-tmux:latest" https://ntfy.wiredquill.com/builds
```

### 2. Claude-specific build script
```bash
#!/bin/bash
# Source: /Users/erquill/Documents/GitHub/k8s-tmux/scripts/claude-build.sh
set -e

TIMESTAMP=$(date +%Y%m%d-%H%M)
TAG="claude-session-$TIMESTAMP"

export BUILDKIT_HOST=tcp://10.0.10.120:1234

buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:$TAG,push=true \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:latest,push=true

echo "Built and pushed: ghcr.io/wiredquill/k8s-tmux:$TAG"
```

## Validation & Testing

### 1. Container Functionality Test
```bash
# Quick smoke test
docker run --rm ghcr.io/wiredquill/k8s-tmux:latest --version

# Full integration test
docker run -p 8080:8080 -p 7681:7681 ghcr.io/wiredquill/k8s-tmux:latest &
sleep 10
curl http://localhost:8080/api/files
curl http://localhost:7681
docker stop $(docker ps -q --filter ancestor=ghcr.io/wiredquill/k8s-tmux:latest)
```

### 2. Image Quality Checks
```bash
# Image size analysis
docker images ghcr.io/wiredquill/k8s-tmux --format "table {{.Tag}}\t{{.Size}}"

# Layer analysis
docker history ghcr.io/wiredquill/k8s-tmux:latest

# Security scan (if available)
docker scout cves ghcr.io/wiredquill/k8s-tmux:latest
```

### 3. Deployment Validation
```bash
# Update deployment with new image
kubectl set image deployment/k8s-tmux k8s-tmux=ghcr.io/wiredquill/k8s-tmux:$TAG -n ai-dev

# Verify rollout
kubectl rollout status deployment/k8s-tmux -n ai-dev

# Health check
kubectl get pods -n ai-dev
curl http://10.9.0.106/api/files
```

## Emergency Procedures

### 1. Build Server Down
```bash
# Switch to GitHub Actions build
git push origin main
# Monitor: https://github.com/wiredquill/k8s-tmux/actions

# Or use local Docker daemon
unset BUILDKIT_HOST
docker build -t ghcr.io/wiredquill/k8s-tmux:emergency .
docker push ghcr.io/wiredquill/k8s-tmux:emergency
```

### 2. Registry Issues
```bash
# Use backup registry
docker tag ghcr.io/wiredquill/k8s-tmux:latest localhost:5000/k8s-tmux:latest
docker push localhost:5000/k8s-tmux:latest

# Update deployment
kubectl set image deployment/k8s-tmux k8s-tmux=localhost:5000/k8s-tmux:latest -n ai-dev
```

### 3. Rollback Procedure
```bash
# Identify last known good image
kubectl rollout history deployment/k8s-tmux -n ai-dev

# Rollback deployment
kubectl rollout undo deployment/k8s-tmux -n ai-dev

# Or specify specific revision
kubectl rollout undo deployment/k8s-tmux --to-revision=2 -n ai-dev
```

## Usage Instructions

### For Task Tool Integration
```
Task Agent Prompt:
"Acting as the Docker Build Agent from agents/docker-build-agent.md, please build and optimize a container image for [project]. Use the remote BuildKit server at tcp://10.0.10.120:1234 and push to ghcr.io/wiredquill/k8s-tmux with appropriate tagging. Focus on build efficiency and production readiness."
```

### Common Build Scenarios

1. **Development Iteration**
   - Quick build with timestamp tag
   - Local cache optimization
   - Single architecture (amd64)

2. **Production Release**
   - Multi-architecture build
   - Semantic version tagging
   - Registry cache optimization
   - Security scanning

3. **Emergency Build**
   - Fast build with minimal optimization
   - Push to multiple registries
   - Immediate deployment ready

4. **Optimization Review**
   - Dockerfile analysis
   - Layer reduction strategies
   - Cache efficiency improvements
   - Size optimization

---

*This agent specification provides comprehensive Docker build capabilities with focus on remote BuildKit server integration, multi-architecture builds, and production-ready container optimization.*