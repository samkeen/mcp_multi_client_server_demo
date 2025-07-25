"""
Unit tests for core.tools module

Tests the ToolManager class functionality focusing on:
- Simple utility functions that don't require complex mocking
- Tool result formatting
- Basic client search functionality

Note: Complex integration tests involving Message objects and tool execution
are documented in TODO_REFACTORING.md as requiring architectural changes.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from mcp.types import Tool

# Add path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.tools import ToolManager


class TestToolManager:
    """Test cases for the ToolManager utility functions."""

    @pytest.mark.asyncio
    async def test_get_all_tools_single_client(self):
        """Test getting tools from a single MCP client."""
        # Create mock tool
        mock_tool = Mock(spec=Tool)
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_tool.inputSchema = {"type": "object", "properties": {}}
        
        # Create mock client
        mock_client = AsyncMock()
        mock_client.list_tools.return_value = [mock_tool]
        
        clients = {"test_client": mock_client}
        
        # Execute
        result = await ToolManager.get_all_tools(clients)
        
        # Verify - the method returns a list of dictionaries
        assert len(result) == 1
        # Since the actual return type differs from annotation, we'll test the structure
        first_tool = result[0]
        assert isinstance(first_tool, dict)
        assert first_tool.get("name") == "test_tool"
        assert first_tool.get("description") == "A test tool"
        mock_client.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_tools_empty_clients(self):
        """Test getting tools when no clients are provided."""
        clients = {}
        
        # Execute
        result = await ToolManager.get_all_tools(clients)
        
        # Verify
        assert result == []

    @pytest.mark.asyncio
    async def test_find_client_with_tool_found(self):
        """Test finding a client that has a specific tool."""
        # Create mock tool
        mock_tool = Mock(spec=Tool)
        mock_tool.name = "target_tool"
        
        # Create mock clients
        mock_client1 = AsyncMock()
        mock_client1.list_tools.return_value = []
        
        mock_client2 = AsyncMock()
        mock_client2.list_tools.return_value = [mock_tool]
        
        clients = [mock_client1, mock_client2]
        
        # Execute
        result = await ToolManager._find_client_with_tool(clients, "target_tool")
        
        # Verify
        assert result == mock_client2
        mock_client1.list_tools.assert_called_once()
        mock_client2.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_client_with_tool_not_found(self):
        """Test finding a client when no client has the tool."""
        # Create mock clients with no matching tools
        mock_tool = Mock(spec=Tool)
        mock_tool.name = "other_tool"
        
        mock_client1 = AsyncMock()
        mock_client1.list_tools.return_value = []
        
        mock_client2 = AsyncMock()
        mock_client2.list_tools.return_value = [mock_tool]
        
        clients = [mock_client1, mock_client2]
        
        # Execute
        result = await ToolManager._find_client_with_tool(clients, "target_tool")
        
        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_find_client_with_tool_empty_clients(self):
        """Test finding a client when no clients are provided."""
        clients = []
        
        # Execute
        result = await ToolManager._find_client_with_tool(clients, "target_tool")
        
        # Verify
        assert result is None

    def test_build_tool_result_part_success(self):
        """Test building a tool result part for successful execution."""
        result = ToolManager._build_tool_result_part(
            "tool_use_123",
            "Operation completed successfully",
            "success"
        )
        
        expected = {
            "tool_use_id": "tool_use_123",
            "type": "tool_result",
            "content": "Operation completed successfully",
            "is_error": False
        }
        
        assert result == expected

    def test_build_tool_result_part_error(self):
        """Test building a tool result part for failed execution."""
        result = ToolManager._build_tool_result_part(
            "tool_use_456",
            "Operation failed",
            "error"
        )
        
        expected = {
            "tool_use_id": "tool_use_456",
            "type": "tool_result",
            "content": "Operation failed",
            "is_error": True
        }
        
        assert result == expected

    def test_build_tool_result_part_empty_content(self):
        """Test building a tool result with empty content."""
        result = ToolManager._build_tool_result_part(
            "tool_use_empty",
            "",
            "success"
        )
        
        expected = {
            "tool_use_id": "tool_use_empty",
            "type": "tool_result",
            "content": "",
            "is_error": False
        }
        
        assert result == expected

    def test_build_tool_result_part_special_characters(self):
        """Test building a tool result with special characters."""
        special_content = "Result with\nnewlines and\ttabs and special chars: !@#$%"
        result = ToolManager._build_tool_result_part(
            "tool_use_special",
            special_content,
            "success"
        )
        
        # Test the actual structure returned
        assert result.get("content") == special_content
        assert result.get("is_error") is False

    @pytest.mark.asyncio
    async def test_get_all_tools_multiple_clients_with_overlapping_tools(self):
        """Test getting tools from multiple clients with same tool names."""
        # Create mock tools with same name but different descriptions
        mock_tool1 = Mock(spec=Tool)
        mock_tool1.name = "common_tool"
        mock_tool1.description = "Tool from client 1"
        mock_tool1.inputSchema = {"type": "object"}
        
        mock_tool2 = Mock(spec=Tool)
        mock_tool2.name = "common_tool"
        mock_tool2.description = "Tool from client 2"
        mock_tool2.inputSchema = {"type": "string"}
        
        # Create mock clients
        mock_client1 = AsyncMock()
        mock_client1.list_tools.return_value = [mock_tool1]
        
        mock_client2 = AsyncMock()
        mock_client2.list_tools.return_value = [mock_tool2]
        
        clients = {"client1": mock_client1, "client2": mock_client2}
        
        # Execute
        result = await ToolManager.get_all_tools(clients)
        
        # Verify - both tools should be included even with same name
        assert len(result) == 2
        # Test the actual returned structure (list of dicts)
        descriptions = [item.get("description") for item in result if isinstance(item, dict)]
        assert "Tool from client 1" in descriptions
        assert "Tool from client 2" in descriptions

    # Note: execute_tool_requests tests are documented in TODO_REFACTORING.md
    # as requiring architectural changes due to complex typing issues
    # and dependency on anthropic.types.Message structure.
    # These will be covered in integration tests where we can test 
    # the actual behavior with real message objects.
