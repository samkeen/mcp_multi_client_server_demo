import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.claude import Claude

from core.cli_chat import CliChat
from core.cli import CliApp

# Load environment variables from .env file
load_dotenv()

# Anthropic Configuration
# These environment variables are required for Claude API access
claude_model = os.getenv("CLAUDE_MODEL", "")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")


# Validate required environment variables
assert claude_model, "Error: CLAUDE_MODEL cannot be empty. Update .env"
assert anthropic_api_key, (
    "Error: ANTHROPIC_API_KEY cannot be empty. Update .env"
)


# Main async function - this is the entry point for our async application
# Using async allows multiple MCP servers to run concurrently without blocking
async def main():
    # Initialize the Claude API service
    claude_service = Claude(model=claude_model)

    # Get any additional MCP server scripts from command line arguments
    # Example: python main.py calculator.py weather.py
    server_scripts = sys.argv[1:]
    clients = {}

    # Determine the command to run the default MCP server
    # USE_UV environment variable allows switching between uv and python
    command, args = (
        ("uv", ["run", "mcp_server.py"])
        if os.getenv("USE_UV", "0") == "1"
        else ("python", ["mcp_server.py"])
    )

    # AsyncExitStack manages multiple async contexts (MCP clients)
    # It ensures all clients are properly closed when the program exits
    async with AsyncExitStack() as stack:
        # Initialize the default document MCP server
        # This server provides access to documents and commands
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)
        )
        clients["doc_client"] = doc_client

        # Initialize any additional MCP servers passed as command line arguments
        # Each server runs in its own process and can provide different tools
        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            # await ensures the client is fully initialized before continuing
            client = await stack.enter_async_context(
                MCPClient(command="uv", args=["run", server_script])
            )
            clients[client_id] = client

        # Create the chat interface that coordinates between:
        # - The Claude API service
        # - The document MCP client
        # - Any additional MCP clients
        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            claude_service=claude_service,
        )

        # Initialize and run the CLI application
        cli = CliApp(chat)
        await cli.initialize()  # Sets up completions and UI
        await cli.run()  # Starts the interactive prompt loop


if __name__ == "__main__":
    # Windows requires a specific event loop policy for subprocess support
    # This is needed for MCP servers which run as subprocesses
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # asyncio.run() is the standard way to run async programs in Python 3.7+
    # It creates an event loop, runs the async function, and cleans up
    asyncio.run(main())
