# CLI Application Module - Interactive Terminal Interface
# This module implements the user interface for the MCP chat application
# using prompt_toolkit for rich terminal interactions.

from typing import List, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.document import Document
from prompt_toolkit.buffer import Buffer

from core.cli_chat import CliChat


class CommandAutoSuggest(AutoSuggest):
    """
    Provides auto-suggestions for MCP commands (prompts).
    
    When a user types a command like "/format", this suggests
    the expected arguments based on the prompt definition.
    """
    
    def __init__(self, prompts: List):
        self.prompts = prompts
        # Create a dictionary for O(1) lookup by prompt name
        self.prompt_dict = {prompt.name: prompt for prompt in prompts}

    def get_suggestion(
        self, buffer: Buffer, document: Document
    ) -> Optional[Suggestion]:
        text = document.text

        # Only suggest for commands (starting with /)
        if not text.startswith("/"):
            return None

        parts = text[1:].split()

        # If user has typed a complete command name, suggest the first argument
        if len(parts) == 1:
            cmd = parts[0]

            if cmd in self.prompt_dict:
                prompt = self.prompt_dict[cmd]
                # Suggest the first argument name if the prompt has arguments
                return Suggestion(f" {prompt.arguments[0].name}")

        return None


class UnifiedCompleter(Completer):
    """
    Unified completion system for both commands and resources.
    
    Handles two types of completions:
    1. Commands: /format, /summarize (from MCP prompts)
    2. Resources: @report.pdf, @deposition.md (from MCP resources)
    """
    
    def __init__(self):
        self.prompts = []  # List of available MCP prompts
        self.prompt_dict = {}  # Dictionary for fast prompt lookup
        self.resources = []  # List of available document IDs

    def update_prompts(self, prompts: List):
        """Update available prompts from MCP server."""
        self.prompts = prompts
        self.prompt_dict = {prompt.name: prompt for prompt in prompts}

    def update_resources(self, resources: List):
        """Update available resources (document IDs) from MCP server."""
        self.resources = resources

    def get_completions(self, document, complete_event):
        """
        Generate completions based on the current input.
        
        This method is called by prompt_toolkit whenever the user
        might need completions (after @, /, or space).
        """
        text = document.text
        text_before_cursor = document.text_before_cursor

        # Handle resource completions (@ mentions)
        if "@" in text_before_cursor:
            # Find the last @ symbol to handle multiple mentions
            last_at_pos = text_before_cursor.rfind("@")
            prefix = text_before_cursor[last_at_pos + 1 :]

            # Complete resource IDs that match the prefix
            for resource_id in self.resources:
                if resource_id.lower().startswith(prefix.lower()):
                    yield Completion(
                        resource_id,
                        start_position=-len(prefix),  # Replace from @ onwards
                        display=resource_id,
                        display_meta="Resource",  # Shows "Resource" label
                    )
            return

        # Handle command completions (/ commands)
        if text.startswith("/"):
            parts = text[1:].split()

            # Complete command names
            if len(parts) <= 1 and not text.endswith(" "):
                cmd_prefix = parts[0] if parts else ""

                # Show all prompts that match the prefix
                for prompt in self.prompts:
                    if prompt.name.startswith(cmd_prefix):
                        yield Completion(
                            prompt.name,
                            start_position=-len(cmd_prefix),
                            display=f"/{prompt.name}",
                            display_meta=prompt.description or "",  # Show description
                        )
                return

            # After command name and space, suggest document IDs
            if len(parts) == 1 and text.endswith(" "):
                cmd = parts[0]

                # If this is a valid command, suggest resources as arguments
                if cmd in self.prompt_dict:
                    for id in self.resources:
                        yield Completion(
                            id,
                            start_position=0,
                            display=id,
                        )
                return

            if len(parts) >= 2:
                doc_prefix = parts[-1]

                for resource in self.resources:
                    if "id" in resource and resource["id"].lower().startswith(
                        doc_prefix.lower()
                    ):
                        yield Completion(
                            resource["id"],
                            start_position=-len(doc_prefix),
                            display=resource["id"],
                        )
                return


