# Docker Build Agent Specification

## Agent Overview
A comprehensive Docker build agent specializing in remote BuildKit operations, container optimization, and GitHub Container Registry integration for the k8s-tmux project.

## Core Capabilities

### 1. Build Server Integration
- **Remote BuildKit Connection**: Expert in connecting to `tcp://10.0.10.120:1234`
- **buildctl Command Mastery**: Advanced usage of BuildKit client commands
- **Multi-Architecture Builds**: Support for `linux/amd64` and `linux/arm64`
- **Registry Integration**: Seamless push to `ghcr.io/wiredquill/k8s-tmux`
- **Build Cache Optimization**: Layer caching and reuse strategies

### 2. Docker Build Optimization

#### Dockerfile Analysis & Optimization
```bash
# Current image analysis command template
docker history ghcr.io/wiredquill/k8s-tmux:latest --no-trunc
docker inspect ghcr.io/wiredquill/k8s-tmux:latest
```

**Optimization Areas:**
- **Layer Consolidation**: Combine RUN commands to reduce layers
- **Package Manager Cleanup**: Ensure `zypper clean -a` after installs
- **Multi-stage Builds**: Separate build dependencies from runtime
- **Base Image Security**: Regular opensuse/leap:15.6 updates
- **Size Reduction**: Remove unnecessary packages and cache files

#### Security Best Practices
- **Non-root User**: Already implemented with `dev` user
- **Minimal Attack Surface**: Remove unnecessary tools from final image
- **Secret Management**: Proper handling of registry credentials
- **Vulnerability Scanning**: Container image security assessment

### 3. Remote Build Execution

#### Primary Build Command Template
```bash
export BUILDKIT_HOST=tcp://10.0.10.120:1234
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:latest,push=true \
    --export-cache type=inline \
    --import-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache
```

#### Multi-Architecture Build
```bash
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:latest,push=true \
    --platform linux/amd64,linux/arm64 \
    --export-cache type=inline
```

#### Error Handling & Diagnostics
```bash
# Connection test
buildctl --addr tcp://10.0.10.120:1234 debug info

# Build logs with verbose output
buildctl build --progress=plain --frontend dockerfile.v0 ...

# Registry authentication check
docker login ghcr.io -u ${GITHUB_ACTOR} -p ${GITHUB_TOKEN}
```

### 4. Registry Management

#### Authentication Setup
```bash
# GitHub Container Registry login
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# buildctl with registry auth
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:tag,push=true,registry.insecure=false
```

#### Tagging Strategy
- **Latest**: `ghcr.io/wiredquill/k8s-tmux:latest` (main branch)
- **Version**: `ghcr.io/wiredquill/k8s-tmux:v1.2.3` (semantic versioning)
- **SHA Tags**: `ghcr.io/wiredquill/k8s-tmux:sha-abc1234` (commit-based)
- **Feature**: `ghcr.io/wiredquill/k8s-tmux:feature-name` (development)
- **Claude Session**: `ghcr.io/wiredquill/k8s-tmux:claude-YYYYMMDD-HHMMSS`

### 5. Build Cache Optimization

#### Cache Strategies
```bash
# Inline cache export/import
--export-cache type=inline
--import-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache

# Registry cache (recommended for CI/CD)
--export-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache,mode=max
--import-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache

# GitHub Actions cache
--cache-from type=gha
--cache-to type=gha,mode=max
```

#### Cache Invalidation
- Dockerfile changes automatically invalidate cache
- Base image updates require cache rebuild
- Package version changes break cache layers

### 6. Build Troubleshooting

#### Common Issues & Solutions

**Connection Issues:**
```bash
# Test BuildKit connection
nc -zv 10.0.10.120 1234
buildctl --addr tcp://10.0.10.120:1234 debug info
```

**Registry Authentication:**
```bash
# Verify GitHub token permissions
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Test registry push permissions
docker pull hello-world
docker tag hello-world ghcr.io/wiredquill/test:latest
docker push ghcr.io/wiredquill/test:latest
```

**Build Performance:**
```bash
# Enable BuildKit metrics
export BUILDKIT_HOST=tcp://10.0.10.120:1234
buildctl debug info | grep -A 10 "buildkit version"

# Parallel build jobs
buildctl build --opt build-arg:BUILDKIT_INLINE_CACHE=1
```

### 7. Specific Build Commands

#### Development Build
```bash
#!/bin/bash
export BUILDKIT_HOST=tcp://10.0.10.120:1234
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
TAG="ghcr.io/wiredquill/k8s-tmux:dev-$TIMESTAMP"

buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=$TAG,push=true \
    --export-cache type=inline \
    --progress=plain
```

