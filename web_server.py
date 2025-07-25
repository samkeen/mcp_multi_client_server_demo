# Web Server for MCP Chat Interface
# This server provides both static file serving and a Claude API proxy
# for the web-based MCP chat interface.

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import MCP client and tool management
from mcp_clients.mcp_client_http import MCPClientHTTP
from core.tools import ToolManager

# Load environment variables
load_dotenv()


class ClaudeAPIProxy:
    """
    Proxy service for Claude API calls.
    
    This proxy handles:
    - CORS restrictions (browsers can't call Anthropic API directly)
    - API key management (keeps keys secure on server-side)
    - Request/response translation between web client and Anthropic API
    """
    
    def __init__(self):
        """Initialize the Claude API proxy with configuration from environment."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
        self.base_url = "https://api.anthropic.com/v1/messages"
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        # Configure HTTP client with proxy settings if available
        proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
        
        # Create HTTP client for making requests to Anthropic API
        client_kwargs = {
            "verify": os.getenv("VERIFY_SSL", "true").lower() != "false",
            "timeout": 60.0
        }
        
        # Add proxy if configured
        if proxy_url:
            client_kwargs["proxy"] = proxy_url
        
        self.client = httpx.AsyncClient(**client_kwargs)
    
    async def forward_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forward a request to the Claude API and return the response.
        
        This method:
        1. Takes a request from the web client
        2. Adds authentication headers
        3. Forwards to Anthropic's API
        4. Returns the response back to the web client
        
        Args:
            request_data: The request payload from the web client
            
        Returns:
            Dict containing the Claude API response
            
        Raises:
            HTTPException: If the API call fails
        """
        try:
            # Prepare headers for Anthropic API
            headers = {
                "x-api-key": self.api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            # Ensure the model is set (use from request or default)
            if "model" not in request_data:
                request_data["model"] = self.model
            
            # Make the request to Anthropic API
            response = await self.client.post(
                self.base_url,
                json=request_data,
                headers=headers
            )
            
            # Handle API errors
            if not response.is_success:
                error_detail = response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Claude API error: {error_detail}"
                )
            
            return response.json()
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Claude API: {str(e)}"
            )
    
    async def cleanup(self):
        """Clean up HTTP client resources."""
        await self.client.aclose()


# Initialize FastAPI app
app = FastAPI(
    title="MCP Web Chat Server",
    description="Web server providing Claude API proxy and static file serving for MCP chat interface",
    version="1.0.0"
)

# Add CORS middleware to allow requests from web browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Claude API proxy
claude_proxy = ClaudeAPIProxy()

# Global MCP clients - will be initialized when needed
mcp_clients: Dict[str, MCPClientHTTP] = {}


async def ensure_mcp_clients_connected():
    """
    Ensure MCP clients are connected to all configured servers with retry logic.
    
    This function initializes HTTP connections to MCP servers if not already connected.
    It includes retry logic with exponential backoff for servers that might be starting up.
    """
    import asyncio
    
    server_configs = {
        "documents": "http://localhost:8001/mcp",
        "calculator": "http://localhost:8002/mcp"
    }
    
    for client_id, base_url in server_configs.items():
        if client_id not in mcp_clients:
            print(f"🔄 Attempting to connect to {client_id} MCP server at {base_url}")
            
            # Retry connection with exponential backoff
            max_retries = 3
            retry_delay = 1.0  # Start with 1 second
            
            for attempt in range(max_retries):
                try:
                    print(f"   Attempt {attempt + 1}/{max_retries} for {client_id}...")
                    
                    # Create and connect HTTP MCP client
                    client = MCPClientHTTP(base_url=base_url, timeout=5.0)
                    await client.connect()
                    mcp_clients[client_id] = client
                    print(f"✅ Connected to {client_id} MCP server at {base_url}")
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    print(f"❌ Attempt {attempt + 1} failed for {client_id}: {e}")
                    
                    if attempt < max_retries - 1:  # Don't wait after last attempt
                        print(f"   Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print(f"❌ All connection attempts failed for {client_id} MCP server")
                        # Don't add failed clients to the dict


@app.post("/claude-proxy")
async def proxy_claude_request(request: Request):
    """
    Proxy endpoint for Claude API requests.
    
    This endpoint receives requests from the web client and forwards them
    to the Claude API, handling authentication and CORS automatically.
    
    The web client sends requests here instead of directly to Anthropic
    to avoid CORS issues and keep API keys secure.
    """
    try:
        # Get the request body from the web client
        request_data = await request.json()
        
        # Forward the request to Claude API via our proxy
        response_data = await claude_proxy.forward_request(request_data)
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list-tools")
async def list_all_tools():
    """
    List all available tools from connected MCP servers.
    
    This endpoint uses the same ToolManager logic as the console client
    to discover and return all available tools in Claude's expected format.
    """
    try:
        print("📋 /list-tools endpoint called")
        
        # Ensure MCP clients are connected
        await ensure_mcp_clients_connected()
        
        if not mcp_clients:
            error_msg = "No MCP servers available - check if servers are running in HTTP mode"
            print(f"❌ {error_msg}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": error_msg,
                    "suggestion": "Try running: uv run main.py --web"
                }
            )
        
        print(f"✅ Connected to {len(mcp_clients)} MCP servers: {list(mcp_clients.keys())}")
        
        # Use existing ToolManager to get all tools
        tools = await ToolManager.get_all_tools(mcp_clients)
        
        tool_names = []
        for t in tools:
            if hasattr(t, 'name'):
                tool_names.append(t.name)
            elif isinstance(t, dict) and 'name' in t:
                tool_names.append(t['name'])
            else:
                tool_names.append('unknown')
        print(f"🛠️  Found {len(tools)} total tools: {tool_names}")
        
        return JSONResponse(content={"tools": tools})
        
    except Exception as e:
        error_msg = f"Failed to list tools: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/call-tool")
