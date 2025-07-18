# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) Chat application - a CLI tool for interactive conversations with Claude through the Anthropic API. It's based on Anthropic's MCP course (https://anthropic.skilljar.com/introduction-to-model-context-protocol).

## Key Commands

### Running the Application
```bash
# With uv (recommended if USE_UV=1 in .env)
uv run main.py

# With standard Python
python main.py

# To run with additional MCP servers
uv run main.py server1.py server2.py
```

### Installation
```bash
# With uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Without uv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install anthropic python-dotenv prompt-toolkit "mcp[cli]==1.8.0"
```

## Architecture

### Core Components

1. **MCP Client/Server Architecture**
   - `mcp_server.py`: Implements MCP server with document management tools
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
USE_UV="0"           # Optional: Set to "1" to use uv for running MCP server
```

### Adding Features

1. **New Documents**: Add to `docs` dictionary in `mcp_server.py`
2. **New MCP Tools**: Implement in `mcp_server.py` following MCP protocol
3. **New Commands**: Add prompts to MCP server's prompt list

### Development Notes

- No linting or type checking currently configured
- Windows requires `asyncio.WindowsProactorEventLoopPolicy()` (handled in main.py:63-64)
- Project uses modern Python packaging with `pyproject.toml`
- Supports Python 3.10+ (per pyproject.toml)