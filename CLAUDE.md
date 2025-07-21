# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) Chat application - a CLI tool for interactive conversations with Claude through the Anthropic API. It's based on Anthropic's MCP course (https://anthropic.skilljar.com/introduction-to-model-context-protocol).

## Project Structure

```
├── main.py                    # Entry point - initializes MCP clients and CLI
├── mcp_client.py             # MCP client for connecting to servers
├── mcp_servers/              # Directory containing MCP servers
│   ├── documents_mcp_server.py  # Document management server
│   └── README.md             # Guide for adding new servers
├── core/                     # Core application modules
│   ├── claude.py            # Claude API wrapper
│   ├── cli.py               # CLI application and UI
│   ├── cli_chat.py          # Chat interface logic
│   ├── chat.py              # Core chat functionality
│   └── tools.py             # Tool implementations
└── docs/                     # Educational materials and slides
```

## Key Commands

### Running the Application
```bash
# Run the main application
uv run main.py

# To run with additional MCP servers
uv run main.py mcp_servers/calculator_mcp_server.py mcp_servers/weather_mcp_server.py
```

### Installation
```bash
# This project requires uv
uv sync
```

## Architecture

### Core Components

1. **MCP Client/Server Architecture**
   - `mcp_servers/documents_mcp_server.py`: Implements MCP server with document management tools
   - `mcp_client.py`: MCP client for connecting to servers
   - `main.py`: Entry point that initializes MCP clients and starts CLI

2. **Core Module (`core/`)**
   - `claude.py`: Wrapper for Anthropic's Claude API
   - `cli.py`: Main CLI application with prompt toolkit integration
   - `cli_chat.py`: Chat interface handling user inputs and Claude responses
   - `chat.py`: Core chat functionality and message handling
   - `tools.py`: Tool implementations and utilities

### Key Design Patterns

- **MCP Protocol**: Uses Model Context Protocol for extensible tool integration
- **Document Retrieval**: `@` mentions trigger document retrieval from MCP server
- **Command System**: `/` prefix executes MCP-defined prompts/commands
- **Async Architecture**: Built on asyncio for concurrent MCP server connections

### Environment Configuration

Required `.env` file:
```
ANTHROPIC_API_KEY=""  # Required: Your Anthropic API key
CLAUDE_MODEL=""       # Required: Model ID (e.g., claude-3-sonnet-20240229)

# Optional: Proxy configuration for corporate environments
HTTP_PROXY=http://127.0.0.1:9000
HTTPS_PROXY=http://127.0.0.1:9000
NO_PROXY=localhost,127.0.0.1,.local
VERIFY_SSL=false  # Set to false for corporate proxies with SSL issues
```

### Adding Features

1. **New Documents**: Add to `docs` dictionary in `mcp_servers/documents_mcp_server.py`
2. **New MCP Tools**: Implement in MCP server files following MCP protocol
3. **New Commands**: Add prompts to MCP server's prompt list
4. **New MCP Servers**: Create new server files in the `mcp_servers/` directory

### Development Notes

- No linting or type checking currently configured
- Windows requires `asyncio.WindowsProactorEventLoopPolicy()` (handled in main.py:63-64)
- Project uses modern Python packaging with `pyproject.toml`
- Supports Python 3.10+ (per pyproject.toml)