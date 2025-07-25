# MCP Server Implementation - Learning Example
# This file demonstrates how to create an MCP (Model Context Protocol) server
# that provides tools, resources, and prompts for an AI assistant to use.

from mcp.server.fastmcp import FastMCP
import sys
import os

# Check if HTTP transport is requested and configure BEFORE creating FastMCP instance
if len(sys.argv) > 1 and sys.argv[1] == "http":
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8002
    # Set environment variables BEFORE creating FastMCP instance
    os.environ['FASTMCP_HOST'] = '127.0.0.1'
    os.environ['FASTMCP_PORT'] = str(port)
    os.environ['FASTMCP_STREAMABLE_HTTP_PATH'] = '/mcp'

# Initialize the MCP server with a name and log level
# FastMCP is a simplified way to create MCP servers
mcp = FastMCP("DocumentMCP", log_level="ERROR")


# In-memory document storage
# In a real application, this might be a database or file system
# Key: document ID, Value: document content
docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# MCP Components Overview:
# 1. Tools: Functions the AI can call to perform actions (read, edit)
# 2. Resources: Data the AI can access via URIs (list docs, fetch content)
# 3. Prompts: Pre-defined templates for common tasks (format, summarize)

# The TODOs below have been implemented - they serve as a learning guide:
# TODO: Write a tool to read a doc ✓
# TODO: Write a tool to edit a doc ✓
# TODO: Write a resource to return all doc id's ✓
# TODO: Write a resource to return the contents of a particular doc ✓
# TODO: Write a prompt to rewrite a doc in markdown format ✓
# TODO: Write a prompt to summarize a doc (exercise for learner)


from pydantic import Field
from mcp.server.fastmcp.prompts import base


# MCP Tool Example 1: Read Document
# Tools are functions that the AI can call to perform actions
# The @mcp.tool decorator registers this function as an MCP tool
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string.",
)
def read_document(
    # Field() provides metadata about the parameter for the AI
    doc_id: str = Field(description="Id of the document to read"),
):
    # Validate that the document exists
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    # Return the document content
    return docs[doc_id]


# MCP Tool Example 2: Edit Document
# This tool allows the AI to modify document content
# Note: In production, you'd want proper permissions and audit logging
@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the documents content with a new string",
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(
        description="The text to replace. Must match exactly, including whitespace"
    ),
    new_str: str = Field(
        description="The new text to insert in place of the old text"
    ),
):
    # Validate document exists
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    # Perform the text replacement
    # Note: This modifies the in-memory storage directly
    docs[doc_id] = docs[doc_id].replace(old_str, new_str)


# MCP Resource Example 1: List Documents
# Resources are data sources that can be accessed via URIs
# The AI can reference these using @mentions in the chat
@mcp.resource("docs://documents", mime_type="application/json")
def list_docs() -> list[str]:
    """Return a list of all available document IDs"""
    return list(docs.keys())


# MCP Resource Example 2: Fetch Specific Document
# The {doc_id} in the URI is a parameter that gets passed to the function
# This allows @deposition.md style references in the chat
@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def fetch_doc(doc_id: str) -> str:
    """Fetch the content of a specific document by ID"""
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]


# MCP Prompt Example: Format Document
# Prompts are pre-defined templates that guide the AI to perform specific tasks
# They can be invoked using /format in the chat
@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in Markdown format.",
)
def format_document(
    doc_id: str = Field(description="Id of the document to format"),
) -> list[base.Message]:
    # Construct a prompt that instructs the AI on how to format the document
    # This demonstrates how prompts can reference tools (edit_document)
    prompt = f"""
    Your goal is to reformat a document to be written with markdown syntax.

    The id of the document you need to reformat is:
    <document_id>
    {doc_id}
    </document_id>

    Add in headers, bullet points, tables, etc as necessary. Feel free to add in extra text, but don't change the meaning of the report.
    Use the 'edit_document' tool to edit the document. After the document has been edited, respond with the final version of the doc. Don't explain your changes.
    """

    # Return a list of messages that will be sent to the AI
    return [base.UserMessage(prompt)]


# Exercise for learners: Implement a 'summarize' prompt
# Try creating an @mcp.prompt() decorated function that:
# 1. Takes a doc_id parameter
# 2. Instructs the AI to read the document using read_doc_contents
# 3. Returns a concise summary of the document
# Hint: Look at the format_document example above

# Entry point when running as a standalone MCP server
if __name__ == "__main__":
    """
    Start the MCP server with configurable transport.
    
    Transport options:
    - stdio: For console/CLI clients (default)
    - http: For web clients and remote connections
    
    Usage:
        python documents_mcp_server.py          # Uses stdio transport
        python documents_mcp_server.py http     # Uses HTTP transport on port 8002
    """
    
    # Check if HTTP transport is requested
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # Get port from command line or default to 8002
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8002
        
        print(f"📚 Starting Documents MCP Server with HTTP transport on port {port}")
        print("   Available tools: read_doc_contents, edit_document")
        print("   Available prompts: format")
        print(f"   MCP endpoint: http://localhost:{port}/mcp")
        
        # Use the correct transport name for FastMCP
        mcp.run(transport="streamable-http")
    else:
        # Default to stdio transport for console clients
        print("📚 Starting Documents MCP Server with stdio transport", file=sys.stderr)
        mcp.run(transport="stdio")
