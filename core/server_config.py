# Shared MCP Server Configuration
# This module provides centralized server discovery and port assignment
# to ensure consistency between main.py and web_server.py

import glob
from pathlib import Path
from typing import Dict, List, Tuple


class MCPServerConfig:
    """
    Centralized MCP server configuration and discovery.
    
    This class ensures that both main.py (server startup) and web_server.py 
    (client connections) use identical server discovery and port assignment logic.
    """
    
    BASE_PORT = 8001
    MAX_SERVERS = 10
    SERVER_PATTERN = "mcp_servers/*mcp_server.py"
    
    @classmethod
    def discover_servers(cls) -> List[str]:
        """
        Discover MCP server scripts using glob pattern.
        
        Returns:
            List[str]: List of server script paths in filesystem order
        """
        server_scripts = glob.glob(cls.SERVER_PATTERN)
        return server_scripts
    
    @classmethod
    def get_server_configs(cls) -> List[Tuple[str, str, int, str]]:
        """
        Get complete server configuration for startup.
        
        Returns:
            List[Tuple[str, str, int, str]]: List of (script_path, server_name, port, display_name)
        """
        server_scripts = cls.discover_servers()
        configs = []
        
        for i, script in enumerate(server_scripts):
            if i >= cls.MAX_SERVERS:
                break
                
            port = cls.BASE_PORT + i
            # Server name for internal use (lowercase, underscores)
            server_name = Path(script).stem.replace('_mcp_server', '').replace('_', ' ').lower().replace(' ', '_')
            # Display name for user-facing output (Title Case)
            display_name = Path(script).stem.replace('_mcp_server', '').replace('_', ' ').title()
            
            configs.append((script, server_name, port, display_name))
        
        return configs
    
    @classmethod
    def get_client_configs(cls) -> Dict[str, str]:
        """
        Get server configurations for web client connections.
        
        Returns:
            Dict[str, str]: Mapping of server_name -> URL for HTTP connections
        """
        server_configs = cls.get_server_configs()
        client_configs = {}
        
        for script, server_name, port, display_name in server_configs:
            url = f"http://localhost:{port}/mcp"
            client_configs[server_name] = url
            
        return client_configs
    
    @classmethod
    def print_discovery_info(cls, context: str = ""):
        """
        Print server discovery information for debugging.
        
        Args:
            context: Context string to identify where this is called from
        """
        configs = cls.get_server_configs()
        context_str = f" ({context})" if context else ""
        
        print(f"🔍 Discovered {len(configs)} MCP servers{context_str}:")
        for script, server_name, port, display_name in configs:
            print(f"   • {server_name} → http://localhost:{port}/mcp")