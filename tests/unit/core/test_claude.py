"""
Unit tests for core.claude module

Tests the Claude API wrapper functionality including:
- Message formatting helpers
- Text extraction from messages
- Basic initialization
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from anthropic.types import Message, TextBlock
from core.claude import Claude


class TestClaude:
    """Test cases for the Claude API wrapper class."""

    def test_init_without_proxy(self):
        """Test Claude initialization without proxy configuration."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('core.claude.Anthropic') as mock_anthropic:
                claude = Claude("claude-3-5-sonnet-20241022")
                
                assert claude.model == "claude-3-5-sonnet-20241022"
                mock_anthropic.assert_called_once_with(http_client=None)

    def test_init_with_proxy(self):
        """Test Claude initialization with proxy configuration."""
        with patch.dict('os.environ', {'HTTPS_PROXY': 'http://proxy:8080'}):
            with patch('core.claude.Anthropic') as mock_anthropic:
                with patch('core.claude.httpx.Client') as mock_httpx:
                    claude = Claude("claude-3-5-sonnet-20241022")
                    
                    assert claude.model == "claude-3-5-sonnet-20241022"
                    mock_httpx.assert_called_once_with(
                        proxy='http://proxy:8080',
                        verify=True
                    )
                    mock_anthropic.assert_called_once()

    def test_init_with_ssl_verification_disabled(self):
        """Test Claude initialization with SSL verification disabled."""
        with patch.dict('os.environ', {
            'HTTPS_PROXY': 'http://proxy:8080',
            'VERIFY_SSL': 'false'
        }):
            with patch('core.claude.Anthropic') as mock_anthropic:
                with patch('core.claude.httpx.Client') as mock_httpx:
                    claude = Claude("claude-3-5-sonnet-20241022")
                    
                    mock_httpx.assert_called_once_with(
                        proxy='http://proxy:8080',
                        verify=False
                    )

    def test_add_user_message_with_string(self):
        """Test adding a user message with string content."""
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = []
        
        claude.add_user_message(messages, "Hello, Claude!")
        
        assert len(messages) == 1
        assert messages[0] == {
            "role": "user",
            "content": "Hello, Claude!"
        }

    def test_add_user_message_with_message_object(self):
        """Test adding a user message with Message object."""
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = []
        
        # Create a mock Message object
        mock_message = Mock(spec=Message)
        mock_message.content = "Hello from Message object!"
        
        claude.add_user_message(messages, mock_message)
        
        assert len(messages) == 1
        assert messages[0] == {
            "role": "user",
            "content": "Hello from Message object!"
        }

    def test_add_assistant_message_with_string(self):
        """Test adding an assistant message with string content."""
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = []
        
        claude.add_assistant_message(messages, "Hello, human!")
        
        assert len(messages) == 1
        assert messages[0] == {
            "role": "assistant",
            "content": "Hello, human!"
        }

    def test_add_assistant_message_with_message_object(self):
        """Test adding an assistant message with Message object."""
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = []
        
        # Create a mock Message object
        mock_message = Mock(spec=Message)
        mock_message.content = "Hello from assistant Message object!"
        
        claude.add_assistant_message(messages, mock_message)
        
        assert len(messages) == 1
        assert messages[0] == {
            "role": "assistant",
            "content": "Hello from assistant Message object!"
        }

    def test_text_from_message_single_text_block(self):
        """Test extracting text from a message with single text block."""
        claude = Claude("claude-3-5-sonnet-20241022")
        
        # Create a mock message with text block
        text_block = Mock(spec=TextBlock)
        text_block.type = "text"
        text_block.text = "This is the text content"
        
        mock_message = Mock(spec=Message)
        mock_message.content = [text_block]
        
        result = claude.text_from_message(mock_message)
        
        assert result == "This is the text content"

    def test_text_from_message_multiple_text_blocks(self):
        """Test extracting text from a message with multiple text blocks."""
        claude = Claude("claude-3-5-sonnet-20241022")
        
        # Create mock text blocks
        text_block1 = Mock(spec=TextBlock)
        text_block1.type = "text"
        text_block1.text = "First line"
        
        text_block2 = Mock(spec=TextBlock)
        text_block2.type = "text"
        text_block2.text = "Second line"
        
        mock_message = Mock(spec=Message)
        mock_message.content = [text_block1, text_block2]
        
        result = claude.text_from_message(mock_message)
        
        assert result == "First line\nSecond line"

    def test_text_from_message_mixed_content_types(self):
        """Test extracting text from a message with mixed content types."""
        claude = Claude("claude-3-5-sonnet-20241022")
        
        # Create mock blocks - text and non-text
        text_block = Mock(spec=TextBlock)
        text_block.type = "text"
        text_block.text = "Text content"
        
        non_text_block = Mock()
        non_text_block.type = "image"
        
        mock_message = Mock(spec=Message)
        mock_message.content = [text_block, non_text_block]
        
        result = claude.text_from_message(mock_message)
        
        assert result == "Text content"

    def test_text_from_message_empty_content(self):
        """Test extracting text from a message with no text blocks."""
        claude = Claude("claude-3-5-sonnet-20241022")
        
        non_text_block = Mock()
        non_text_block.type = "image"
        
        mock_message = Mock(spec=Message)
        mock_message.content = [non_text_block]
        
        result = claude.text_from_message(mock_message)
        
        assert result == ""

    @patch('core.claude.Anthropic')
    def test_chat_basic_parameters(self, mock_anthropic):
        """Test chat method with basic parameters."""
        # Setup
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock(spec=Message)
        mock_client.messages.create.return_value = mock_response
        
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = [{"role": "user", "content": "Hello"}]
        
        # Execute
        result = claude.chat(messages)
        
        # Verify
        assert result == mock_response
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=messages,
            temperature=1.0,
            stop_sequences=[]
        )

    @patch('core.claude.Anthropic')
    def test_chat_with_system_prompt(self, mock_anthropic):
        """Test chat method with system prompt."""
        # Setup
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock(spec=Message)
        mock_client.messages.create.return_value = mock_response
        
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = [{"role": "user", "content": "Hello"}]
        system_prompt = "You are a helpful assistant."
        
        # Execute
        result = claude.chat(messages, system=system_prompt)
        
        # Verify
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=messages,
            temperature=1.0,
            stop_sequences=[],
            system=system_prompt
        )

    @patch('core.claude.Anthropic')
    def test_chat_with_thinking_enabled(self, mock_anthropic):
        """Test chat method with thinking mode enabled."""
        # Setup
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock(spec=Message)
        mock_client.messages.create.return_value = mock_response
        
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = [{"role": "user", "content": "Hello"}]
        
        # Execute
        result = claude.chat(messages, thinking=True, thinking_budget=2048)
        
        # Verify
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=messages,
            temperature=1.0,
            stop_sequences=[],
            thinking={
                "type": "enabled",
                "budget_tokens": 2048
            }
        )

    @patch('core.claude.Anthropic')
    def test_chat_with_tools(self, mock_anthropic):
        """Test chat method with tools provided."""
        # Setup
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock(spec=Message)
        mock_client.messages.create.return_value = mock_response
        
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"name": "test_tool", "description": "A test tool"}]
        
        # Execute
        result = claude.chat(messages, tools=tools)
        
        # Verify
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=messages,
            temperature=1.0,
            stop_sequences=[],
            tools=tools
        )

    @patch('core.claude.Anthropic')
    def test_chat_with_custom_temperature(self, mock_anthropic):
        """Test chat method with custom temperature."""
        # Setup
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock(spec=Message)
        mock_client.messages.create.return_value = mock_response
        
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = [{"role": "user", "content": "Hello"}]
        
        # Execute
        result = claude.chat(messages, temperature=0.5)
        
        # Verify
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=messages,
            temperature=0.5,
            stop_sequences=[]
        )

    @patch('core.claude.Anthropic')
    def test_chat_with_stop_sequences(self, mock_anthropic):
        """Test chat method with stop sequences."""
        # Setup
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock(spec=Message)
        mock_client.messages.create.return_value = mock_response
        
        claude = Claude("claude-3-5-sonnet-20241022")
        messages = [{"role": "user", "content": "Hello"}]
        stop_sequences = ["END", "STOP"]
        
        # Execute
        result = claude.chat(messages, stop_sequences=stop_sequences)
        
        # Verify
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=messages,
            temperature=1.0,
            stop_sequences=stop_sequences
        )
