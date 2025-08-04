// Terminal Automation System for Claude AI Integration
class TerminalAutomation {
    constructor(terminal) {
        this.terminal = terminal;
        this.scheduledMessages = [];
        this.autoResponseEnabled = false;
        this.autoResponseRules = {
            twoChoice: 1,  // Press 1 for 2-choice questions
            threeChoice: 2  // Press 2 for 3-choice questions
        };
        this.messageQueue = [];
        this.isProcessing = false;
        
        this.init();
    }

    init() {
        // Start the message scheduler
        setInterval(() => this.processScheduledMessages(), 1000);
        
        // Monitor terminal output for choice questions
        this.observeTerminalOutput();
    }

    // Schedule a message to be sent at a specific time
    scheduleMessage(message, timestamp) {
        const scheduledTime = new Date(timestamp);
        this.scheduledMessages.push({
            message: message,
            timestamp: scheduledTime,
            id: Date.now() + Math.random()
        });
        
        // Sort by timestamp
        this.scheduledMessages.sort((a, b) => a.timestamp - b.timestamp);
        
        console.log(`📅 Scheduled message for ${scheduledTime.toLocaleString()}: "${message}"`);
        this.updateScheduleDisplay();
    }

    // Process scheduled messages
    processScheduledMessages() {
        const now = new Date();
        const readyMessages = this.scheduledMessages.filter(msg => msg.timestamp <= now);
        
        readyMessages.forEach(msg => {
            this.sendMessage(msg.message);
            this.scheduledMessages = this.scheduledMessages.filter(m => m.id !== msg.id);
        });
        
        if (readyMessages.length > 0) {
            this.updateScheduleDisplay();
        }
    }

    // Send a message as if typed by user
    sendMessage(message) {
        if (!this.terminal) return;
        
        console.log(`🤖 Auto-sending: "${message}"`);
        
        // Simulate typing each character
        const chars = message.split('');
        let index = 0;
        
        const typeChar = () => {
            if (index < chars.length) {
                // Send character to terminal
                this.terminal.write(chars[index]);
                index++;
                setTimeout(typeChar, 50); // 50ms delay between characters
            } else {
                // Send Enter key
                setTimeout(() => {
                    this.terminal.write('\r');
                }, 100);
            }
        };
        
        typeChar();
    }

    // Observe terminal output for choice questions
    observeTerminalOutput() {
        if (!this.terminal) return;
        
        // Hook into terminal data events
        const originalWrite = this.terminal.write;
        this.terminal.write = (data) => {
            originalWrite.call(this.terminal, data);
            this.analyzeOutput(data);
        };
    }

    // Analyze terminal output for auto-response opportunities
    analyzeOutput(data) {
        if (!this.autoResponseEnabled) return;
        
        const text = data.toString().toLowerCase();
        
        // Detect 2-choice questions (common patterns)
        if (this.isChoiceQuestion(text, 2)) {
            setTimeout(() => {
                console.log(`🔄 Auto-responding to 2-choice question with: ${this.autoResponseRules.twoChoice}`);
                this.sendMessage(this.autoResponseRules.twoChoice.toString());
            }, 1000); // Wait 1 second before responding
        }
        
        // Detect 3-choice questions
        else if (this.isChoiceQuestion(text, 3)) {
            setTimeout(() => {
                console.log(`🔄 Auto-responding to 3-choice question with: ${this.autoResponseRules.threeChoice}`);
                this.sendMessage(this.autoResponseRules.threeChoice.toString());
            }, 1000);
        }
    }

    // Detect if text contains a choice question
    isChoiceQuestion(text, numChoices) {
        const patterns = {
            2: [
                /\b(1\.|1\))\s.*\b(2\.|2\))\s/,
                /choose.*[12]/i,
                /select.*[12]/i,
                /option.*[12]/i
            ],
            3: [
                /\b(1\.|1\))\s.*\b(2\.|2\))\s.*\b(3\.|3\))\s/,
                /choose.*[123]/i,
                /select.*[123]/i,
                /option.*[123]/i
            ]
        };
        
        return patterns[numChoices]?.some(pattern => pattern.test(text)) || false;
    }

    // Toggle auto-response mode
    toggleAutoResponse() {
        this.autoResponseEnabled = !this.autoResponseEnabled;
        console.log(`🔄 Auto-response mode: ${this.autoResponseEnabled ? 'ENABLED' : 'DISABLED'}`);
        this.updateStatusDisplay();
        return this.autoResponseEnabled;
    }

    // Update auto-response rules
    updateAutoResponseRules(twoChoice, threeChoice) {
        this.autoResponseRules.twoChoice = parseInt(twoChoice) || 1;
        this.autoResponseRules.threeChoice = parseInt(threeChoice) || 2;
        console.log(`📋 Updated auto-response rules: 2-choice→${this.autoResponseRules.twoChoice}, 3-choice→${this.autoResponseRules.threeChoice}`);
    }

    // Cancel scheduled message
    cancelScheduledMessage(id) {
        this.scheduledMessages = this.scheduledMessages.filter(msg => msg.id !== id);
        this.updateScheduleDisplay();
    }

    // Get current status
    getStatus() {
        return {
            autoResponseEnabled: this.autoResponseEnabled,
            scheduledMessages: this.scheduledMessages.length,
            rules: this.autoResponseRules
        };
    }

    // Update UI displays
    updateStatusDisplay() {
        const statusEl = document.getElementById('automation-status');
        if (statusEl) {
            const status = this.getStatus();
            statusEl.innerHTML = `
                <div>🔄 Auto-response: ${status.autoResponseEnabled ? 'ON' : 'OFF'}</div>
                <div>📅 Scheduled: ${status.scheduledMessages}</div>
                <div>📋 Rules: 2-choice→${status.rules.twoChoice}, 3-choice→${status.rules.threeChoice}</div>
            `;
        }
    }

    updateScheduleDisplay() {
        const scheduleEl = document.getElementById('schedule-list');
        if (scheduleEl) {
            scheduleEl.innerHTML = this.scheduledMessages.map(msg => `
                <div class="scheduled-message">
                    <span>${msg.timestamp.toLocaleString()}</span>
                    <span>"${msg.message}"</span>
                    <button onclick="automation.cancelScheduledMessage(${msg.id})">❌</button>
                </div>
            `).join('');
        }
    }
}

// UI Helper Functions
function scheduleMessageFromUI() {
    const message = document.getElementById('schedule-message').value;
    const datetime = document.getElementById('schedule-time').value;
    
    if (!message || !datetime) {
        alert('Please enter both message and time');
        return;
    }
    
    automation.scheduleMessage(message, new Date(datetime));
    
    // Clear form
    document.getElementById('schedule-message').value = '';
    document.getElementById('schedule-time').value = '';
}

function toggleAutoResponseFromUI() {
    const enabled = automation.toggleAutoResponse();
    const button = document.getElementById('auto-response-toggle');
    if (button) {
        button.textContent = enabled ? '🔄 Auto-Response: ON' : '🔄 Auto-Response: OFF';
        button.className = enabled ? 'btn-success' : 'btn-secondary';
    }
}

function updateRulesFromUI() {
    const twoChoice = document.getElementById('two-choice-rule').value;
    const threeChoice = document.getElementById('three-choice-rule').value;
    automation.updateAutoResponseRules(twoChoice, threeChoice);
}

// Global automation instance (will be initialized when terminal is ready)
let automation = null;