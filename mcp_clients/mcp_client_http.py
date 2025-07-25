# MCP HTTP Client Implementation - Streamable HTTP Transport
# This client connects to MCP servers via HTTP transport (REST API),
# which is ideal for web applications and remote server deployments.

import asyncio
import logging
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client
import json
from pydantic import AnyUrl

# Set up logging for debugging
logger = logging.getLogger(__name__)
# Note: Don't override global logging config - use logging.basicConfig() in main.py instead


class MCPClientHTTP:
    """
    A web-based MCP client that connects to servers via HTTP transport.
    
    This client implementation:
    - Connects to MCP servers running as HTTP services
    - Communicates via HTTP REST API (streamable HTTP transport)
    - Designed for web applications and remote server deployments
    - Provides the same Python interface as the console client
    
    Use this client for:
    - Web applications (like our web chat interface)
    - Remote MCP servers running on different machines
    - Production deployments where servers run as services
    - Scenarios where stdio transport isn't suitable
    """
    
    def __init__(
        self,
        base_url: str,  # Base URL of the MCP server (e.g., "http://localhost:8001")
        timeout: Optional[float] = 30.0,  # Request timeout in seconds
        headers: Optional[dict] = None,  # Optional HTTP headers
    ):
        """
        Initialize the HTTP MCP client.
        
        Args:
            base_url: The base URL where the MCP server is running
            timeout: Request timeout in seconds (default: 30)
            headers: Optional additional HTTP headers to send with requests
        """
        self._base_url = base_url.rstrip('/')  # Remove trailing slash
        self._timeout = timeout
        self._headers = headers or {}
        self._session: Optional[ClientSession] = None
        # AsyncExitStack manages cleanup of async resources
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        """
        Establishes connection to the MCP server via HTTP.
        
        This method:
        1. Creates an HTTP client connection to the server
        2. Sets up the MCP session for protocol communication
        3. Initializes the session with a handshake
        """
        logger.debug(f"🔄 Starting HTTP connection to {self._base_url}")
        
        try:
            # Create HTTP transport - this connects to the remote MCP server
            # The streamablehttp_client handles HTTP requests/responses
            from datetime import timedelta
            logger.debug(f"   Creating streamablehttp_client with timeout={self._timeout}s")
            
            http_transport = await self._exit_stack.enter_async_context(
                streamablehttp_client(
                    url=self._base_url,
                    headers=self._headers,
                    timeout=timedelta(seconds=self._timeout)
                )
            )
            read_stream, write_stream, get_session_id = http_transport
            logger.debug("   ✅ HTTP transport created successfully")
            
            # Create the MCP session that handles protocol communication
            # This is the same session type used by the console client
            logger.debug("   Creating MCP ClientSession...")
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            logger.debug("   ✅ ClientSession created successfully")
            
            # Initialize the session - this performs the MCP handshake
            # The server and client exchange capabilities and establish the session
            logger.debug("   Performing MCP handshake...")
            await self._session.initialize()
            logger.debug(f"   ✅ MCP handshake completed for {self._base_url}")
            
        except Exception as e:
            logger.error(f"   ❌ Connection failed to {self._base_url}: {type(e).__name__}: {e}")
            raise

    def session(self) -> ClientSession:
        """
        Get the active MCP session, raising an error if not connected.
        
        Returns:
            ClientSession: The active MCP session
            
        Raises:
            ConnectionError: If the client is not connected to a server
        """
        if self._session is None:
            raise ConnectionError(
                "HTTP client session not initialized. Call connect() first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        """
        List all tools available from the connected MCP server.
        
        Tools are functions that can be called to perform specific tasks,
        like reading documents, performing calculations, etc.
        
        Returns:
            list[types.Tool]: List of available tools with their schemas
        """
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult | None:
        """
        Call a tool on the MCP server.
        
        This sends a tool execution request to the server and returns the result.
        The server will execute the tool with the provided parameters.
        
        Args:
            tool_name: Name of the tool to call (e.g., "read_doc_contents")
            tool_input: Parameters for the tool (e.g., {"doc_id": "report.pdf"})
            
        Returns:
            CallToolResult: The result of the tool execution, or None if failed
        """
        return await self.session().call_tool(tool_name, tool_input)

    async def list_prompts(self) -> list[types.Prompt]:
        """
        List all prompts (pre-defined templates) available from the server.
        
        Prompts are reusable message templates that can be filled with parameters.
        They're useful for consistent messaging patterns.
        
        Returns:
            list[types.Prompt]: List of available prompt templates
        """
        result = await self.session().list_prompts()
        return result.prompts

    async def get_prompt(self, prompt_name: str, args: dict[str, str]):
        """
        Get a specific prompt with arguments filled in.
        
        This retrieves a prompt template and fills it with the provided arguments
        to create concrete messages ready for use.
        
        Args:
            prompt_name: Name of the prompt template (e.g., "format")
            args: Arguments to fill into the prompt template
            
        Returns:
            list[PromptMessage]: The rendered prompt messages
        """
        result = await self.session().get_prompt(prompt_name, args)
        return result.messages

    async def read_resource(self, uri: str) -> Any:
        """
        Read a resource from the MCP server.
        
        Resources are data that can be accessed via URIs. The server
        determines what resources are available and how to retrieve them.
        
        Args:
            uri: URI of the resource (e.g., "docs://documents/report.pdf")
            
        Returns:
            Any: The resource content, parsed based on MIME type
        """
        result = await self.session().read_resource(AnyUrl(uri))
        resource = result.contents[0]

        # Handle different content types returned by the server
        if isinstance(resource, types.TextResourceContents):
            # Parse JSON resources into Python objects for easier handling
            if resource.mimeType == "application/json":
                return json.loads(resource.text)
            # Return plain text as-is
            return resource.text

    async def cleanup(self):
        """
        Clean up resources and close the HTTP connection.
        
        This method should always be called when finished with the client
        to ensure proper cleanup of network resources.
        """
        await self._exit_stack.aclose()
        self._session = None

    # Context manager support - allows using 'async with MCPClientHTTP(...) as client:'
    # This ensures proper cleanup even if an error occurs
    async def __aenter__(self):
        """Enter the async context manager - establishes connection."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager - cleans up resources."""
        await self.cleanup()


# Example usage for testing the HTTP client
async def main():
    """
    Example demonstrating how to use the HTTP MCP client.
    
    This assumes you have an MCP server running on http://localhost:8001
    You can start one with: uv run mcp_servers/calculator_mcp_server.py http
    """
    # Using async with ensures the client is properly cleaned up
    async with MCPClientHTTP(
        # HTTP client connects to servers via URL instead of spawning processes
        base_url="http://localhost:8001",
        timeout=30.0,
        headers={"User-Agent": "MCP-Learning-Demo/1.0"}
    ) as client:
        # Example: List available tools from the server
        print("Available tools:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Example: Call a tool (if calculator server is running)
        if tools and any(tool.name == "add" for tool in tools):
            result = await client.call_tool("add", {"a": 5, "b": 3})
            print(f"Calculator result: {result}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())