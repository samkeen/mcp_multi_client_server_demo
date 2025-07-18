# Core Module

## Overview

The `core` module contains the application's business logic, separated from the MCP protocol implementation. This separation follows clean architecture principles, making the codebase more maintainable and testable.

## Module Purpose

This module encapsulates:
- **Chat Logic**: Core conversation handling independent of MCP
- **Claude API Integration**: Direct interface with Anthropic's API
- **CLI Interface**: User interaction layer built with prompt_toolkit
- **Tool Utilities**: Helper functions for tool execution

## Why Separate from MCP?

1. **Separation of Concerns**: MCP is a protocol for tool communication. The core chat functionality should work independently of how tools are implemented or communicated.

2. **Testability**: Core logic can be tested without MCP server dependencies.

3. **Flexibility**: The chat interface could potentially work with other tool protocols beyond MCP.

4. **Clarity**: Developers can understand the chat flow without needing to understand MCP internals.

## Module Structure

### `chat.py`
Base chat functionality and message handling. This is the foundation that other components build upon.

### `claude.py`
Wrapper around Anthropic's API client. Handles:
- API authentication
- Message formatting
- Response streaming
- Error handling

### `cli.py`
Main CLI application using prompt_toolkit. Provides:
- Command completion (for `/` commands)
- Resource completion (for `@` mentions)
- Keyboard shortcuts and UI styling
- History management

### `cli_chat.py`
Bridges the CLI interface with chat logic. Handles:
- User input parsing (commands vs queries)
- MCP client coordination
- Response formatting for terminal display

### `tools.py`
Utility functions for tool handling, including:
- Tool result formatting
- Error handling helpers
- Common tool patterns

## Key Design Decisions

1. **Async First**: All components use async/await for non-blocking I/O operations
2. **Protocol Agnostic**: Core chat logic doesn't depend on MCP specifics
3. **Extensible**: New features can be added without modifying existing code
4. **User-Centric**: UI/UX considerations are handled in the CLI layer

## For Developers New to Async Python

The module heavily uses Python's `asyncio` for handling concurrent operations:
- Multiple MCP servers can run simultaneously
- User input doesn't block API calls
- Streaming responses update in real-time

Key async patterns to understand:
- `async def` functions must be awaited
- `AsyncExitStack` manages multiple async contexts
- `asyncio.create_task()` runs coroutines concurrently