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

# Configure proxy settings if provided
def configure_proxy():
    """Configure proxy settings from environment variables"""
    http_proxy = os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("HTTPS_PROXY") 
    no_proxy = os.getenv("NO_PROXY")
    verify_ssl = os.getenv("VERIFY_SSL", "true")
    
    if http_proxy or https_proxy:
        print(f"🌐 Configuring proxy settings...")
        if http_proxy:
            os.environ["HTTP_PROXY"] = http_proxy
            print(f"   HTTP_PROXY: {http_proxy}")
        if https_proxy:
            os.environ["HTTPS_PROXY"] = https_proxy
            print(f"   HTTPS_PROXY: {https_proxy}")
        if no_proxy:
            os.environ["NO_PROXY"] = no_proxy
            print(f"   NO_PROXY: {no_proxy}")
        print(f"   SSL_VERIFY: {verify_ssl}")
    else:
        print("🌐 No proxy configuration found")

# Configure proxy before any network operations
configure_proxy()

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
    # Example: uv run main.py mcp_servers/calculator_mcp_server.py mcp_servers/weather_mcp_server.py
    server_scripts = sys.argv[1:]
    clients = {}

    # Use uv to run the default documents MCP server
    command, args = ("uv", ["run", "mcp_servers/documents_mcp_server.py"])

    # AsyncExitStack manages multiple async contexts (MCP clients)
    # It ensures all clients are properly closed when the program exits
    async with AsyncExitStack() as stack:
        # Initialize the default document MCP server
        # This server provides access to documents and related commands
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
