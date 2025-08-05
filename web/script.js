/**
 * MCP Web Chat Client
 * 
 * This client provides a web interface for interacting with MCP servers
 * through a Claude API proxy. It demonstrates the full MCP protocol
 * with excellent observability for learning purposes.
 */

class MCPWebChatClient {
    constructor() {
        // Configuration - loaded from server
        this.config = null;
        this.availableServers = {};
        this.connectedServers = {};
        
        // Claude API configuration
        this.claudeApiKey = null;
        
        // Chat state
        this.conversationHistory = [];
        this.availableTools = [];
        
        // UI elements
        this.elements = {
            chatInput: document.getElementById('chatInput'),
            sendButton: document.getElementById('sendButton'),
            chatMessages: document.getElementById('chatMessages'),
            consoleContent: document.getElementById('consoleContent'),
            clearConsole: document.getElementById('clearConsole'),
            statusDot: document.getElementById('statusDot'),
            statusText: document.querySelector('.status-text'),
            serverList: document.getElementById('serverList')
        };
        
        // Bind event handlers
        this.bindEvents();
        
        // Initialize the client
        this.initialize();
    }
    
    /**
     * Helper function to detect if a string is JSON
     */
    isJSON(str) {
        if (typeof str !== 'string') return false;
        try {
            const parsed = JSON.parse(str);
            return typeof parsed === 'object' && parsed !== null;
        } catch (e) {
            return false;
        }
    }
    
