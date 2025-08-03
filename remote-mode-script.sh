#!/bin/bash

# Remote Mode Toggle Script for Claude AI Integration
# Adds remote mode functionality to existing terminal

NTFY_SERVER="http://10.0.0.10:8080"  # Adjust this to your ntfy server
NTFY_TOPIC="wq_ai_82e3j"
REMOTE_MODE_FILE="/tmp/remote_mode_enabled"
LOG_FILE="/tmp/claude_monitor.log"

# Function to send notification to ntfy
send_ntfy() {
    local title="$1"
    local message="$2"
    local priority="${3:-3}"
    
    curl -s -X POST "$NTFY_SERVER/$NTFY_TOPIC" \
        -H "Title: $title" \
        -H "Priority: $priority" \
        -d "$message" >> "$LOG_FILE" 2>&1
}

# Function to toggle remote mode
toggle_remote_mode() {
    if [ -f "$REMOTE_MODE_FILE" ]; then
        rm "$REMOTE_MODE_FILE"
        echo "🔴 Remote mode DISABLED"
        send_ntfy "Claude Remote Mode" "Remote mode disabled" 2
    else
        touch "$REMOTE_MODE_FILE"
        echo "🟢 Remote mode ENABLED"
        echo "Claude responses will be sent to ntfy when multiple options are available"
        send_ntfy "Claude Remote Mode" "Remote mode enabled - monitoring Claude responses" 4
    fi
}

# Function to check if remote mode is enabled
is_remote_mode() {
    [ -f "$REMOTE_MODE_FILE" ]
}

# Function to monitor Claude output and detect multiple responses
monitor_claude_responses() {
    if ! is_remote_mode; then
        return
    fi
    
    # This would need to be integrated with Claude's output
    # For now, this is a placeholder that could be called when Claude presents options
    local responses="$1"
    if [ -n "$responses" ]; then
        send_ntfy "Claude Options Available" "$responses" 5
        echo "📱 Sent options to ntfy: $NTFY_TOPIC"
    fi
}

# Create remote mode toggle command
create_remote_toggle() {
    cat > /usr/local/bin/remote-toggle << 'EOF'
#!/bin/bash
source /tmp/remote-mode-script.sh
toggle_remote_mode
EOF
    chmod +x /usr/local/bin/remote-toggle
}

# Create Claude response sender
create_claude_sender() {
    cat > /usr/local/bin/send-claude-options << 'EOF'
#!/bin/bash
source /tmp/remote-mode-script.sh
if [ $# -eq 0 ]; then
    echo "Usage: send-claude-options 'Option 1|Option 2|Option 3'"
    exit 1
fi
monitor_claude_responses "$1"
EOF
    chmod +x /usr/local/bin/send-claude-options
}

# Initialize remote mode functionality
init_remote_mode() {
    echo "Initializing remote mode functionality..."
    create_remote_toggle
    create_claude_sender
    
    # Add to shell aliases
    echo "alias rm='remote-toggle'" >> ~/.bashrc
    echo "alias send-options='send-claude-options'" >> ~/.bashrc
    
    echo "📡 Remote mode functionality initialized"
    echo "Commands available:"
    echo "  remote-toggle  - Toggle remote mode on/off"
    echo "  send-claude-options 'opt1|opt2|opt3' - Send options to ntfy"
    echo "  rm - Alias for remote-toggle"
}

# If script is run directly, initialize
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    init_remote_mode
fi