# MCP Console Client Implementation - stdio Transport
# This client connects to MCP servers via stdio (stdin/stdout) transport,
# which is ideal for local server processes spawned as subprocesses.

import sys
import asyncio
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

import json
from pydantic import AnyUrl


class MCPClient:
    """
    A console-based MCP client that connects to servers via stdio transport.
    
    This client implementation:
    - Spawns MCP servers as local subprocesses
    - Communicates via stdin/stdout (stdio transport)
    - Manages the full lifecycle of server processes
    - Provides a Python interface to MCP protocol operations
    
    Use this client for:
    - Local MCP servers (like our documents and calculator servers)
    - Development and testing
    - CLI applications that need direct server control
    """
    
    def __init__(
        self,
        command: str,  # Command to run the server (e.g., "python", "uv")
        args: list[str],  # Arguments for the command (e.g., ["run", "server.py"])
        env: Optional[dict] = None,  # Optional environment variables
    ):
        self._command = command
        self._args = args
        self._env = env
        self._session: Optional[ClientSession] = None
        # AsyncExitStack manages cleanup of async resources
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        """
        Establishes connection to the MCP server.
        
        This method:
        1. Spawns the server process as a subprocess
        2. Sets up stdio communication channels
        3. Initializes the MCP session
        """
        # Configure how to start the server process
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )
        
        # Create stdio transport - this spawns the server process
        # and sets up communication via stdin/stdout
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        _stdio, _write = stdio_transport
        
        # Create the MCP session that handles protocol communication
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write)
        )
        
        # Initialize the session - this performs the MCP handshake
        await self._session.initialize()

    def session(self) -> ClientSession:
        """Get the active MCP session, raising an error if not connected."""
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized or cache not populated. Call connect_to_server first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        """List all tools available from the connected MCP server."""
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(
        self, tool_name: str, tool_input
    ) -> types.CallToolResult | None:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call (e.g., "read_doc_contents")
            tool_input: Parameters for the tool (e.g., {"doc_id": "report.pdf"})
        """
        return await self.session().call_tool(tool_name, tool_input)

    async def list_prompts(self) -> list[types.Prompt]:
        """List all prompts (pre-defined templates) available from the server."""
        result = await self.session().list_prompts()
        return result.prompts

    async def get_prompt(self, prompt_name, args: dict[str, str]):
        """
        Get a specific prompt with arguments filled in.
        
        Args:
            prompt_name: Name of the prompt (e.g., "format")
            args: Arguments to fill into the prompt template
        """
        result = await self.session().get_prompt(prompt_name, args)
        return result.messages

    async def read_resource(self, uri: str) -> Any:
        """
        Read a resource from the MCP server.
        
        Resources are accessed via URIs like "docs://documents/report.pdf"
        This method handles parsing based on MIME type.
        """
        result = await self.session().read_resource(AnyUrl(uri))
        resource = result.contents[0]

        # Handle different content types
        if isinstance(resource, types.TextResourceContents):
            # Parse JSON resources into Python objects
            if resource.mimeType == "application/json":
                return json.loads(resource.text)
            # Return plain text as-is
            return resource.text

    async def cleanup(self):
        """Clean up resources and terminate the server process."""
        await self._exit_stack.aclose()
        self._session = None

    # Context manager support - allows using 'async with MCPClient(...) as client:'
    # This ensures proper cleanup even if an error occurs
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# Example usage for testing the console client
async def main():
    # Using async with ensures the client is properly cleaned up
    async with MCPClient(
        # Console client spawns servers as subprocesses using command/args
        command="uv",
        args=["run", "mcp_servers/documents_mcp_server.py"],
    ) as _client:
        # In a real application, you would interact with the client here:
        # tools = await _client.list_tools()
        # result = await _client.call_tool("read_doc_contents", {"doc_id": "report.pdf"})
        pass


if __name__ == "__main__":
    # Windows subprocess support requires ProactorEventLoop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
