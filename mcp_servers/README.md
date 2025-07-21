# MCP Servers

This directory contains MCP (Model Context Protocol) servers that provide various tools, resources, and prompts for Claude to use.

## Current Servers

### documents_mcp_server.py
The default document management server that provides:
- **Tools**: Read and edit documents
- **Resources**: List and fetch document contents
- **Prompts**: Format documents in markdown

## Adding New Servers

To add a new MCP server:

1. Create a new Python file in this directory (e.g., `calculator_mcp_server.py`)
2. Follow the pattern from `documents_mcp_server.py`:
   - Import `FastMCP` from `mcp.server.fastmcp`
   - Initialize the server with a descriptive name
   - Define tools, resources, and prompts using decorators
   - Add the `if __name__ == "__main__":` block to run via stdio
3. Pass the server file path as an argument when running main.py:
   ```bash
   uv run main.py mcp_servers/calculator_mcp_server.py
   ```

## Server Structure

Each MCP server should follow this basic structure:

```python
from mcp.server.fastmcp import FastMCP

# Initialize server
mcp = FastMCP("ServerName", log_level="ERROR")

# Define tools with @mcp.tool()
# Define resources with @mcp.resource()
# Define prompts with @mcp.prompt()

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Examples of Server Types

Consider creating servers for:
- **Calculator**: Mathematical operations and computations
- **Weather**: Weather data and forecasts
- **File System**: File operations and management
- **Database**: Data storage and retrieval
- **API Integration**: External service connections
- **Code Generation**: Programming assistance tools
