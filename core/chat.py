# Base Chat Module - Core Conversation Logic
# This module provides the foundation for chat functionality,
# handling the conversation loop between user, Claude, and MCP tools.

from core.claude import Claude
from mcp_client import MCPClient
from core.tools import ToolManager
from anthropic.types import MessageParam


class Chat:
    """
    Base chat class that manages conversations between user, Claude, and tools.
    
    This class implements the core chat loop:
    1. Process user query
    2. Send to Claude with available tools
    3. If Claude wants to use tools, execute them and continue
    4. Return final response to user
    
    Subclasses can override _process_query to add specific functionality
    like handling commands or resource mentions.
    """
    
    def __init__(self, claude_service: Claude, clients: dict[str, MCPClient]):
        self.claude_service: Claude = claude_service  # API wrapper for Claude
        self.clients: dict[str, MCPClient] = clients  # All available MCP clients
        self.messages: list[MessageParam] = []  # Conversation history

    async def _process_query(self, query: str):
        """
        Process a user query and add it to the conversation.
        
        The base implementation simply adds the query as a user message.
        Subclasses can override this to handle special syntax like
        commands (/) or resource mentions (@).
        """
        self.messages.append({"role": "user", "content": query})

    async def run(
        self,
        query: str,
    ) -> str:
        """
        Execute a complete chat interaction.
        
        This method implements the core chat loop:
        1. Process the user's query
        2. Send to Claude with tool access
        3. Handle any tool calls Claude makes
        4. Return the final response
        
        Returns:
            The final text response from Claude
        """
        final_text_response = ""

        # First, process the user's query (may be overridden by subclasses)
        await self._process_query(query)

        # Main conversation loop - continues until Claude gives a final answer
        while True:
            # Send current conversation to Claude with all available tools
            response = self.claude_service.chat(
                messages=self.messages,
                tools=await ToolManager.get_all_tools(self.clients),
            )

            # Add Claude's response to the conversation history
            self.claude_service.add_assistant_message(self.messages, response)

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Print Claude's reasoning before tool execution
                print(self.claude_service.text_from_message(response))
                
                # Execute the tools Claude requested
                tool_result_parts = await ToolManager.execute_tool_requests(
                    self.clients, response
                )

                # Add tool results back to conversation as user message
                # This lets Claude see the tool outputs and continue reasoning
                self.claude_service.add_user_message(
                    self.messages, tool_result_parts
                )
                # Loop continues - Claude will process tool results
            else:
                # Claude finished without needing tools - extract final response
                final_text_response = self.claude_service.text_from_message(
                    response
                )
                break  # Exit the conversation loop

        return final_text_response