#### Production Build
```bash
#!/bin/bash
export BUILDKIT_HOST=tcp://10.0.10.120:1234
VERSION=${1:-latest}
TAG="ghcr.io/wiredquill/k8s-tmux:$VERSION"

buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=$TAG,push=true \
    --platform linux/amd64,linux/arm64 \
    --export-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache,mode=max \
    --import-cache type=registry,ref=ghcr.io/wiredquill/k8s-tmux:buildcache
```

#### Emergency Rollback
```bash
#!/bin/bash
PREVIOUS_TAG=${1:-$(git rev-parse HEAD~1 | cut -c1-8)}
docker pull ghcr.io/wiredquill/k8s-tmux:sha-$PREVIOUS_TAG
docker tag ghcr.io/wiredquill/k8s-tmux:sha-$PREVIOUS_TAG ghcr.io/wiredquill/k8s-tmux:latest
docker push ghcr.io/wiredquill/k8s-tmux:latest
```

### 8. GitHub Actions Integration

#### Workflow Trigger Commands
```bash
# Trigger build via gh CLI
gh workflow run build.yaml

# Trigger with parameters
gh workflow run claude-trigger.yaml \
    -f trigger_source="manual" \
    -f container_changes="Updated Dockerfile"
```

#### Workflow Status Monitoring
```bash
# Check workflow status
gh run list --workflow=build.yaml --limit=5

# View workflow logs
gh run view --log
```

### 9. Container Validation & Testing

#### Post-Build Validation
```bash
# Test container functionality
docker run --rm ghcr.io/wiredquill/k8s-tmux:latest /bin/bash -c "
    which kubectl && \
    which helm && \
    which tmux && \
    which zsh && \
    echo 'Container validation passed'
"

# Security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image ghcr.io/wiredquill/k8s-tmux:latest
```

#### Size Analysis
```bash
# Container size comparison
docker images ghcr.io/wiredquill/k8s-tmux --format "table {{.Tag}}\t{{.Size}}"

# Layer analysis
docker history ghcr.io/wiredquill/k8s-tmux:latest --format "table {{.CreatedBy}}\t{{.Size}}"
```

### 10. Monitoring & Alerting

#### Build Notifications
```bash
# Success notification
curl -X POST "https://ntfy.wiredquill.com/ai_communication" \
    -H "Title: Container Build Success" \
    -d "k8s-tmux container built successfully: $TAG"

# Failure notification
curl -X POST "https://ntfy.wiredquill.com/ai_communication" \
    -H "Title: Container Build Failed" \
    -d "k8s-tmux container build failed. Check logs."
```

## Current Project Analysis

### Existing Infrastructure
- **Dockerfile**: OpenSUSE Leap 15.6 base with comprehensive tooling
- **BuildKit Server**: Remote server at `10.0.10.120:1234`
- **Registry**: GitHub Container Registry (`ghcr.io/wiredquill/k8s-tmux`)
- **CI/CD**: GitHub Actions with Docker Buildx
- **Tools**: kubectl, helm, k9s, Claude CLI, tmux, zsh

### Optimization Opportunities
1. **Multi-stage Build**: Separate tool building from runtime
2. **Layer Caching**: Better use of BuildKit cache features
3. **Package Consolidation**: Combine similar package installations
4. **Base Image Updates**: Automated security updates
5. **Size Reduction**: Remove build-time dependencies

### Integration Points
- **Existing Scripts**: 
  - `/scripts/build.sh` - Basic BuildKit integration
  - `/scripts/claude-build.sh` - Multi-option build trigger
- **GitHub Actions**: 
  - Build workflow with GitHub Actions runner fallback
  - Automated tagging and registry push
- **Kubernetes Deployments**: 
  - Multiple deployment configurations in `/deployments/`

## Usage Examples

### Daily Development Workflow
```bash
# 1. Make Dockerfile changes
vim Dockerfile

# 2. Test build locally (without push)
export BUILDKIT_HOST=tcp://10.0.10.120:1234
buildctl build --frontend dockerfile.v0 --local context=. --local dockerfile=.

# 3. Build and push development tag
./scripts/claude-build.sh "Updated kubectl version"

# 4. Test deployment
kubectl set image deployment/k8s-tmux container=ghcr.io/wiredquill/k8s-tmux:dev-$(date +%Y%m%d-%H%M%S)
```

### Production Release Workflow
```bash
# 1. Tag release
git tag v1.2.3
git push origin v1.2.3

# 2. Build production image
export BUILDKIT_HOST=tcp://10.0.10.120:1234
buildctl build \
    --frontend dockerfile.v0 \
    --local context=. \
    --local dockerfile=. \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:v1.2.3,push=true \
    --output type=image,name=ghcr.io/wiredquill/k8s-tmux:latest,push=true

# 3. Update production deployments
kubectl set image deployment/k8s-tmux container=ghcr.io/wiredquill/k8s-tmux:v1.2.3
```

This agent specification provides comprehensive Docker build capabilities tailored specifically to your remote BuildKit setup and GitHub Container Registry integration, with emphasis on optimization, security, and reliability.