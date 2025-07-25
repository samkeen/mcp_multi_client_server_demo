# MCP Learning Demo

MCP Learning Demo is a comprehensive application that enables interactive chat capabilities with AI models through the Anthropic API. It provides both **console** and **web** interfaces, supporting document retrieval, command-based prompts, and extensible tool integrations via the MCP (Model Context Protocol) architecture.

**Note**: This project requires [uv](https://github.com/astral-sh/uv) for package management and execution. Traditional pip/python setups are not supported.

**Source**: This is the original code from Anthropic's MCP Introduction Course at: https://anthropic.skilljar.com/introduction-to-model-context-protocol

**Enhancements**: We have added educational code comments throughout the codebase and generated comprehensive training materials in the `docs/` folder to help developers learn MCP concepts.

**Course Notes**: The original course notes are in [anthropic_mcp_course_notes.md](anthropic_mcp_course_notes.md)

**Training Materials**: See `docs/` folder for auto-generated educational slides and presentations

## Architecture Overview

This application demonstrates a flexible, modular MCP architecture with dual interfaces:

### Architecture Components
- **`mcp_servers/`** - Modular MCP servers providing different capabilities (documents, calculator, etc.)
- **`mcp_clients/`** - Pluggable MCP client implementations for different transport types (stdio, HTTP)
- **`core/`** - Core application logic for chat interface, Claude API integration, and tool management
- **`web/`** - Web-based chat interface with full MCP observability
- **`web_server.py`** - HTTP server providing Claude API proxy and static file serving

### Key Features
- **Dual Interface**: Both console (CLI) and web-based chat interfaces
- **Transport Flexibility**: stdio transport for local development, HTTP transport for web/remote
- **Auto-discovery** - Automatically loads all available servers when no specific servers are specified
- **Multi-server composition** - Claude can use tools from multiple servers in a single response
- **Full Observability** - Web interface shows all MCP communications in real-time

## Prerequisites

- Python 3.9+
- Anthropic API Key

## Setup

### Step 1: Configure the environment variables

1. Copy the environment template and configure your API key:

```bash
cp .env.dist .env
```

2. Edit the `.env` file and add your Anthropic API key:

```
ANTHROPIC_API_KEY=""  # Enter your Anthropic API secret key
CLAUDE_MODEL=""       # Enter your Claude model (e.g., claude-3-sonnet-20240229)
```

### Proxy Configuration (Optional)

If you're behind a corporate proxy (e.g., Zscaler), add these settings to your `.env` file:

```
HTTP_PROXY=http://127.0.0.1:9000
HTTPS_PROXY=http://127.0.0.1:9000
NO_PROXY=localhost,127.0.0.1,.local

# SSL Configuration for corporate proxies
# Set to false if you're having SSL certificate issues with corporate proxies
VERIFY_SSL=false
```

The application will automatically detect and configure proxy settings when these environment variables are present.

### Step 2: Install dependencies

This project requires [uv](https://github.com/astral-sh/uv) for package management and running.

1. [Install uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation), if not already installed

2. Install dependencies:

```bash
uv sync
```

3. Run the project:

```bash
uv run main.py
```

### Running with Multiple MCP Servers

The application supports flexible MCP server loading:

**Auto-Discovery (Default):**
```bash
# Automatically loads all *mcp_server.py files in mcp_servers/
uv run main.py
```

**Manual Selection:**
```bash
# Load specific servers only
uv run main.py mcp_servers/calculator_mcp_server.py
uv run main.py mcp_servers/documents_mcp_server.py

# Multiple specific servers
uv run main.py mcp_servers/calculator_mcp_server.py mcp_servers/weather_mcp_server.py
```

The application will display which servers are loaded at startup.

See [MULTI_SERVER_USAGE.md](MULTI_SERVER_USAGE.md) for detailed examples.

## Usage

The MCP Learning Demo supports two interface modes:

### Console Mode (Default)
Run the traditional command-line interface:
```bash
# Auto-discover all available MCP servers
uv run main.py

# Use specific servers
uv run main.py mcp_servers/calculator_mcp_server.py mcp_servers/documents_mcp_server.py
```

### Web Mode
Run the web-based chat interface with full MCP observability:
```bash
# Auto-discover all available MCP servers  
uv run main.py --web

# Use specific servers
uv run main.py --web mcp_servers/calculator_mcp_server.py
```

Then open your browser to: **http://localhost:8000**

The web interface provides:
- **Split-panel design**: Chat on the left, MCP communication log on the right
- **Real-time observability**: See all MCP protocol messages as they happen  
- **Tool execution visualization**: Watch Claude use tools to answer questions
- **Responsive design**: Works on desktop and mobile devices

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.

## Educational Resources

### Training Materials
The `docs/` folder contains comprehensive educational materials:

- **`mcp-education-slides.md`**: Complete slide deck covering MCP concepts with speaker notes
- **`mcp-education-slides.html`**: Rendered HTML version of the slides

### Code Comments
The entire codebase has been enhanced with educational comments explaining:
- MCP architecture and design patterns
- Async programming patterns in Python
- Tool, resource, and prompt implementations
- Client-server communication flows
- Real-world development considerations

### Documentation
- **`CLAUDE.md`**: Developer guide for working with this codebase
- **`core/README.md`**: Explanation of the core module architecture
- **`anthropic_mcp_course_notes.md`**: Original course notes from Anthropic

## MCP Interaction Flows

The following diagrams illustrate how different types of MCP interactions work within the application:

### Tool Usage Flow

When Claude needs to call a tool (like reading a document):

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Claude
    participant ToolManager
    participant MCPClient
    participant MCPServer

    User->>CLI: "What does report.pdf contain?"
    CLI->>Claude: Send query + available tools
    Claude->>ToolManager: Request tool execution: read_doc_contents(doc_id="report.pdf")
    ToolManager->>MCPClient: call_tool("read_doc_contents", {"doc_id": "report.pdf"})
    MCPClient->>MCPServer: Execute tool via stdio
    MCPServer->>MCPClient: Return document content
    MCPClient->>ToolManager: Tool result
    ToolManager->>Claude: Formatted tool result
    Claude->>CLI: Response with document information
    CLI->>User: Display response
```

### Resource Access Flow

When a user mentions a document with @ syntax:

```mermaid
sequenceDiagram
    participant User
    participant CliChat
    participant MCPClient
    participant MCPServer

    User->>CliChat: "Summarize @deposition.md"
    CliChat->>CliChat: Parse @deposition.md mention
    CliChat->>MCPClient: read_resource("docs://documents/deposition.md")
    MCPClient->>MCPServer: Request resource via stdio
    MCPServer->>MCPClient: Return document content
    MCPClient->>CliChat: Document content
    CliChat->>CliChat: Build prompt with document content
    CliChat->>Claude: Send enriched prompt
    Claude->>CliChat: Response based on document
    CliChat->>User: Display summary
```

### Prompt Execution Flow

When a user executes a command with / syntax:

```mermaid
sequenceDiagram
    participant User
    participant CliChat
    participant MCPClient
    participant MCPServer
    participant Claude

    User->>CliChat: "/format report.pdf"
    CliChat->>CliChat: Parse command and arguments
    CliChat->>MCPClient: get_prompt("format", {"doc_id": "report.pdf"})
    MCPClient->>MCPServer: Request prompt template
    MCPServer->>MCPClient: Return prompt with instructions
    MCPClient->>CliChat: Formatted prompt messages
    CliChat->>CliChat: Add prompt to conversation history
    CliChat->>Claude: Send conversation with prompt
    Note over Claude: Claude sees the formatting instructions<br/>and may call tools to read/edit the document
    Claude->>CliChat: Execute formatting task
    CliChat->>User: Display formatted result
```

## Development

### Adding New Documents

Edit the `mcp_servers/documents_mcp_server.py` file to add new documents to the `docs` dictionary.

### Implementing MCP Features

To fully implement the MCP features:

1. Complete the TODOs in `mcp_servers/documents_mcp_server.py`
2. Implement the missing functionality in `mcp_clients/mcp_client_console.py`

### Linting and Typing Check

There are no lint or type checks implemented.

---

## Appendix: Feature Requests & Future Enhancements

### Current Architecture Limitations

**Document Features (When No Documents Server Loaded)**
When running with only non-document servers (e.g., `uv run main.py mcp_servers/calculator_mcp_server.py`):

- ❌ **@ Mentions**: `@document.pdf` references will not fetch document content
- ❌ **/ Commands**: `/format document.pdf` commands will not work

**Why This is Correct Behavior**:
- These features should only work when a documents server is available
- Clean architecture: no fake dependencies or hardcoded assumptions
- Graceful degradation: other features work normally

### Requested Enhancements

#### 1. Better User Feedback
**Priority**: Low  
**Description**: When user tries @mentions or /commands without documents server, provide helpful error message explaining they need to load documents server.

#### 2. Feature Detection UI
**Priority**: Low  
**Description**: CLI could show which features are available based on loaded servers:
```
Available features:
  ✅ Mathematical calculations (calculator server)
  ❌ Document operations (no documents server loaded)
```

#### 3. Dynamic Server Loading
**Priority**: Very Low  
**Description**: Allow adding/removing servers during runtime without restart.

#### 4. Additional Server Types
**Priority**: Medium  
**Suggested servers to implement**:
- **Weather Server**: Weather data and forecasts
- **File System Server**: File operations and management  
- **Database Server**: Data storage and retrieval
- **API Integration Server**: External service connections
- **Code Generation Server**: Programming assistance tools

#### 5. Enhanced Multi-Server Tool Composition
**Priority**: Medium  
**Description**: Better examples and documentation showing how Claude can compose tools from multiple servers in a single response (e.g., read document + perform calculations + edit results back).