async def call_tool_endpoint(request: Request):
    """
    Execute a tool on the appropriate MCP server.
    
    This endpoint uses the same ToolManager logic as the console client
    to find the right server and execute the requested tool.
    
    Expected request format:
    {
        "tool_name": "add",
        "tool_input": {"a": 5, "b": 3},
        "tool_id": "unique_id"
    }
    """
    try:
        # Ensure MCP clients are connected
        await ensure_mcp_clients_connected()
        
        if not mcp_clients:
            return JSONResponse(
                status_code=503,
                content={"error": "No MCP servers available"}
            )
        
        # Get request data
        request_data = await request.json()
        tool_name = request_data.get("tool_name")
        tool_input = request_data.get("tool_input", {})
        tool_id = request_data.get("tool_id", "unknown")
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="tool_name is required")
        
        # Create a mock message in the format expected by ToolManager
        from anthropic.types import Message, ToolUseBlock, Usage
        
        tool_use_block = ToolUseBlock(
            type="tool_use",
            id=tool_id,
            name=tool_name,
            input=tool_input
        )
        
        mock_message = Message(
            id="web-request",
            role="assistant",
            type="message",
            content=[tool_use_block],
            model="claude-3-sonnet-20240229",
            stop_reason="tool_use",
            stop_sequence=None,
            usage=Usage(input_tokens=0, output_tokens=0)
        )
        
        # Execute the tool using existing ToolManager
        tool_results = await ToolManager.execute_tool_requests(mcp_clients, mock_message)
        
        if tool_results:
            result = tool_results[0]  # Get the first (and only) result
            return JSONResponse(content={
                "success": not result.get("is_error", False),
                "content": result.get("content", ""),
                "tool_use_id": result.get("tool_use_id", tool_id)
            })
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "No result returned from tool execution"}
            )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to execute tool: {str(e)}"}
        )


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "MCP Web Chat Server"}


@app.get("/health-mcp") 
async def health_check_mcp():
    """
    Health check endpoint specifically for MCP server connectivity.
    
    This endpoint attempts to connect to all MCP servers and reports their status.
    Useful for debugging connection issues.
    """
    server_configs = {
        "documents": "http://localhost:8001/mcp",
        "calculator": "http://localhost:8002/mcp"
    }
    
    server_status = {}
    overall_healthy = True
    
    for client_id, base_url in server_configs.items():
        try:
            # Try to create a test connection (don't store it)
            test_client = MCPClientHTTP(base_url=base_url, timeout=3.0)
            await test_client.connect()
            
            # Try to list tools to verify full functionality
            tools = await test_client.list_tools()
            
            # Clean up test connection
            await test_client.cleanup()
            
            server_status[client_id] = {
                "status": "healthy",
                "url": base_url,
                "tools_count": len(tools),
                "tools": [tool.name for tool in tools]
            }
            
        except Exception as e:
            overall_healthy = False
            server_status[client_id] = {
                "status": "unhealthy", 
                "url": base_url,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    return {
        "overall_status": "healthy" if overall_healthy else "degraded",
        "servers": server_status,
        "connected_count": len([s for s in server_status.values() if s["status"] == "healthy"]),
        "total_count": len(server_configs)
    }


@app.get("/config")
async def get_config():
    """
    Provide configuration information to the web client.
    
    This allows the frontend to know what MCP servers are available.
    Note: The frontend now uses proxy endpoints instead of connecting directly.
    """
    return {
        "mcp_servers": {
            "documents": "http://localhost:8001/mcp",
            "calculator": "http://localhost:8002/mcp"
        },
        "claude_model": claude_proxy.model,
        "proxy_endpoints": {
            "list_tools": "/list-tools",
            "call_tool": "/call-tool"
        }
    }


# Mount static files (HTML, CSS, JS) for the web interface
# This serves the actual web chat interface files
static_path = Path(__file__).parent / "web"
if static_path.exists():
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
else:
    @app.get("/")
    async def root():
        """Fallback root endpoint if web directory doesn't exist yet."""
        return HTMLResponse("""
        <html>
            <head><title>MCP Web Chat - Setup Required</title></head>
            <body>
                <h1>MCP Web Chat Server</h1>
                <p>The web interface files are not yet created.</p>
                <p>Please run the setup to create the web/ directory with the chat interface.</p>
                <ul>
                    <li>Health Check: <a href="/health">/health</a></li>
                    <li>Configuration: <a href="/config">/config</a></li>
                    <li>Claude API Proxy: POST to /claude-proxy</li>
                </ul>
            </body>
        </html>
        """)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the server shuts down."""
    await claude_proxy.cleanup()
    
    # Clean up MCP clients
    for client_id, client in mcp_clients.items():
        try:
            await client.cleanup()
            print(f"✅ Cleaned up {client_id} MCP client")
        except Exception as e:
            print(f"❌ Error cleaning up {client_id} MCP client: {e}")
    
    mcp_clients.clear()


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """
    Start the web server.
    
    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8000)
    """
    print(f"🌐 Starting MCP Web Chat Server...")
    print(f"   Server URL: http://{host}:{port}")
    print(f"   Health Check: http://{host}:{port}/health")
    print(f"   Claude API Proxy: http://{host}:{port}/claude-proxy")
    print(f"   Configuration: http://{host}:{port}/config")
    
    # Start the server with uvicorn
    uvicorn.run(
        "web_server:app",
        host=host,
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    )


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY environment variable is required")
        print("   Please set it in your .env file")
        exit(1)
    
    # Start the server
    start_server()