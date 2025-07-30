# Tool Management Module - MCP Tool Execution
# This module manages tool discovery and execution across multiple MCP clients,
# providing a unified interface for Claude to use tools from any connected server.

import json
import sys
from typing import Optional, Literal, List
from mcp.types import CallToolResult, Tool, TextContent
from mcp_clients.mcp_client_console import MCPClient
# Support both console and HTTP clients
try:
    from mcp_clients.mcp_client_http import MCPClientHTTP
    MCPClientType = MCPClient | MCPClientHTTP
except ImportError:
    MCPClientType = MCPClient
from anthropic.types import Message, ToolResultBlockParam


class ToolManager:
    """
    Manages tool discovery and execution across multiple MCP clients.
    
    This class provides a unified interface for:
    - Collecting tools from all connected MCP servers
    - Finding which server provides a specific tool
    - Executing tools and formatting results for Claude
    
    All methods are class methods since this is a stateless utility class.
    """
    
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClientType]) -> list[Tool]:
        """
        Collect all available tools from all connected MCP clients.
        
        This method queries each MCP server for its available tools
        and combines them into a single list that Claude can use.
        
        Args:
            clients: Dictionary of MCP client instances
            
        Returns:
            List of tool definitions in Claude's expected format
        """
        tools = []
        for client_name, client in clients.items():
            # Get tools from this MCP server
            tool_models = await client.list_tools()
            print(f"Tools from {client_name}: {[t.name for t in tool_models]}", file=sys.stderr)
            # Convert MCP tool format to Claude's expected format
            tools += [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,  # JSON schema for parameters
                }
                for t in tool_models
            ]
        print(f"Total tools available: {len(tools)}", file=sys.stderr)
        return tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClientType], tool_name: str
    ) -> Optional[MCPClientType]:
        """
        Find which MCP client provides a specific tool.
        
        When Claude wants to use a tool, we need to find which MCP server
        actually implements that tool so we can route the request correctly.
        
        Args:
            clients: List of MCP client instances to search
            tool_name: Name of the tool to find
            
        Returns:
            The MCP client that provides the tool, or None if not found
        """
        for client in clients:
            # Query this client for its available tools
            tools = await client.list_tools()
            # Check if this client has the tool we're looking for
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                return client
        return None

    @classmethod
    def _build_tool_result_part(
        cls,
        tool_use_id: str,
        text: str,
        status: Literal["success"] | Literal["error"],
    ) -> ToolResultBlockParam:
        """
        Build a tool result block for Claude.
        
        Claude expects tool results in a specific format with:
        - The ID of the tool use request
        - The result content
        - Whether it was an error
        
        Args:
            tool_use_id: ID from Claude's tool use request
            text: The result content
            status: Whether the execution succeeded or failed
            
        Returns:
            Formatted tool result block for Claude
        """
        return {
            "tool_use_id": tool_use_id,
            "type": "tool_result",
            "content": text,
            "is_error": status == "error",
        }

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClientType], message: Message
    ) -> List[ToolResultBlockParam]:
        """
        Execute all tool requests from Claude's message.
        
        When Claude wants to use tools, it sends a message containing
        one or more tool_use blocks. This method:
        1. Extracts each tool request
        2. Finds the right MCP server for each tool
        3. Executes the tool
        4. Formats the results for Claude
        
        Args:
            clients: Dictionary of available MCP clients
            message: Claude's message containing tool use requests
            
        Returns:
            List of formatted tool results to send back to Claude
        """
        # Extract all tool_use blocks from Claude's message
        tool_requests = [
            block for block in message.content if block.type == "tool_use"
        ]
        tool_result_blocks: list[ToolResultBlockParam] = []
        # Process each tool request individually
        for tool_request in tool_requests:
            tool_use_id = tool_request.id  # Claude's ID for this request
            tool_name = tool_request.name  # Name of the tool to call
            tool_input = tool_request.input  # Parameters for the tool

            # Find which MCP client provides this tool
            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            # Handle case where tool is not found
            if not client:
                tool_result_part = cls._build_tool_result_part(
                    tool_use_id, "Could not find that tool", "error"
                )
                tool_result_blocks.append(tool_result_part)
                continue  # Skip to next tool request

            # Execute the tool on the appropriate MCP server
            try:
                # Call the tool with the provided parameters
                tool_output: CallToolResult | None = await client.call_tool(
                    tool_name, tool_input
                )
                
                # Extract text content from the tool result
                items = []
                if tool_output:
                    items = tool_output.content
                # Filter for text content blocks and extract the text
                content_list = [
                    item.text for item in items if isinstance(item, TextContent)
                ]
                
                # Format content based on number of items to avoid unnecessary array wrapping
                if len(content_list) == 1:
                    # Single result - return the text directly (more natural format)
                    content_result = content_list[0]
                elif len(content_list) == 0:
                    # No content - return empty string
                    content_result = ""
                else:
                    # Multiple results - use JSON array format
                    content_result = json.dumps(content_list)
                
                # Build the result block with success/error status
                tool_result_part = cls._build_tool_result_part(
                    tool_use_id,
                    content_result,
                    "error"
                    if tool_output and tool_output.isError
                    else "success",
                )
            except Exception as e:
                # Handle any errors during tool execution
                error_message = f"Error executing tool '{tool_name}': {e}"
                print(error_message)  # Log the error for debugging
                tool_result_part = cls._build_tool_result_part(
                    tool_use_id,
                    json.dumps({"error": error_message}),
                    "error",  # Always mark exceptions as errors
                )

            # Add this tool result to the collection
            tool_result_blocks.append(tool_result_part)
            
        # Return all tool results to be sent back to Claude
        return tool_result_blocks
