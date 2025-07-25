# MCP Web Chat Interface

This directory contains the web-based chat interface for the MCP Learning Demo. It provides a split-panel design with chat functionality and full observability of MCP protocol communications.

## Features

### Chat Interface (Left Panel)
- **Interactive Chat**: Send messages and receive responses from Claude
- **Tool Integration**: Automatic execution of MCP tools when needed
- **Real-time Updates**: Messages appear with smooth animations
- **Responsive Design**: Works on desktop and mobile devices

### Console Log (Right Panel)
- **MCP Communication Log**: See all MCP protocol messages in real-time
- **Color-coded Messages**: Different colors for requests, responses, errors, etc.
- **Timestamped Entries**: Each log entry shows the exact time
- **JSON Formatting**: Complex data structures are properly formatted
- **Clear Function**: Reset the console log at any time

### Status Indicators
- **Connection Status**: Visual indicator (red/green dot) showing connection state
- **Server List**: Display of connected MCP servers
- **Error Handling**: Clear error messages and status updates

## Files

- **`index.html`**: Main HTML structure with Tailwind CSS styling
- **`script.js`**: JavaScript client implementing MCP communication and UI logic
- **`README.md`**: This documentation file

## Architecture

### Frontend Components
1. **MCPWebChatClient Class**: Main client handling all functionality
2. **Claude API Integration**: Communicates with Claude via the proxy server
3. **MCP Tool Execution**: Simulated tool calls for demonstration
4. **UI Management**: Real-time updates and responsive design

### Communication Flow
1. User sends message via chat input
2. Frontend calls Claude API through `/claude-proxy` endpoint
3. Claude determines if tools are needed
4. If tools are needed, frontend executes them (simulated)
5. Tool results are sent back to Claude
6. Claude provides final response
7. All communications are logged to the console panel

## Learning Objectives

This interface demonstrates:
- **MCP Protocol**: How clients communicate with MCP servers
- **Tool Integration**: How AI assistants use tools to enhance capabilities
- **Observability**: How to debug and understand MCP communications
- **Web Integration**: How to build web interfaces for MCP applications

## Usage

The web interface is automatically served when running:
```bash
uv run main.py --web
```

Then open your browser to: http://localhost:8000

## Customization

### Adding New Tools
1. Update the `availableTools` array in `script.js`
2. Add corresponding tool execution logic in `executeSimulatedTool()`
3. Tools will automatically appear in Claude's tool list

### Styling Changes
- Modify Tailwind CSS classes in `index.html`
- The design uses a responsive grid layout
- Color scheme can be adjusted by changing CSS classes

### Backend Integration
- The frontend expects MCP servers to be running on ports 8001, 8002, etc.
- Claude API proxy should be available at `/claude-proxy`
- Configuration endpoint should provide server information at `/config`

## Educational Value

This web interface serves as an excellent learning tool because:
1. **Visual Feedback**: See exactly what's happening during MCP communications
2. **Interactive Learning**: Try different queries and see how tools are used
3. **Protocol Understanding**: Watch the full request/response cycle
4. **Debugging Skills**: Learn to interpret MCP protocol messages
5. **Architecture Patterns**: Understand how web clients integrate with MCP servers