class CliApp:
    """
    Main CLI application class.
    
    Manages the interactive terminal interface, including:
    - Command completion
    - Resource completion
    - Keyboard shortcuts
    - Visual styling
    - Command history
    """
    
    def __init__(self, agent: CliChat):
        self.agent = agent  # The chat agent that handles MCP communication
        self.resources = []  # Cached list of available resources
        self.prompts = []  # Cached list of available prompts

        # Initialize completion systems
        self.completer = UnifiedCompleter()
        self.command_autosuggester = CommandAutoSuggest([])

        # Set up keyboard shortcuts
        self.kb = KeyBindings()

        # Keyboard shortcut: / triggers command completion
        @self.kb.add("/")
        def _(event):
            buffer = event.app.current_buffer
            # If at start of line, insert / and show completions
            if buffer.document.is_cursor_at_the_end and not buffer.text:
                buffer.insert_text("/")
                buffer.start_completion(select_first=False)
            else:
                # Otherwise just insert the character
                buffer.insert_text("/")

        # Keyboard shortcut: @ triggers resource completion
        @self.kb.add("@")
        def _(event):
            buffer = event.app.current_buffer
            buffer.insert_text("@")
            # Show completions if cursor is at the end
            if buffer.document.is_cursor_at_the_end:
                buffer.start_completion(select_first=False)

        # Keyboard shortcut: Space triggers context-aware completion
        @self.kb.add(" ")
        def _(event):
            buffer = event.app.current_buffer
            text = buffer.text

            buffer.insert_text(" ")

            # For commands, show argument completions after space
            if text.startswith("/"):
                parts = text[1:].split()

                # After command name, show document completions
                if len(parts) == 1:
                    buffer.start_completion(select_first=False)
                # If the argument looks like it wants a document ID
                elif len(parts) == 2:
                    arg = parts[1]
                    if (
                        "doc" in arg.lower()
                        or "file" in arg.lower()
                        or "id" in arg.lower()
                    ):
                        buffer.start_completion(select_first=False)

        # Store command history for up/down arrow navigation
        self.history = InMemoryHistory()
        
        # Create the main prompt session with all features enabled
        self.session = PromptSession(
            completer=self.completer,
            history=self.history,
            key_bindings=self.kb,
            # Visual styling for the prompt and completion menu
            style=Style.from_dict(
                {
                    "prompt": "#aaaaaa",  # Gray prompt color
                    "completion-menu.completion": "bg:#222222 #ffffff",  # Dark menu
                    "completion-menu.completion.current": "bg:#444444 #ffffff",  # Selected item
                }
            ),
            complete_while_typing=True,  # Show completions as you type
            complete_in_thread=True,  # Don't block UI for completions
            auto_suggest=self.command_autosuggester,  # Show command suggestions
        )

    async def initialize(self):
        """
        Initialize the CLI by fetching available resources and prompts.
        
        This is called after MCP connections are established.
        """
        await self.refresh_resources()
        await self.refresh_prompts()

    async def refresh_resources(self):
        """Fetch and cache available document IDs from MCP server."""
        try:
            # Get document IDs from the chat agent (which queries MCP)
            self.resources = await self.agent.list_docs_ids()
            # Update the completer with new resources
            self.completer.update_resources(self.resources)
        except Exception as e:
            print(f"Error refreshing resources: {e}")

    async def refresh_prompts(self):
        """Fetch and cache available prompts from MCP server."""
        try:
            # Get prompts from the chat agent (which queries MCP)
            self.prompts = await self.agent.list_prompts()
            # Update completer with new prompts
            self.completer.update_prompts(self.prompts)
            # Recreate auto-suggester with new prompts
            self.command_autosuggester = CommandAutoSuggest(self.prompts)
            self.session.auto_suggest = self.command_autosuggester
        except Exception as e:
            print(f"Error refreshing prompts: {e}")

    async def run(self):
        """
        Main event loop for the CLI.
        
        Continuously prompts for user input and displays responses.
        Handles Ctrl+C gracefully to exit.
        """
        while True:
            try:
                # Prompt for user input with async support
                # This allows other async tasks to run while waiting for input
                user_input = await self.session.prompt_async("> ")
                
                # Skip empty inputs
                if not user_input.strip():
                    continue

                # Process the input through the chat agent
                response = await self.agent.run(user_input)
                print(f"\nResponse:\n{response}")

            except KeyboardInterrupt:
                # Graceful exit on Ctrl+C
                break