    /**
     * Helper function to format JSON with syntax highlighting
     */
    formatJSON(json, theme = 'chat') {
        let jsonObj;
        if (typeof json === 'string') {
            if (!this.isJSON(json)) return json;
            jsonObj = JSON.parse(json);
        } else {
            jsonObj = json;
        }
        
        const formatted = JSON.stringify(jsonObj, null, 2);
        const codeClass = theme === 'console' ? 'console-code' : 'chat-code';
        const buttonId = 'copy-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        
        // Store the formatted text in a data attribute to avoid escaping issues
        setTimeout(() => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.dataset.copyText = formatted;
            }
        }, 10);
        
        return `<div class="code-block ${codeClass}">
            <button id="${buttonId}" class="copy-button" onclick="window.mcpClient.copyToClipboardById('${buttonId}')">Copy</button>
            <pre style="margin: 0; padding-right: 3rem;"><code class="language-json">${this.escapeHtml(formatted)}</code></pre>
        </div>`;
    }
    
    /**
     * Copy text to clipboard using button ID (safer for large texts)
     */
    async copyToClipboardById(buttonId) {
        const button = document.getElementById(buttonId);
        if (!button) return;
        
        const text = button.dataset.copyText || '';
        
        try {
            await navigator.clipboard.writeText(text);
            
            // Show feedback
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('copied');
            }, 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
            button.textContent = 'Failed';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        }
    }
    
    /**
     * Helper function to escape HTML for safe display
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Helper function to escape text for HTML attributes
     */
    escapeForAttribute(text) {
        return text.replace(/'/g, '&#39;').replace(/"/g, '&quot;').replace(/\n/g, '\\n');
    }
    
    /**
     * Create a collapsible block for large content
     */
    createCollapsibleBlock(title, content, isExpanded = false) {
        const blockId = 'collapsible-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        
        // Check if content is large enough to warrant collapsing
        const lineCount = (content.match(/\n/g) || []).length + 1;
        if (lineCount <= 10 && content.length < 500) {
            // Small content, don't make it collapsible
            return `<div class="collapsible-block" style="width: 100%; box-sizing: border-box;">
                <div style="padding: 0.5rem 1rem; overflow-x: auto;">
                    <strong>${title}</strong>
                    <div style="margin-top: 0.5rem; max-width: 100%; overflow-x: auto;">${content}</div>
                </div>
            </div>`;
        }
        
        return `<div class="collapsible-block" style="width: 100%; box-sizing: border-box;">
            <div class="collapsible-header" onclick="window.mcpClient.toggleCollapsible('${blockId}')">
                <span><strong>${title}</strong> <span style="color: #888; font-size: 0.875rem;">(${lineCount} lines)</span></span>
                <span class="collapsible-icon ${isExpanded ? 'expanded' : ''}" id="${blockId}-icon">▶</span>
            </div>
            <div class="collapsible-content ${isExpanded ? 'expanded' : ''}" id="${blockId}" style="overflow-x: auto;">
                <div style="padding: 1rem; max-width: 100%; overflow-x: auto;">
                    ${content}
                </div>
            </div>
        </div>`;
    }
    
    /**
     * Toggle a collapsible block
     */
    toggleCollapsible(blockId) {
        const content = document.getElementById(blockId);
        const icon = document.getElementById(blockId + '-icon');
        
        if (content && icon) {
            content.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }
    }
    
    /**
     * Copy text to clipboard
     */
    async copyToClipboard(button, text) {
        try {
            // Unescape the text
            text = text.replace(/\\n/g, '\n').replace(/&#39;/g, "'").replace(/&quot;/g, '"');
            
            await navigator.clipboard.writeText(text);
            
            // Show feedback
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('copied');
            }, 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
            button.textContent = 'Failed';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        }
    }
    
    /**
     * Bind event handlers for UI interactions
     */
    bindEvents() {
        // Send message on button click
        this.elements.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key
        this.elements.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Clear console
        this.elements.clearConsole.addEventListener('click', () => this.clearConsole());
    }
    
    /**
     * Initialize the chat client by loading configuration and connecting to servers
     */
    async initialize() {
        try {
            this.logToConsole('info', 'Loading configuration...');
            
            // Load configuration from the web server
            const configResponse = await fetch('/config');
            if (!configResponse.ok) {
                throw new Error(`Config load failed: ${configResponse.status}`);
            }
            
            this.config = await configResponse.json();
            this.logToConsole('success', `Configuration loaded: ${JSON.stringify(this.config, null, 2)}`);
            
            // Get Claude API key from user
            this.claudeApiKey = this.getClaudeApiKey();
            if (!this.claudeApiKey) {
                this.logToConsole('error', 'Claude API key required for chat functionality');
                this.updateStatus('error', 'API key required');
                return;
            }
            
            // Connect to MCP servers
            await this.connectToServers();
            
            // Update UI
            this.updateServerList();
            this.updateStatus('connected', 'Ready');
            
            this.logToConsole('success', 'MCP Web Client fully initialized and ready!');
            
        } catch (error) {
            this.logToConsole('error', `Initialization failed: ${error.message}`);
            this.updateStatus('error', 'Initialization failed');
        }
    }
    
    /**
     * Get Claude API key from localStorage or prompt user
     */
    getClaudeApiKey() {
        // Try to get from localStorage first
        let apiKey = localStorage.getItem('claude_api_key');
        if (!apiKey) {
            apiKey = prompt('Please enter your Claude API key (will be stored locally):');
            if (apiKey) {
                localStorage.setItem('claude_api_key', apiKey);
            }
        }
        return apiKey;
    }
    
    /**
     * Connect to MCP servers via our web server proxy and discover their tools
     */
    async connectToServers() {
        this.logToConsole('info', 'Discovering available MCP tools via proxy...');
        
        try {
            // Use our proxy endpoint to list all tools from connected servers
            const response = await fetch('/list-tools');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Store the available tools
            this.availableTools = data.tools || [];
            
            // Update server status for UI
            const serverNames = Object.keys(this.config.mcp_servers || {});
            for (const serverName of serverNames) {
                this.connectedServers[serverName] = {
                    connected: true,
                    tools: this.availableTools.filter(tool => 
                        // Simple heuristic to group tools by server based on tool names
                        (serverName === 'calculator' && ['add', 'subtract', 'multiply', 'divide', 'power', 'square_root', 'calculate_expression'].includes(tool.name)) ||
                        (serverName === 'documents' && ['list_docs', 'read_doc_contents', 'search_docs'].includes(tool.name))
                    )
                };
            }
            
            this.logToConsole('success', `Connected to MCP servers via proxy - Found ${this.availableTools.length} tools: ${this.availableTools.map(t => t.name).join(', ')}`);
            
        } catch (error) {
            this.logToConsole('error', `Failed to connect to MCP servers: ${error.message}`);
            
            // Mark all servers as disconnected
            const serverNames = Object.keys(this.config.mcp_servers || {});
            for (const serverName of serverNames) {
                this.connectedServers[serverName] = {
                    connected: false,
                    tools: []
                };
            }
            this.availableTools = [];
        }
    }
    
    
    /**
     * Send a message to Claude via the proxy
     */
    async sendMessage() {
        const message = this.elements.chatInput.value.trim();
        if (!message) return;
        
        // Clear input and disable send button
        this.elements.chatInput.value = '';
        this.elements.sendButton.disabled = true;
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Add user message to conversation history
        this.conversationHistory.push({
            role: 'user',
            content: message
        });
        
        // Show thinking indicator
        const thinkingMessage = this.addMessage('assistant', '🤔 Thinking...');
        
        try {
            this.logToConsole('request', `Sending message to Claude: "${message}"`);
            
            // Call Claude API with available tools
            const claudeResponse = await this.callClaudeAPI(message);
            
            // Remove thinking indicator
            thinkingMessage.remove();
            
            // Handle Claude's response
            if (claudeResponse.hasToolUse) {
                // Claude wants to use tools - execute them
                await this.handleToolUse(claudeResponse);
            } else {
                // Regular text response - extract text from content blocks
                const textContent = claudeResponse.content
                    .filter(block => block.type === 'text')
                    .map(block => block.text)
                    .join('\n');
                
                this.addMessage('assistant', textContent);
                this.conversationHistory.push({
                    role: 'assistant', 
                    content: textContent
                });
            }
            
        } catch (error) {
            thinkingMessage.remove();
            this.addMessage('error', `Error: ${error.message}`);
            this.logToConsole('error', `Chat error: ${error.message}`);
        } finally {
            this.elements.sendButton.disabled = false;
        }
    }
    
    /**
     * Call Claude API via our proxy server
     */
    async callClaudeAPI(message) {
        const requestBody = {
            model: this.config.claude_model,
            max_tokens: 1000,
            messages: this.conversationHistory,
            system: `You are an AI assistant that helps users interact with MCP (Model Context Protocol) servers. You have access to tools for calculations and document reading. Use the appropriate tools when users ask questions that would benefit from them.`
        };
        
        // Add tools if available
        if (this.availableTools.length > 0) {
            requestBody.tools = this.availableTools.map(tool => ({
                name: tool.name,
                description: tool.description,
                input_schema: tool.input_schema  // Fixed: use snake_case to match server response
            }));
        }
        
        this.logToConsole('request', `Claude API request: ${JSON.stringify(requestBody, null, 2)}`);
        
        const response = await fetch('/claude-proxy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Claude API error: ${response.status} ${errorText}`);
        }
        
        const data = await response.json();
        this.logToConsole('response', `Claude API response: ${JSON.stringify(data, null, 2)}`);
        
        // Check if Claude wants to use tools
        const hasToolUse = data.content && data.content.some(block => block.type === 'tool_use');
        
        return {
            content: data.content,
            hasToolUse: hasToolUse,
            rawResponse: data
        };
    }
    
    /**
     * Handle tool use requests from Claude
     */
    async handleToolUse(claudeResponse) {
        const toolUseBlocks = claudeResponse.content.filter(block => block.type === 'tool_use');
        const textBlocks = claudeResponse.content.filter(block => block.type === 'text');
        
        // Show any text content first
        if (textBlocks.length > 0) {
            const textContent = textBlocks.map(block => block.text).join('\n');
            this.addMessage('assistant', textContent);
        }
        
        // Execute each tool
        const toolResults = [];
        for (const toolBlock of toolUseBlocks) {
            this.logToConsole('tool', `Executing tool: ${toolBlock.name} with input: ${JSON.stringify(toolBlock.input)}`);
            
            const toolMessage = this.addMessage('tool', `🔧 Using ${toolBlock.name}...`);
            
            try {
                const result = await this.executeToolOnServer(toolBlock.name, toolBlock.input);
                
                // Format the tool result - check if it's JSON
                let formattedResult;
                if (this.isJSON(result)) {
                    formattedResult = this.formatJSON(result, 'chat');
                } else if (typeof result === 'object' && result !== null) {
                    formattedResult = this.formatJSON(result, 'chat');
                } else {
                    formattedResult = this.escapeHtml(String(result));
                }
                
                // Create a nice display for the tool result
                const resultContent = `
                    <div style="display: flex; align-items: start; gap: 0.5rem;">
                        <span>🔧</span>
                        <div style="flex: 1;">
                            <strong>${toolBlock.name}</strong>
                            ${Object.keys(toolBlock.input || {}).length > 0 ? 
                                `<span style="color: #666; font-size: 0.875rem;"> (${Object.entries(toolBlock.input).map(([k,v]) => `${k}: ${v}`).join(', ')})</span>` : 
                                ''}
                            <div style="margin-top: 0.5rem;">
                                ${formattedResult}
                            </div>
                        </div>
                    </div>
                `;
                
                toolMessage.innerHTML = resultContent;
                
                // Trigger syntax highlighting
                if (typeof Prism !== 'undefined') {
                    setTimeout(() => {
                        Prism.highlightAllUnder(toolMessage);
                    }, 10);
                }
                
                toolResults.push({
                    tool_use_id: toolBlock.id,
                    content: result
                });
                
                this.logToConsole('success', `Tool ${toolBlock.name} completed: ${result}`);
                
            } catch (error) {
                toolMessage.innerHTML = `🔧 <strong>${toolBlock.name}</strong>: Error - ${error.message}`;
                
                toolResults.push({
                    tool_use_id: toolBlock.id,
                    content: `Error: ${error.message}`,
                    is_error: true
                });
                
                this.logToConsole('error', `Tool ${toolBlock.name} failed: ${error.message}`);
            }
        }
        
        // Add tool results to conversation history
        this.conversationHistory.push({
            role: 'assistant',
            content: claudeResponse.content
        });
        
        this.conversationHistory.push({
            role: 'user',
            content: toolResults.map(result => ({
                type: 'tool_result',
                tool_use_id: result.tool_use_id,
                content: result.content,
                is_error: result.is_error
            }))
        });
        
        // Get Claude's follow-up response
        const followUpResponse = await this.callClaudeAPI('Continue with the tool results.');
        
        // Extract text content from follow-up response
        const followUpText = followUpResponse.content
            .filter(block => block.type === 'text')
            .map(block => block.text)
            .join('\n');
        
        this.addMessage('assistant', followUpText);
        this.conversationHistory.push({
            role: 'assistant',
            content: followUpText
        });
    }
    
    /**
     * Execute a tool using the web server proxy
     */
    async executeToolOnServer(toolName, input) {
        this.logToConsole('tool', `Executing ${toolName} via proxy...`);
        
        try {
            // Use our proxy endpoint to execute the tool
            const response = await fetch('/call-tool', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tool_name: toolName,
                    tool_input: input,
                    tool_id: `web-${Date.now()}`
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (!data.success) {
                throw new Error(`Tool execution failed: ${data.content}`);
            }
            
            this.logToConsole('success', `Tool ${toolName} executed successfully: ${data.content}`);
            return data.content;
            
        } catch (error) {
            this.logToConsole('error', `Failed to execute ${toolName}: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Add a message to the chat interface
     */
    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-4 animate-fade-in ${type === 'user' ? 'text-right' : 'text-left'}`;
        
        const messageContent = document.createElement('div');
        // Use message-bubble class for proper width constraints
        messageContent.className = `inline-block message-bubble px-4 py-2 rounded-lg text-sm ${this.getMessageClasses(type)}`;
        messageContent.innerHTML = this.formatMessage(content);
        
        messageDiv.appendChild(messageContent);
        this.elements.chatMessages.appendChild(messageDiv);
        
        // Trigger Prism syntax highlighting for any code blocks in the message
        if (typeof Prism !== 'undefined') {
            setTimeout(() => {
                Prism.highlightAllUnder(messageDiv);
            }, 10);
        }
        
        // Scroll to bottom
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    /**
     * Get CSS classes for different message types
     */
    getMessageClasses(type) {
        switch (type) {
            case 'user':
                return 'bg-blue-500 text-white';
            case 'assistant':
                return 'bg-gray-200 text-gray-900';
            case 'tool':
                return 'bg-green-100 text-green-800 border border-green-200';
            case 'error':
                return 'bg-red-100 text-red-800 border border-red-200';
            default:
                return 'bg-gray-100 text-gray-900';
        }
    }
    
    /**
     * Format message content for display
     */
    formatMessage(content) {
        if (typeof content === 'string') {
            // Check if the content is JSON
            if (this.isJSON(content)) {
                return this.formatJSON(content, 'chat');
            }
            
            // Check for code blocks (simple heuristic: contains curly braces or looks like code)
            if (content.includes('{') && content.includes('}') && content.includes(':')) {
                // Try to parse as JSON first
                try {
                    const parsed = JSON.parse(content);
                    return this.formatJSON(parsed, 'chat');
                } catch (e) {
                    // Not valid JSON, but might be code - escape and format
                    return `<pre style="background: #f7f7f7; padding: 1rem; border-radius: 0.375rem; overflow-x: auto;"><code>${this.escapeHtml(content)}</code></pre>`;
                }
            }
            
            // Regular text - convert newlines to breaks
            return this.escapeHtml(content).replace(/\n/g, '<br>');
        }
        
        // Handle Claude API content format (array of content blocks)
        if (Array.isArray(content)) {
            return content
                .filter(block => block.type === 'text')
                .map(block => {
                    // Check each text block for JSON
                    if (this.isJSON(block.text)) {
                        return this.formatJSON(block.text, 'chat');
                    }
                    return this.escapeHtml(block.text).replace(/\n/g, '<br>');
                })
                .join('<br>');
        }
        
        // Handle single content block
        if (content && typeof content === 'object' && content.text) {
            if (this.isJSON(content.text)) {
                return this.formatJSON(content.text, 'chat');
            }
            return this.escapeHtml(content.text).replace(/\n/g, '<br>');
        }
        
        // Handle objects - format as JSON
        if (typeof content === 'object' && content !== null) {
            return this.formatJSON(content, 'chat');
        }
        
        // Fallback - escape and display
        return this.escapeHtml(String(content));
    }
    
    /**
     * Log a message to the console panel
     */
    logToConsole(type, message) {
        const timestamp = new Date().toLocaleTimeString();
        const logDiv = document.createElement('div');
        logDiv.className = 'flex gap-2 mb-1';
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'text-gray-400 whitespace-nowrap';
        timeSpan.textContent = `[${timestamp}]`;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex-1 ${this.getConsoleMessageClass(type)}`;
        
        // Check if message contains JSON or objects
        let formattedContent;
        
        // Check if message looks like it contains JSON
        if (typeof message === 'string' && (message.includes('request:') || message.includes('response:') || message.includes('{'))) {
            // Try to extract and format JSON from messages like "Claude API request: {...}"
            const jsonMatch = message.match(/^([^:]+:\s*)(.+)$/s);
            if (jsonMatch) {
                const prefix = jsonMatch[1];
                const jsonPart = jsonMatch[2];
                
                if (this.isJSON(jsonPart)) {
                    // Parse and format the JSON
                    const parsed = JSON.parse(jsonPart);
                    const lineCount = JSON.stringify(parsed, null, 2).split('\n').length;
                    
                    // Use collapsible block for large JSON
                    if (lineCount > 10) {
                        formattedContent = prefix + this.createCollapsibleBlock(
                            'JSON Data',
                            this.formatJSON(parsed, 'console'),
                            false // Start collapsed
                        );
                    } else {
                        formattedContent = prefix + '<br>' + this.formatJSON(parsed, 'console');
                    }
                    messageDiv.innerHTML = formattedContent;
                } else {
                    // Not JSON, display as regular text
                    messageDiv.textContent = message;
                }
            } else if (this.isJSON(message)) {
                // Entire message is JSON
                const parsed = JSON.parse(message);
                messageDiv.innerHTML = this.formatJSON(parsed, 'console');
            } else {
                // Regular message
                messageDiv.textContent = message;
            }
        } else if (typeof message === 'object' && message !== null) {
            // Direct object passed
            messageDiv.innerHTML = this.formatJSON(message, 'console');
        } else {
            // Regular text message
            messageDiv.textContent = message;
        }
        
        logDiv.appendChild(timeSpan);
        logDiv.appendChild(messageDiv);
        
        this.elements.consoleContent.appendChild(logDiv);
        this.elements.consoleContent.scrollTop = this.elements.consoleContent.scrollHeight;
        
        // Trigger Prism syntax highlighting for any new code blocks
        if (typeof Prism !== 'undefined') {
            setTimeout(() => {
                Prism.highlightAllUnder(logDiv);
            }, 10);
        }
    }
    
    /**
     * Get CSS class for console message types
     */
    getConsoleMessageClass(type) {
        switch (type) {
            case 'info':
                return 'text-blue-400';
            case 'success':
                return 'text-green-400';
            case 'error':
                return 'text-red-400';
            case 'request':
                return 'text-yellow-400';
            case 'response':
                return 'text-purple-400';
            case 'tool':
                return 'text-orange-400';
            default:
                return 'text-gray-300';
        }
    }
    
    /**
     * Clear the console panel
     */
    clearConsole() {
        this.elements.consoleContent.innerHTML = `
            <div class="flex gap-2 mb-2">
                <span class="text-gray-400 whitespace-nowrap">[${new Date().toLocaleTimeString()}]</span>
                <span class="text-teal-400">Console cleared.</span>
            </div>
        `;
    }
    
    /**
     * Update connection status indicator
     */
    updateStatus(status, text) {
        const statusClasses = {
            'connected': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500'
        };
        
        this.elements.statusDot.className = `w-2 h-2 rounded-full ${statusClasses[status] || 'bg-gray-500'}`;
        this.elements.statusText.textContent = text;
    }
    
    /**
     * Update the server list display
     */
    updateServerList() {
        const serverNames = Object.keys(this.connectedServers);
        this.elements.serverList.textContent = serverNames.length > 0 
            ? serverNames.join(', ') 
            : 'None connected';
    }
}

// Initialize the chat client when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.mcpClient = new MCPWebChatClient();
});