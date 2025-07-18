# Claude API Integration Module
# This module provides a wrapper around Anthropic's Claude API,
# simplifying message handling and API calls for the chat application.

from anthropic import Anthropic
from anthropic.types import Message


class Claude:
    """
    Wrapper class for Anthropic's Claude API.
    
    This class simplifies interaction with Claude by:
    - Managing the API client instance
    - Providing helper methods for message formatting
    - Abstracting common API parameters
    """
    
    def __init__(self, model: str):
        # Initialize the Anthropic client (API key from environment)
        self.client = Anthropic()
        # Store the model ID to use for all requests
        self.model = model

    def add_user_message(self, messages: list, message):
        """
        Add a user message to the conversation history.
        
        Args:
            messages: List of conversation messages
            message: Either a Message object or string content
        """
        user_message = {
            "role": "user",
            # Extract content if it's a Message object, otherwise use as-is
            "content": message.content
            if isinstance(message, Message)
            else message,
        }
        messages.append(user_message)

    def add_assistant_message(self, messages: list, message):
        """
        Add an assistant message to the conversation history.
        
        Args:
            messages: List of conversation messages
            message: Either a Message object or string content
        """
        assistant_message = {
            "role": "assistant",
            # Extract content if it's a Message object, otherwise use as-is
            "content": message.content
            if isinstance(message, Message)
            else message,
        }
        messages.append(assistant_message)

    def text_from_message(self, message: Message):
        """
        Extract plain text from a Claude Message object.
        
        Claude messages can contain multiple content blocks (text, images, etc.).
        This method extracts only the text blocks and joins them.
        """
        return "\n".join(
            [block.text for block in message.content if block.type == "text"]
        )

    def chat(
        self,
        messages,  # List of conversation messages
        system=None,  # Optional system prompt
        temperature=1.0,  # Response randomness (0.0-1.0)
        stop_sequences=[],  # Sequences that stop generation
        tools=None,  # Optional tool definitions for Claude to use
        thinking=False,  # Enable Claude's thinking mode
        thinking_budget=1024,  # Token budget for thinking
    ) -> Message:
        """
        Send a chat request to Claude and return the response.
        
        This method handles the API call with commonly used parameters
        and provides sensible defaults for the chat application.
        """
        # Build the API request parameters
        params = {
            "model": self.model,
            "max_tokens": 8000,  # Maximum response length
            "messages": messages,
            "temperature": temperature,
            "stop_sequences": stop_sequences,
        }

        # Add optional parameters if provided
        if thinking:
            # Enable Claude's thinking mode for complex reasoning
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }

        if tools:
            # Include tool definitions if the chat needs to use tools
            params["tools"] = tools

        if system:
            # Add system prompt to guide Claude's behavior
            params["system"] = system

        # Make the API call and return the response
        message = self.client.messages.create(**params)
        return message
