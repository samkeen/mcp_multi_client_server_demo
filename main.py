import asyncio
import sys
import os
import glob
from pathlib import Path
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_clients.mcp_client_console import MCPClient
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

    # Get any MCP server scripts from command line arguments or auto-discover
    server_scripts = sys.argv[1:]
    
    # If no servers specified, auto-discover all *mcp_server.py files in mcp_servers/
    if not server_scripts:
        mcp_servers_pattern = "mcp_servers/*mcp_server.py"
        server_scripts = glob.glob(mcp_servers_pattern)
        print(f"🔍 Auto-discovering MCP servers: {mcp_servers_pattern}")
    else:
        print(f"📋 Using specified MCP servers")
    
    # Display loaded servers
    if server_scripts:
        print(f"🚀 Loading {len(server_scripts)} MCP server(s):")
        for i, script in enumerate(server_scripts, 1):
            server_name = Path(script).stem.replace('_mcp_server', '').replace('_', ' ').title()
            print(f"   {i}. {server_name} ({script})")
    else:
        print("⚠️  No MCP servers found or specified")
        return

    clients = {}

    # AsyncExitStack manages multiple async contexts (MCP clients)
    # It ensures all clients are properly closed when the program exits
    async with AsyncExitStack() as stack:
        # Initialize all MCP servers
        # Each server runs in its own process and can provide different tools
        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{Path(server_script).stem}"
            # Use uv to run each MCP server
            command, args = ("uv", ["run", server_script])
            # await ensures the client is fully initialized before continuing
            client = await stack.enter_async_context(
                MCPClient(command=command, args=args)
            )
            clients[client_id] = client

        # Ensure we have at least one client
        if not clients:
            print("❌ Error: No MCP servers could be initialized")
            return

        # Create the chat interface that coordinates between:
        # - The Claude API service  
        # - All available MCP clients
        chat = CliChat(
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
