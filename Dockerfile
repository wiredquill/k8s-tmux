FROM opensuse/leap:15.6

# Install base packages
RUN zypper refresh && \
    zypper install -y \
    curl \
    wget \
    git \
    bash-completion \
    vim \
    nano \
    tmux \
    zsh \
    sudo \
    openssh-clients \
    tar \
    gzip \
    unzip \
    jq \
    python3 \
    python3-pip \
    patterns-devel-base-devel_basis \
    ca-certificates \
    mc \
    tree \
    && zypper clean -a

# Install additional tools that might not be in main repos
RUN zypper install -y iputils || echo "iputils not available, skipping" && \
    zypper install -y nfs-client || echo "nfs-client not available, skipping" && \
    zypper install -y xclip || echo "xclip not available, skipping"

# Add Kubernetes repository and install kubectl/helm
RUN zypper addrepo https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64 kubernetes || echo "Failed to add k8s repo" && \
    zypper --gpg-auto-import-keys refresh || echo "Refresh failed" && \
    zypper install -y kubectl || \
    (echo "Installing kubectl manually..." && \
     curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
     install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
     rm kubectl)

# Install helm manually (more reliable)
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install kubectx and kubens with error handling
RUN KUBECTX_VERSION=$(curl -s https://api.github.com/repos/ahmetb/kubectx/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/') && \
    echo "Installing kubectx version: $KUBECTX_VERSION" && \
    curl -L "https://github.com/ahmetb/kubectx/releases/download/${KUBECTX_VERSION}/kubectx_${KUBECTX_VERSION}_linux_x86_64.tar.gz" | tar xz -C /tmp && \
    curl -L "https://github.com/ahmetb/kubectx/releases/download/${KUBECTX_VERSION}/kubens_${KUBECTX_VERSION}_linux_x86_64.tar.gz" | tar xz -C /tmp && \
    mv /tmp/kubectx /usr/local/bin/kubectx && \
    mv /tmp/kubens /usr/local/bin/kubens && \
    chmod +x /usr/local/bin/kubectx /usr/local/bin/kubens || \
    echo "kubectx/kubens installation failed, creating aliases instead" && \
    echo '#!/bin/bash\necho "kubectx not available - use kubectl config use-context"' > /usr/local/bin/kubectx && \
    echo '#!/bin/bash\necho "kubens not available - use kubectl config set-context --current --namespace"' > /usr/local/bin/kubens && \
    chmod +x /usr/local/bin/kubectx /usr/local/bin/kubens

# Install k9s
RUN curl -L https://github.com/derailed/k9s/releases/latest/download/k9s_Linux_amd64.tar.gz | tar xz -C /tmp && \
    mv /tmp/k9s /usr/local/bin/k9s && \
    chmod +x /usr/local/bin/k9s

# Install fastfetch (with error handling)
RUN curl -L https://github.com/fastfetch-cli/fastfetch/releases/latest/download/fastfetch-linux-amd64.tar.gz | tar xz -C /tmp || echo "fastfetch download failed" && \
    if [ -f /tmp/fastfetch-linux-amd64/usr/bin/fastfetch ]; then \
        mv /tmp/fastfetch-linux-amd64/usr/bin/fastfetch /usr/local/bin/fastfetch && \
        chmod +x /usr/local/bin/fastfetch; \
    else \
        echo "fastfetch not found, creating placeholder"; \
        echo '#!/bin/bash\necho "fastfetch not available"' > /usr/local/bin/fastfetch && \
        chmod +x /usr/local/bin/fastfetch; \
    fi && \
    rm -rf /tmp/fastfetch-linux-amd64

# Install btop (alternative system monitor)
RUN curl -L https://github.com/aristocratos/btop/releases/latest/download/btop-x86_64-linux-musl.tbz | tar xj -C /tmp || echo "btop download failed" && \
    if [ -f /tmp/btop/bin/btop ]; then \
        mv /tmp/btop/bin/btop /usr/local/bin/btop && \
        chmod +x /usr/local/bin/btop; \
    else \
        echo "btop not found, using htop alternative"; \
        zypper install -y htop || echo "htop also not available"; \
    fi && \
    rm -rf /tmp/btop

# Install ttyd for web terminal access
RUN curl -L https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64 -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# Install GitHub CLI manually (zypper package has issues)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg || echo "gpg setup failed, trying direct download" && \
    curl -L https://github.com/cli/cli/releases/latest/download/gh_2.74.2_linux_amd64.tar.gz | tar xz -C /tmp || \
    curl -L "$(curl -s https://api.github.com/repos/cli/cli/releases/latest | grep 'browser_download_url.*linux_amd64.tar.gz' | cut -d '"' -f 4)" | tar xz -C /tmp && \
    find /tmp -name "gh" -type f -executable | head -1 | xargs -I {} cp {} /usr/local/bin/gh && \
    chmod +x /usr/local/bin/gh && \
    rm -rf /tmp/gh_* || echo "gh installation completed with fallback"

# Install Claude
RUN curl -fsSL claude.ai/install.sh | bash

# Create remote mode script
RUN cat > /usr/local/bin/remote-toggle << 'EOF'
#!/bin/bash
NTFY_SERVER="https://ntfy.wiredquill.com"
NTFY_TOPIC="ai_communication"
REMOTE_MODE_FILE="/tmp/remote_mode_enabled"

if [ -f "$REMOTE_MODE_FILE" ]; then
    rm "$REMOTE_MODE_FILE"
    echo "🔴 Remote mode DISABLED"
    curl -s -X POST "$NTFY_SERVER/$NTFY_TOPIC" -H "Title: Claude Remote Mode" -d "Remote mode disabled"
else
    touch "$REMOTE_MODE_FILE"
    echo "🟢 Remote mode ENABLED"
    curl -s -X POST "$NTFY_SERVER/$NTFY_TOPIC" -H "Title: Claude Remote Mode" -d "Remote mode enabled"
fi
EOF
RUN chmod +x /usr/local/bin/remote-toggle

# Create user first
RUN useradd -m -s /bin/zsh dev && \
    echo "dev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create tmux run directory after user creation
RUN mkdir -p /run/tmux && chown -R dev:dev /run/tmux

# Configure tmux
COPY config/tmux.conf /home/dev/.tmux.conf

# Configure shell environments
USER dev
WORKDIR /home/dev
RUN sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" --unattended

# Enable bash completion and configure aliases
RUN echo 'source /etc/bash_completion' >> ~/.bashrc && \
    echo 'source <(kubectl completion bash)' >> ~/.bashrc && \
    echo 'source <(helm completion bash)' >> ~/.bashrc && \
    echo 'alias k=kubectl' >> ~/.bashrc && \
    echo 'alias kx=kubectx' >> ~/.bashrc && \
    echo 'alias kn=kubens' >> ~/.bashrc && \
    echo 'alias ll="ls -la"' >> ~/.bashrc && \
    echo 'alias la="ls -A"' >> ~/.bashrc && \
    echo 'alias l="ls -CF"' >> ~/.bashrc && \
    echo 'alias rmtoggle="remote-toggle"' >> ~/.bashrc && \
    echo 'export PS1="\[\033[1;32m\]\u@\h\[\033[00m\]:\[\033[1;34m\]\w\[\033[00m\]\$([ -f /tmp/remote_mode_enabled ] && echo \"\[\033[1;31m\][REMOTE]\[\033[00m\]\")$ "' >> ~/.bashrc

# Configure zsh with completion and aliases
RUN echo 'source <(kubectl completion zsh)' >> ~/.zshrc && \
    echo 'source <(helm completion zsh)' >> ~/.zshrc && \
    echo 'alias k=kubectl' >> ~/.zshrc && \
    echo 'alias kx=kubectx' >> ~/.zshrc && \
    echo 'alias kn=kubens' >> ~/.zshrc && \
    echo 'alias ll="ls -la"' >> ~/.zshrc && \
    echo 'alias la="ls -A"' >> ~/.zshrc && \
    echo 'alias l="ls -CF"' >> ~/.zshrc

# Copy initialization script
COPY --chown=dev:dev config/init.sh /home/dev/init.sh
RUN chmod +x /home/dev/init.sh

# Create mount points
USER root
RUN mkdir -p /mnt/k8s-tmux /mnt/WiredQuill && \
    chown dev:users /mnt/k8s-tmux /mnt/WiredQuill

USER dev
EXPOSE 7681

CMD ["/home/dev/init.sh"]