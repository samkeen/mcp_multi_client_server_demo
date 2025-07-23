# CLI Chat Module - Bridges CLI with MCP and Claude
# This module handles the chat flow specific to the CLI interface,
# including processing commands (/) and resource mentions (@).

from typing import List, Tuple
from mcp.types import Prompt, PromptMessage
from anthropic.types import MessageParam

from core.chat import Chat
from core.claude import Claude
from mcp_client import MCPClient


class CliChat(Chat):
    """
    CLI-specific chat implementation that extends the base Chat class.
    
    This class adds CLI-specific features:
    - Processing @ mentions to include document content
    - Processing / commands to execute MCP prompts
    - Managing the document-specific MCP client
    """
    
    def __init__(
        self,
        clients: dict[str, MCPClient],  # All MCP clients
        claude_service: Claude,  # Claude API service
    ):
        # Initialize parent class with all clients
        super().__init__(clients=clients, claude_service=claude_service)

    async def list_prompts(self) -> list[Prompt]:
        """Get available prompts from any available client."""
        for client in self.clients.values():
            try:
                return await client.list_prompts()
            except Exception:
                continue
        return []

    async def list_docs_ids(self) -> list[str]:
        """Get list of available document IDs, if any documents server exists."""
        for client in self.clients.values():
            try:
                return await client.read_resource("docs://documents")
            except Exception:
                continue
        return []

    async def get_doc_content(self, doc_id: str) -> str:
        """Fetch document content, if any documents server exists."""
        for client in self.clients.values():
            try:
                return await client.read_resource(f"docs://documents/{doc_id}")
            except Exception:
                continue
        raise FileNotFoundError(f"Document '{doc_id}' not found - no documents server available")

    async def get_prompt(
        self, command: str, doc_id: str
    ) -> list[PromptMessage]:
        """Get a prompt template, trying all available clients."""
        for client in self.clients.values():
            try:
                return await client.get_prompt(command, {"doc_id": doc_id})
            except Exception:
                continue
        raise ValueError(f"Command '{command}' not found in any server")

    async def _extract_resources(self, query: str) -> str:
        """
        Extract and fetch content for any @mentioned documents.
        
        Example: "Tell me about @report.pdf" will fetch report.pdf content
        and return it wrapped in XML tags for Claude to process.
        """
        # Find all words starting with @ in the query
        mentions = [word[1:] for word in query.split() if word.startswith("@")]

        # Get available document IDs from the server
        doc_ids = await self.list_docs_ids()
        mentioned_docs: list[Tuple[str, str]] = []

        # Fetch content for each mentioned document that exists
        for doc_id in doc_ids:
            if doc_id in mentions:
                content = await self.get_doc_content(doc_id)
                mentioned_docs.append((doc_id, content))

        # Format documents in XML for clear structure in the prompt
        return "".join(
            f'\n<document id="{doc_id}">\n{content}\n</document>\n'
            for doc_id, content in mentioned_docs
        )

    async def _process_command(self, query: str) -> bool:
        """
        Process / commands by fetching and executing MCP prompts.
        
        Example: "/format report.pdf" will get the format prompt
        and add it to the message history.
        
        Returns True if a command was processed, False otherwise.
        """
        if not query.startswith("/"):
            return False

        words = query.split()
        command = words[0].replace("/", "")  # Remove the / prefix

        # Get the prompt template from the MCP server
        # The second word is assumed to be the document ID
        try:
            messages = await self.get_prompt(command, words[1])
            # Convert MCP prompt messages to Claude message format
            self.messages += convert_prompt_messages_to_message_params(messages)
            return True
        except (ValueError, IndexError):
            # Command not found or invalid syntax - treat as regular query
            return False

    async def _process_query(self, query: str):
        """
        Process user queries, handling both commands and regular questions.
        
        This method:
        1. First checks if it's a command (/format, /summarize)
        2. If not, extracts any @mentioned resources
        3. Constructs a prompt with the query and resource content
        """
        # Check if this is a command first
        if await self._process_command(query):
            return

        # Extract content from any @mentioned documents
        added_resources = await self._extract_resources(query)

        # Construct the prompt for Claude with clear instructions
        prompt = f"""
        The user has a question:
        <query>
        {query}
        </query>

        The following context may be useful in answering their question:
        <context>
        {added_resources}
        </context>

        Note the user's query might contain references to documents like "@report.docx". The "@" is only
        included as a way of mentioning the doc. The actual name of the document would be "report.docx".
        If the document content is included in this prompt, you don't need to use an additional tool to read the document.
        Answer the user's question directly and concisely. Start with the exact information they need. 
        Don't refer to or mention the provided context in any way - just use it to inform your answer.
        """

        # Add the constructed prompt to the message history
        self.messages.append({"role": "user", "content": prompt})


def convert_prompt_message_to_message_param(
    prompt_message: "PromptMessage",
) -> MessageParam:
    """
    Convert an MCP PromptMessage to Claude's MessageParam format.
    
    MCP and Claude use slightly different message formats, so this
    function handles the conversion, including extracting text from
    various content structures.
    """
    # Map MCP roles to Claude roles
    role = "user" if prompt_message.role == "user" else "assistant"

    content = prompt_message.content

    # Handle content that's a single text block
    # Content can be either a dict or an object with attributes
    if isinstance(content, dict) or hasattr(content, "__dict__"):
        content_type = (
            content.get("type", None)
            if isinstance(content, dict)
            else getattr(content, "type", None)
        )
        if content_type == "text":
            # Extract the text field
            content_text = (
                content.get("text", "")
                if isinstance(content, dict)
                else getattr(content, "text", "")
            )
            return {"role": role, "content": content_text}

    # Handle content that's a list of blocks
    if isinstance(content, list):
        text_blocks = []
        for item in content:
            # Each item can be a dict or object
            if isinstance(item, dict) or hasattr(item, "__dict__"):
                item_type = (
                    item.get("type", None)
                    if isinstance(item, dict)
                    else getattr(item, "type", None)
                )
                if item_type == "text":
                    # Extract text from each text block
                    item_text = (
                        item.get("text", "")
                        if isinstance(item, dict)
                        else getattr(item, "text", "")
                    )
                    text_blocks.append({"type": "text", "text": item_text})

        if text_blocks:
            return {"role": role, "content": text_blocks}

    # Fallback for unrecognized content format
    return {"role": role, "content": ""}


def convert_prompt_messages_to_message_params(
    prompt_messages: List[PromptMessage],
) -> List[MessageParam]:
    """
    Convert a list of MCP PromptMessages to Claude MessageParams.
    
    This is used when executing MCP prompts that return multiple messages.
    """
    return [
        convert_prompt_message_to_message_param(msg) for msg in prompt_messages
    ]
