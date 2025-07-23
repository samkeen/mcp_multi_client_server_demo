# Multi-Server Usage Example
# This demonstrates how to use multiple MCP servers together

## Available Servers

The application supports flexible MCP server loading:

### Auto-Discovery Mode (Default)
When no servers are specified, all `*mcp_server.py` files in `mcp_servers/` are loaded automatically:

```bash
# Auto-discover and load all available servers
uv run main.py
```

Currently available servers:
1. **Documents Server** - Manage and manipulate documents
2. **Calculator Server** - Perform mathematical calculations

### Manual Server Selection
Specify only the servers you want to use:

```bash
# Load only calculator server
uv run main.py mcp_servers/calculator_mcp_server.py

# Load only documents server  
uv run main.py mcp_servers/documents_mcp_server.py

# Load multiple specific servers
uv run main.py mcp_servers/calculator_mcp_server.py mcp_servers/weather_mcp_server.py
```

## Server Loading Information

The application will display which servers are being loaded:

**Auto-discovery example:**
```
🔍 Auto-discovering MCP servers: mcp_servers/*mcp_server.py
🚀 Loading 2 MCP server(s):
   1. Documents (mcp_servers/documents_mcp_server.py)
   2. Calculator (mcp_servers/calculator_mcp_server.py)
```

**Manual selection example:**
```
📋 Using specified MCP servers
🚀 Loading 1 MCP server(s):
   1. Calculator (mcp_servers/calculator_mcp_server.py)
```

### Server Compatibility

- **Any server combination works**: You can load any combination of servers
- **Document features**: Document-specific features (@mentions, /format commands) are only available when the documents server is loaded
- **Graceful feature availability**: Features dynamically enable/disable based on loaded servers

### Feature Availability by Server

**Documents Server Loaded:**
- ✅ @ mentions: `@report.pdf` fetches document content
- ✅ / commands: `/format document.pdf` executes document prompts
- ✅ Document management tools

**Calculator Server Loaded:**  
- ✅ Mathematical calculations: "what is 2+2?"
- ✅ Complex expressions: "calculate 2^3 + sqrt(16)"

**No Documents Server:**
- ❌ @ mentions will be ignored (no document content fetched)
- ❌ / commands will be treated as regular chat messages
- ✅ All other features work normally

### Example Conversations

**Basic Math:**
```
> Can you calculate 25 + 17?
Claude will use the `add` tool: 25 + 17 = 42
```

**Complex Expressions:**
```
> What is the result of 2 + 3 * 4?
Claude will use the `calculate_expression` tool: 2 + 3 * 4 = 14
```

**Document + Math:**
```
> Read @report.pdf and calculate the square root of any numbers you find
Claude will:
1. Use document tools to read the report
2. Use calculator tools for any math operations
3. Combine both results in the response
```

**Document Analysis:**
```
> Create a summary of @financials.docx and calculate the total if there are multiple amounts
Claude can combine document reading with mathematical operations
```

## Tool Composition

The real power comes from Claude being able to use tools from multiple servers in a single response:

1. **Read document content** using document server tools
2. **Perform calculations** using calculator server tools  
3. **Edit documents** with calculated results
4. **Format outputs** using document formatting tools

This demonstrates the MCP architecture's strength in composable, modular functionality.

## Testing Your Setup

Run the test script to verify everything works:
```bash
uv run test_calculator.py
```

This confirms that:
- ✅ Calculator server starts correctly
- ✅ All mathematical tools are available
- ✅ Operations return correct results
- ✅ Resources are accessible
