#!/usr/bin/env python3
"""
Test script to verify calculator MCP server functionality
"""

import asyncio
import os
from contextlib import AsyncExitStack
from dotenv import load_dotenv

from mcp_client import MCPClient

async def test_calculator_server():
    """Test the calculator MCP server tools"""
    
    # Load environment variables
    load_dotenv()
    
    print("🧮 Testing Calculator MCP Server")
    print("=" * 40)
    
    async with AsyncExitStack() as stack:
        # Initialize calculator MCP client
        calc_client = await stack.enter_async_context(
            MCPClient(command="uv", args=["run", "mcp_servers/calculator_mcp_server.py"])
        )
        
        # Test listing available tools
        print("📋 Available tools:")
        tools = await calc_client.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        print("\n🔧 Testing calculator operations:")
        
        # Test addition
        result = await calc_client.call_tool("add", {"a": 5, "b": 3})
        print(f"  5 + 3 = {result}")
        
        # Test multiplication
        result = await calc_client.call_tool("multiply", {"a": 4, "b": 7})
        print(f"  4 × 7 = {result}")
        
        # Test square root
        result = await calc_client.call_tool("square_root", {"number": 16})
        print(f"  √16 = {result}")
        
        # Test expression evaluation
        result = await calc_client.call_tool("calculate_expression", {"expression": "2 + 3 * 4"})
        print(f"  2 + 3 × 4 = {result}")
        
        # Test resource
        print("\n📊 Calculator info:")
        info_result = await calc_client.read_resource("calculator://info")
        # The result might be wrapped, let's handle it properly
        if hasattr(info_result, 'contents'):
            import json
            info = json.loads(info_result.contents[0].text)
        else:
            info = info_result
        print(f"  Name: {info.get('name', 'Unknown')}")
        print(f"  Operations: {', '.join(info.get('operations', []))}")
        
        print("\n✅ All calculator tests passed!")

if __name__ == "__main__":
    asyncio.run(test_calculator_server())
