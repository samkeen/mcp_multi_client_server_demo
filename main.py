import asyncio
import sys
import os
import glob
import logging
from pathlib import Path
from dotenv import load_dotenv
from contextlib import AsyncExitStack
import subprocess
import time

from mcp_clients.mcp_client_console import MCPClient
from core.claude import Claude

from core.cli_chat import CliChat
from core.cli import CliApp

# Configure logging level - set to INFO to reduce debug noise
# You can change this to DEBUG, WARNING, ERROR as needed
# Or set via environment variable: LOG_LEVEL=DEBUG
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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


def start_web_mode():
    """
    Start the application in web mode.
    
    This function:
    1. Starts MCP servers in HTTP mode on different ports
    2. Starts the web server with Claude API proxy
    3. Opens the web interface in the browser (optional)
    """
    print("🌐 Starting MCP Learning Demo in Web Mode")
    print("=" * 50)
    
    # Get MCP server scripts (same logic as console mode)
    server_scripts = sys.argv[2:]  # Skip 'main.py' and '--web'
    
    if not server_scripts:
        mcp_servers_pattern = "mcp_servers/*mcp_server.py"
        server_scripts = glob.glob(mcp_servers_pattern)
        print(f"🔍 Auto-discovering MCP servers: {mcp_servers_pattern}")
    else:
        print(f"📋 Using specified MCP servers")
    
    if not server_scripts:
        print("⚠️  No MCP servers found or specified")
        return
    
    # Display servers that will be started
    print(f"🚀 Starting {len(server_scripts)} MCP server(s) in HTTP mode:")
    ports = [8001, 8002, 8003, 8004, 8005]  # Assign ports for each server
    server_processes = []
    
    try:
        # Start each MCP server in HTTP mode
        for i, script in enumerate(server_scripts):
            if i >= len(ports):
                print(f"   ⚠️  Skipping {script} - no available port")
                continue
                
            port = ports[i]
            server_name = Path(script).stem.replace('_mcp_server', '').replace('_', ' ').title()
            print(f"   {i+1}. {server_name} → http://localhost:{port} ({script})")
            
            # Start the server process with HTTP transport and specific port
            process = subprocess.Popen([
                "uv", "run", script, "http", str(port)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            server_processes.append((process, server_name, port))
            time.sleep(0.5)  # Give each server time to start
        
        # Wait a bit more for all servers to be fully ready
        print(f"\n⏳ Waiting for {len(server_processes)} MCP servers to start...")
        time.sleep(3)
        
        print("\n🌐 Starting web server...")
        print("   Web Interface: http://localhost:8000")
        print("   Claude API Proxy: http://localhost:8000/claude-proxy")
        print("   Configuration: http://localhost:8000/config")
        
        # Import and start the web server
        from web_server import start_server
        start_server(host="127.0.0.1", port=8000)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down web mode...")
        
        # Clean up server processes
        for process, name, port in server_processes:
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ Web mode stopped")


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


def print_usage():
    """Print usage instructions for the MCP Learning Demo."""
    print("MCP Learning Demo - Model Context Protocol Chat Interface")
    print("=" * 60)
    print()
    print("USAGE:")
    print("  Console Mode:")
    print("    uv run main.py                           # Auto-discover all servers")
    print("    uv run main.py server1.py server2.py    # Use specific servers")
    print()
    print("  Web Mode:")
    print("    uv run main.py --web                     # Auto-discover all servers")
    print("    uv run main.py --web server1.py         # Use specific servers")
    print()
    print("TRANSPORT MODES:")
    print("  • Console mode uses stdio transport (spawns subprocesses)")
    print("  • Web mode uses HTTP transport (remote server connections)")
    print()
    print("EXAMPLES:")
    print("  uv run main.py")
    print("  uv run main.py --web")
    print("  uv run main.py mcp_servers/calculator_mcp_server.py")
    print("  uv run main.py --web mcp_servers/calculator_mcp_server.py")
    print()


if __name__ == "__main__":
    # Show help if requested
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_usage()
        sys.exit(0)
    
    # Check if web mode is requested - handle separately to avoid event loop conflicts
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        start_web_mode()
        sys.exit(0)
    
    # Windows requires a specific event loop policy for subprocess support
    # This is needed for MCP servers which run as subprocesses
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # asyncio.run() is the standard way to run async programs in Python 3.7+
    # It creates an event loop, runs the async function, and cleans up
    asyncio.run(main())
