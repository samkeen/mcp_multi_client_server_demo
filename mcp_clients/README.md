# MCP Clients

This directory contains MCP (Model Context Protocol) client implementations that connect to and communicate with MCP servers.

## Current Clients

### mcp_client_console.py
The default console/CLI MCP client implementation that provides:
- **stdio Transport**: Communication via stdin/stdout with server processes
- **Session Management**: Handles MCP protocol handshake and lifecycle
- **Tool Calls**: Execute tools on connected MCP servers
- **Resource Access**: Read resources using URI patterns
- **Prompt Management**: Fetch and execute prompt templates
- **Context Manager Support**: Automatic cleanup with `async with` syntax

### mcp_client_http.py
The web-based HTTP MCP client implementation that provides:
- **HTTP Transport**: Communication via Streamable HTTP with remote servers
- **Remote Connections**: Connect to MCP servers running as HTTP services
- **Same Interface**: Drop-in replacement for console client with identical methods
- **Network Resilience**: Handles timeouts, retries, and connection management
- **Web Integration**: Designed for web applications and remote deployments
- **Future-Proof**: Suitable for production deployments and cloud environments

## Client Architecture

Each MCP client handles:
1. **Transport Layer**: How to communicate with servers (stdio, HTTP, WebSocket, etc.)
2. **Protocol Management**: MCP handshake, session lifecycle, message routing
3. **Type Conversion**: Convert between Python objects and MCP protocol types
4. **Error Handling**: Connection errors, timeouts, protocol violations
5. **Resource Cleanup**: Proper shutdown of connections and processes

## Adding New Client Types

To add a new MCP client implementation:

1. Create a new Python file in this directory (e.g., `mcp_client_http.py`)
2. Follow the pattern from `mcp_client_console.py`:
   - Implement async context manager (`__aenter__`, `__aexit__`)
   - Provide standard interface methods: `list_tools()`, `call_tool()`, `list_prompts()`, etc.
   - Handle transport-specific connection logic
   - Ensure proper resource cleanup
3. Update imports in consuming modules as needed

## Client Structure

Each MCP client should follow this basic interface:

```python
class MCPClient:
    def __init__(self, ...): # Transport-specific parameters
        pass
    
    async def connect(self): # Establish connection
        pass
    
    async def list_tools(self) -> list[types.Tool]:
        pass
    
    async def call_tool(self, tool_name: str, tool_input) -> types.CallToolResult:
        pass
    
    async def list_prompts(self) -> list[types.Prompt]:
        pass
    
    async def get_prompt(self, prompt_name: str, args: dict) -> list[types.PromptMessage]:
        pass
    
    async def read_resource(self, uri: str) -> Any:
        pass
    
    async def cleanup(self):
        pass
    
    # Context manager support
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
```

## Examples of Client Types

Consider creating clients for:
- **HTTP Client**: Connect to MCP servers over HTTP/REST APIs
- **WebSocket Client**: Real-time bidirectional communication
- **TCP Client**: Raw TCP socket communication
- **Message Queue Client**: Connect via Redis, RabbitMQ, etc.
- **Local Process Client**: Enhanced stdio with process monitoring
- **Remote SSH Client**: Connect to MCP servers on remote machines
- **Mock Client**: Testing and development client with simulated responses

## Transport Considerations

Different transports have different characteristics:

| Transport | Use Case | Pros | Cons |
|-----------|----------|------|------|
| stdio | Local processes | Simple, direct | Limited to local |
| HTTP | Web services | Scalable, cacheable | Request/response only |
| WebSocket | Real-time apps | Bidirectional, low latency | More complex |
| TCP | High performance | Fast, reliable | Lower level |
| SSH | Remote servers | Secure, authenticated | Network dependent |

## Transport Comparison

| Feature | Console Client (stdio) | HTTP Client (streamable-http) |
|---------|----------------------|------------------------------|
| **Use Case** | Local development, CLI apps | Web apps, remote deployments |
| **Connection** | Spawns subprocesses | Connects to HTTP endpoints |
| **Performance** | Very fast (local) | Network dependent |
| **Scalability** | Limited to local machine | Highly scalable |
| **Complexity** | Simple | Slightly more complex |
| **Security** | Process isolation | Network security needed |
| **Debugging** | Process logs | HTTP request/response logs |

## Current Usage

Both clients are used throughout the application:
- **Console Mode**: `main.py` uses `MCPClient` for stdio transport
- **Web Mode**: `main.py --web` uses `MCPClientHTTP` for HTTP transport
- **Testing**: `test_calculator.py` uses console client for local testing
- **Core Modules**: Both clients work with existing `core/` modules

All clients maintain the same interface to ensure compatibility across the application.
