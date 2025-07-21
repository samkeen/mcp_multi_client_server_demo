---
marp: true
theme: default
class: lead
paginate: true
backgroundColor: #fff
backgroundImage: url('https://marp.app/assets/hero-background.svg')
style: |
  .columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }
  .small-code {
    font-size: 0.8em;
  }
  .tiny-code {
    font-size: 0.7em;
  }
  .compact {
    line-height: 1.2;
  }
  pre {
    font-size: 0.8em;
  }
  section {
    font-size: 24px;
  }
  h1 {
    font-size: 2.2em;
  }
  h2 {
    font-size: 1.8em;
  }
  h3 {
    font-size: 1.4em;
  }
---

# Model Context Protocol (MCP)
## Learning Through Code

**Understanding MCP architecture and implementation patterns**

<!--
Speaker Notes:
Welcome to this hands-on exploration of the Model Context Protocol. This presentation will take you through MCP concepts using a real, working codebase that demonstrates all the key features. 

Unlike abstract explanations, we'll see actual code examples from a companion app that implements MCP clients, servers, tools, resources, and prompts. By the end, you'll understand both the theory and practical implementation of MCP.

The companion app we'll explore is from Anthropic's official MCP course and serves as a complete learning environment for understanding how MCP works in practice.
-->

---

# What is MCP?

- **Model Context Protocol**: A standardized way for AI applications to connect with external tools and data sources
- **Problem it solves**: Eliminates the need for developers to manually write tool schemas and implementations for every service
- **Core benefit**: Shifts tool creation burden from application developers to dedicated MCP server implementations

<!--
Speaker Notes:
Think of MCP as a "universal translator" for AI applications. Before MCP, if you wanted Claude to interact with GitHub, Slack, or your database, you had to write custom tool implementations for each service - defining schemas, handling API calls, managing errors, etc.

MCP changes this by creating a standard protocol. Now, service providers (or the community) can create MCP servers that expose their functionality as tools, resources, and prompts. Your application just connects to these servers and gets access to all their capabilities without writing any custom integration code.

This is similar to how we have standard protocols like HTTP - you don't need to write custom networking code for each website, you just use the standard HTTP protocol.
-->

---

# Traditional vs MCP Approach

<div class="columns">
<div>

## Traditional ❌
```python
# Developer writes for each service
def github_create_issue(title, body):
    # Custom API + schema
    pass

def slack_send_message(channel, text):
    # More custom code
    pass
```

</div>
<div>

## MCP ✅
```python
# Use pre-built servers
tools = await client.list_tools()
# Ready to use!
```

</div>
</div>

<!--
Speaker Notes:
This slide shows the dramatic difference in developer experience. On the left, the traditional approach requires you to write tool functions for every single service you want to integrate. Each one needs:
- Custom API calls with proper authentication
- Error handling for network issues, rate limits, etc.
- JSON schema definitions for Claude to understand the parameters
- Input validation and type conversion
- Documentation and maintenance

On the right, with MCP, you simply connect to pre-built servers and list their tools. The GitHub MCP server already has create_issue, list_repos, etc. The Slack MCP server has send_message, create_channel, etc. You get all this functionality instantly.

Our companion app demonstrates this - it has a document management MCP server with read_document and edit_document tools that are immediately available to Claude without any custom tool development.
-->

---

# MCP Architecture Overview

```
┌─────────────────┐    MCP Protocol     ┌─────────────────┐
│   MCP Client    │ ◄─────────────────► │   MCP Server    │
│                 │                     │                 │
│ • Your App      │                     │ • Tools         │
│ • Claude API    │                     │ • Resources     │
│ • Tool Manager  │                     │ • Prompts       │
└─────────────────┘                     └─────────────────┘
```

**Transport**: stdio, HTTP, WebSockets
**Communication**: JSON-RPC 2.0 messages

<!--
Speaker Notes:
This diagram shows the fundamental MCP architecture. It's a client-server model where:

The MCP Client side contains:
- Your application (the CLI chat app in our case)
- Claude API integration
- Tool Manager that routes requests to appropriate servers

The MCP Server side contains:
- Tools: Functions that Claude can call autonomously
- Resources: Data that your app can fetch on-demand
- Prompts: Pre-built instruction templates

The communication happens over various transports. In our companion app, we use stdio (standard input/output), which means the MCP server runs as a subprocess that communicates via stdin/stdout. This is perfect for local development and simple deployments.

The protocol itself uses JSON-RPC 2.0, which provides a standardized way to make remote procedure calls. Our app demonstrates all of this working together in a real implementation.
-->

---

# Three Core Primitives

## 🔧 Tools - Model-controlled
Claude decides when to execute

## 📄 Resources - App-controlled  
Application fetches data

## 💬 Prompts - User-controlled
Triggered by user actions

<!--
Speaker Notes:
These three primitives form the foundation of MCP and represent different control patterns:

TOOLS are model-controlled, meaning Claude autonomously decides when to use them. When you ask "What's in my GitHub repo?", Claude sees the available tools and decides to call the "list_repositories" tool on its own. You don't explicitly tell it to use that tool.

RESOURCES are app-controlled, meaning your application fetches them proactively. When you type "@report.pdf" in our companion app, the application immediately fetches that document content and includes it in the prompt to Claude. Claude doesn't decide to fetch it - the app does.

PROMPTS are user-controlled, triggered by explicit user actions. When you type "/format" in our app, you're explicitly asking to execute a formatting prompt template. This gives users direct control over specific workflows.

Understanding this control pattern is crucial - it determines how you architect your MCP integration and what type of primitive to use for different scenarios.
-->

---

# Tools Example

```python
@mcp.tool(name="read_doc_contents")
def read_document(doc_id: str = Field(description="Document ID")):
    return docs[doc_id]
```

**Purpose**: Add capabilities to Claude (file reading, API calls, calculations)

<!--
Speaker Notes:
This is a real tool from our companion app's MCP server. The @mcp.tool decorator automatically:
- Generates a JSON schema that Claude can understand
- Registers the function with the MCP server
- Handles parameter validation and type conversion

The Field() annotation provides Claude with a description of what this parameter does, helping it make intelligent decisions about when and how to call this tool.

When you ask Claude "What does report.pdf contain?", Claude will autonomously decide to call this read_doc_contents tool with doc_id="report.pdf" to get the information it needs to answer your question.

This is much simpler than the traditional approach where you'd need to manually write JSON schemas, handle parameter validation, and register tools with your application framework.
-->

---

# Resources Example

```python
@mcp.resource("docs://documents/{doc_id}")
def fetch_doc(doc_id: str) -> str:
    return docs[doc_id]
```

**Purpose**: Provide data to applications (document lists, user profiles)

<!--
Speaker Notes:
Resources are fundamentally different from tools - they're about data access, not actions. In our companion app, when you type "@report.pdf", the application immediately fetches this resource and includes its content in the prompt to Claude.

The URI pattern here uses templating - the {doc_id} part gets replaced with the actual document ID. So "docs://documents/report.pdf" becomes a call to fetch_doc with doc_id="report.pdf".

This is app-controlled, meaning your application decides when to fetch resources, not Claude. This is perfect for scenarios like:
- Auto-completion data (showing available documents as you type @)
- Context injection (including relevant documents in prompts)
- User interface elements (displaying lists of available items)

The key insight is that resources provide data TO your application, while tools provide capabilities FOR Claude to use.
-->

---

# Prompts Example

```python
@mcp.prompt(name="format")
def format_document(doc_id: str) -> list[Message]:
    return [UserMessage("Format this document...")]
```

**Purpose**: Enable user workflows (chat starters, templates)

<!--
Speaker Notes:
Prompts are essentially prompt engineering as a service. Instead of users having to craft perfect prompts for common tasks, domain experts can create optimized prompt templates that are tested and refined.

In our companion app, when you type "/format report.pdf", you're executing this prompt template. The template gets the doc_id parameter filled in, and returns a carefully crafted message that tells Claude exactly how to format the document.

This pattern is incredibly powerful because:
- Domain experts can encode their knowledge into prompts
- Users get consistent, high-quality results
- Prompts can be version-controlled and improved over time
- Complex workflows can be simplified into single commands

You see this pattern in Claude's web interface with the chat starter buttons - those are essentially prompts that help users get started with common tasks. The /format command in our app works similarly, providing a pre-built workflow for document formatting.
-->

---

# MCP Server Setup

<div class="small-code">

```python
from mcp.server.fastmcp import FastMCP

# Initialize server
mcp = FastMCP("DocumentMCP", log_level="ERROR")

# In-memory document storage
docs = {
    "report.pdf": "Report content...",
    "deposition.md": "Deposition content...",
}
```

</div>

**FastMCP Benefits**: Auto-schemas, simple setup, no manual work

<!--
Speaker Notes:
This shows how simple it is to create an MCP server using the FastMCP framework. In just a few lines, we have a fully functional MCP server.

FastMCP is part of the Python MCP SDK and provides significant benefits:
- Automatically generates JSON schemas from your Python function signatures
- Handles all the MCP protocol details (JSON-RPC, message routing, etc.)
- Provides decorators that make tool/resource/prompt registration trivial
- Manages server lifecycle and error handling

The document storage here is intentionally simple - just an in-memory dictionary. In a production system, this would be a database, file system, or API calls to external services. But for learning purposes, this simple approach lets us focus on MCP concepts without getting distracted by data persistence details.

Notice the server name "DocumentMCP" - this becomes the server identifier and helps with debugging when you have multiple servers running.
-->

---

# Tool Implementation

<div class="tiny-code">

```python
@mcp.tool(name="edit_document", description="Edit document text")
def edit_document(
    doc_id: str = Field(description="Document ID"),
    old_str: str = Field(description="Text to replace"),
    new_str: str = Field(description="Replacement text")
):
    if doc_id not in docs:
        raise ValueError(f"Doc {doc_id} not found")
    docs[doc_id] = docs[doc_id].replace(old_str, new_str)
```

</div>

**Pattern**: Decorator → Parameters → Validation → Logic

---

# Resource Implementation

<div class="tiny-code">

```python
# List all documents
@mcp.resource("docs://documents", mime_type="application/json")
def list_docs() -> list[str]:
    return list(docs.keys())

# Fetch specific document  
@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def fetch_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc {doc_id} not found")
    return docs[doc_id]
```

</div>

**URI patterns**: Static vs Templated `{doc_id}`

---

# Prompt Implementation

<div class="tiny-code">

```python
@mcp.prompt(name="format", description="Rewrite in Markdown")
def format_document(doc_id: str = Field(description="Document to format")):
    prompt = f"""
    Reformat this document to use markdown syntax.
    Document ID: {doc_id}
    
    Use the 'edit_document' tool to make changes.
    Add headers, bullet points, tables as needed.
    """
    return [base.UserMessage(prompt)]
```

</div>

**Purpose**: Expert-crafted prompts for domain-specific tasks

---

# MCP Client Setup

<div class="tiny-code">

```python
class MCPClient:
    def __init__(self, command: str, args: list[str]):
        self._command = command  # "python" or "uv"  
        self._args = args       # ["run", "mcp_servers/documents_mcp_server.py"]
        self._session = None
        
    async def connect(self):
        # Spawn server process via stdio
        server_params = StdioServerParameters(
            command=self._command, args=self._args
        )
        # Create session for communication
        self._session = ClientSession(stdio, write)
        await self._session.initialize()
```

</div>

---

# Client Operations

<div class="tiny-code">

```python
async def list_tools(self) -> list[Tool]:
    """Get all available tools"""
    result = await self.session().list_tools()
    return result.tools

async def call_tool(self, tool_name: str, tool_input) -> CallToolResult:
    """Execute a tool with parameters"""
    return await self.session().call_tool(tool_name, tool_input)

async def read_resource(self, uri: str) -> Any:
    """Fetch resource by URI"""
    result = await self.session().read_resource(AnyUrl(uri))
    resource = result.contents[0]
    
    if resource.mimeType == "application/json":
        return json.loads(resource.text)
    return resource.text
```

</div>

---

# Tool Usage Flow

<div class="compact">

1. **User**: "What does report.pdf contain?"
2. **CLI** → **Claude**: Query + available tools
3. **Claude** → **ToolManager**: call read_doc_contents("report.pdf")  
4. **ToolManager** → **MCPClient**: execute tool
5. **MCPClient** → **MCPServer**: JSON-RPC via stdio
6. **MCPServer**: Execute tool, return content
7. **Response flows back through chain**
8. **Claude**: Formulates answer with document content

</div>

<!--
Speaker Notes:
This sequence shows the complete flow when Claude decides to use a tool. Let me walk through what happens in our companion app:

1. User asks a natural language question
2. Our CLI sends this query to Claude along with a list of all available tools from all connected MCP servers
3. Claude analyzes the query and decides it needs document content, so it requests to call the read_doc_contents tool
4. Our ToolManager receives this request and routes it to the appropriate MCP client
5. The MCP client sends a JSON-RPC message via stdio to the MCP server subprocess
6. The MCP server executes the actual Python function and returns the document content
7. The response flows back through the same chain
8. Claude receives the document content and can now formulate a complete answer

This entire flow is asynchronous and non-blocking, so the user interface remains responsive throughout the process.
-->

---

# Resource Access Flow

<div class="compact">

1. **User**: "Summarize @deposition.md"
2. **CliChat**: Parse @mention
3. **CliChat** → **MCPClient**: read_resource("docs://documents/deposition.md")
4. **MCPClient** → **MCPServer**: Fetch resource
5. **MCPServer**: Return document content
6. **CliChat**: Build enriched prompt with content
7. **Claude**: Process with full document context

</div>

<!--
Speaker Notes:
This flow demonstrates the key difference between resources and tools - the application controls when resources are fetched, not Claude.

Here's what makes this powerful:

1. The user types @deposition.md - this is a UI convention we've implemented
2. Our CliChat code immediately recognizes this @ syntax and parses out the document ID
3. Before sending anything to Claude, the application fetches the resource content
4. The application builds an enriched prompt that includes both the user's request AND the full document content
5. Claude receives a complete context and can provide a comprehensive summary

This is much more efficient than the tool approach for this use case, because:
- No round-trip to Claude to decide what to fetch
- The user explicitly indicated what context they want
- Claude gets the full context upfront, leading to better responses

In our companion app, you can see this working - try typing "@" and you'll get auto-completion showing available documents. This is only possible because resources can be listed and fetched by the application independently.
-->

---

# Prompt Execution Flow

<div class="compact">

1. **User**: "/format report.pdf"
2. **CliChat**: Parse command and arguments
3. **CliChat** → **MCPClient**: get_prompt("format", {"doc_id": "report.pdf"})
4. **MCPClient** → **MCPServer**: Request prompt template
5. **MCPServer**: Return formatted prompt with instructions
6. **CliChat**: Add to conversation history
7. **Claude**: Execute formatting task (may use tools)

</div>

---

# Chat Loop Architecture

<div class="tiny-code">

```python
async def run(self, query: str) -> str:
    await self._process_query(query)  # Handle @mentions, /commands
    
    while True:
        # Send to Claude with all available tools
        response = self.claude_service.chat(
            messages=self.messages,
            tools=await ToolManager.get_all_tools(self.clients)
        )
        
        if response.stop_reason == "tool_use":
            # Execute tools and continue conversation
            tool_results = await ToolManager.execute_tool_requests(...)
            self.messages.append(tool_results)
        else:
            # Final response
            return self.claude_service.text_from_message(response)
```

</div>

---

# Tool Manager

<div class="tiny-code">

```python
class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]):
        """Collect tools from all connected MCP servers"""
        tools = []
        for client in clients.values():
            server_tools = await client.list_tools()
            tools.extend(format_for_claude(server_tools))
        return tools
    
    @classmethod 
    async def execute_tool_requests(cls, clients, message):
        """Route tool calls to appropriate servers"""
        for tool_request in extract_tool_requests(message):
            client = await cls._find_client_with_tool(clients, tool_request.name)
            result = await client.call_tool(tool_request.name, tool_request.input)
```

</div>

**Key feature**: Supports multiple MCP servers simultaneously

---

# CLI Auto-completion

<div class="tiny-code">

```python
class UnifiedCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # Handle @resource mentions
        if "@" in text:
            for resource_id in self.resources:
                if resource_id.startswith(prefix):
                    yield Completion(resource_id, display_meta="Resource")
        
        # Handle /command completions  
        if text.startswith("/"):
            for prompt in self.prompts:
                if prompt.name.startswith(prefix):
                    yield Completion(prompt.name, display_meta=prompt.description)
```

</div>

**Features**: Tab completion, real-time suggestions

---

# Async Patterns

**Why async?**
- Multiple MCP servers as separate processes
- Non-blocking I/O for stdio communication  
- Tool execution doesn't block UI

<div class="small-code">

```python
# AsyncExitStack manages multiple MCP connections
async with AsyncExitStack() as stack:
    doc_client = await stack.enter_async_context(MCPClient(...))
    other_client = await stack.enter_async_context(MCPClient(...))
    # All clients properly cleaned up on exit
```

</div>

**Key**: `await` ensures full initialization before use

<!--
Speaker Notes:
Async patterns are crucial in MCP applications for several reasons:

First, MCP servers run as separate processes. In our companion app, when you start main.py, it spawns mcp_servers/documents_mcp_server.py as a subprocess. Communication happens via stdin/stdout, which is inherently I/O-bound and benefits greatly from async patterns.

Second, you often connect to multiple MCP servers simultaneously. Our app demonstrates this - you can pass additional server scripts as command line arguments, and each runs as its own subprocess. AsyncExitStack lets us manage all these connections cleanly.

Third, tool execution should never block the user interface. When Claude calls a tool that takes time (like an API call or file operation), the async pattern ensures the CLI remains responsive.

The `await` keyword is critical - it ensures processes are fully initialized before use. Without proper awaiting, you might try to send requests to a server that hasn't finished starting up yet.

This async architecture is what makes MCP practical for real-world applications where responsiveness is important.
-->

---

# Error Handling

<div class="small-code">

```python
# Server-side validation
def read_document(doc_id: str):
    if doc_id not in docs:
        raise ValueError(f"Doc {doc_id} not found")
    return docs[doc_id]

# Client-side error handling
try:
    result = await client.call_tool(tool_name, tool_input)
    return format_success(result)
except Exception as e:
    return format_error(f"Tool execution failed: {e}")
```

</div>

**Best practices**: Validate early, clear messages, handle gracefully

---

# Development & Testing

## MCP Inspector
```bash
mcp dev mcp_servers/documents_mcp_server.py
# Opens web interface for testing tools, resources, prompts
```

## Direct Testing
<div class="small-code">

```python
# Test client connection
async with MCPClient("uv", ["run", "mcp_servers/documents_mcp_server.py"]) as client:
    tools = await client.list_tools()
    print(f"Available tools: {[t.name for t in tools]}")
```

</div>

---

# CLI Usage Examples

```bash
uv run main.py
> Tell me about @report.pdf        # Resource access
> /format deposition.md            # Prompt execution  
> What tools are available?        # Tool discovery
```

<!--
Speaker Notes:
These examples show the three different interaction patterns in our companion app:

1. "@report.pdf" demonstrates resource access - the app immediately fetches the document content and includes it in the prompt to Claude. You'll see auto-completion as you type the @.

2. "/format deposition.md" demonstrates prompt execution - this runs a pre-built prompt template that instructs Claude how to format documents. The prompt may in turn cause Claude to use tools to read and edit the document.

3. "What tools are available?" demonstrates tool discovery - Claude will autonomously decide to examine the available tools and list them for you.

The beauty of this interface is that users don't need to understand the underlying MCP concepts. They just use natural language, @ for documents, and / for commands. The complexity is hidden behind a simple, intuitive interface.

Try running the app yourself and experimenting with these patterns. You'll see how the auto-completion makes the interface feel polished and professional.
-->

---

# Real-World MCP Examples

## Tools (Model-controlled)
- Code execution environments
- API integrations (GitHub, Slack)
- Database queries
- File system operations

## Resources (App-controlled)  
- Document listings from Google Drive
- User profiles from databases
- Configuration settings
- Autocomplete data

## Prompts (User-controlled)
- Chat starter buttons in Claude
- Workflow templates
- Domain-specific instructions
- Quality assurance checklists

<!--
Speaker Notes:
These examples help illustrate when to use each primitive in real-world scenarios:

TOOLS are perfect when you want Claude to autonomously take actions:
- A code execution tool lets Claude run Python code when it needs to do calculations
- GitHub integration tools let Claude create issues, commits, or pull requests when helping with development
- Database query tools let Claude look up information as needed during conversations

RESOURCES are ideal for providing context and options to your application:
- Google Drive document listings for auto-completion in your UI
- User profile data that your app can inject into prompts for personalization
- Configuration settings that determine what tools or prompts are available
- Any data your app needs to show or use, independent of Claude's decision-making

PROMPTS work best for standardized workflows that users explicitly trigger:
- Chat starter buttons that help users begin conversations with proven prompts
- Templates for common tasks like code reviews, documentation, or analysis
- Domain-specific instructions crafted by experts in that field

The key is matching the control pattern to your use case: autonomous AI actions → tools, app-driven data → resources, user-triggered workflows → prompts.
-->

---

# Architecture Benefits

## For Developers
- **Reusable tools**: No reimplementation needed
- **Standardized interface**: Consistent APIs
- **Reduced maintenance**: Logic in dedicated servers

## For Users  
- **Consistent experience**: Same patterns across tools
- **Discoverability**: Auto-completion and help
- **Reliability**: Well-tested implementations

---

# Ecosystem Benefits

## For the Ecosystem
- **Composability**: Mix and match from different providers
- **Specialization**: Domain experts create optimal tools
- **Innovation**: Focus on capabilities, not integration

---

# Key Takeaways

1. **MCP shifts tool creation burden** from app developers to specialized server implementations

2. **Three primitives serve different needs**:
   - Tools → Model capabilities
   - Resources → App data access  
   - Prompts → User workflows

3. **Async architecture enables** non-blocking multi-server communication

4. **Transport agnostic design** supports local (stdio) and remote (HTTP) servers

5. **Rich CLI integration** provides auto-completion, syntax highlighting, and user-friendly interfaces

<!--
Speaker Notes:
Let me summarize the key insights from our exploration:

1. The fundamental value proposition of MCP is division of labor. Instead of every application developer writing GitHub tools, database tools, etc., domain experts create high-quality MCP servers that everyone can use. This is similar to how we don't all write HTTP servers - we use existing implementations.

2. The three primitives aren't arbitrary - they represent different control patterns in AI applications. Tools for when you want the AI to autonomously use capabilities, resources for when your app needs to provide context, prompts for when users want specific workflows.

3. Async isn't just a nice-to-have - it's essential for practical MCP applications. You're dealing with multiple processes, network I/O, and user interface responsiveness. Our companion app shows how this works in practice.

4. The transport agnostic design means you can start simple (stdio for local development) and scale up (HTTP for production deployments) without changing your application logic.

5. The CLI integration in our app shows how MCP enables rich user experiences - auto-completion of commands and resources, real-time suggestions, syntax highlighting. This makes AI applications much more user-friendly.

The companion app we've explored demonstrates all these concepts working together in a real, practical implementation.
-->

---

# Next Steps

## Extend the Learning App
- Add more document types and operations
- Implement additional MCP servers
- Create custom prompts for your domain

---

# Explore & Build

## Explore the Ecosystem
- Browse existing MCP servers on GitHub
- Try connecting to third-party services
- Contribute to the MCP specification

## Build Production Systems
- Implement error recovery and logging
- Add authentication and authorization
- Scale with multiple server instances

<!--
Speaker Notes:
Now that you understand MCP fundamentals through our companion app, here are your next steps:

EXPLORING THE ECOSYSTEM:
The MCP community is growing rapidly. GitHub has numerous MCP servers for popular services - GitHub, Slack, databases, file systems, and more. Many are open source, so you can learn from their implementations and contribute improvements.

Try connecting our companion app to third-party MCP servers. The architecture supports multiple servers simultaneously, so you can add a GitHub MCP server alongside our document server and have access to both sets of tools.

The MCP specification itself is community-driven and welcomes contributions. If you find gaps or have ideas for improvements, the community is very receptive to feedback.

BUILDING PRODUCTION SYSTEMS:
Our companion app is educational, but production systems need additional considerations:
- Error recovery: What happens when an MCP server crashes? How do you restart connections?
- Logging: Comprehensive logging of MCP messages for debugging and monitoring
- Authentication: Most real services need proper auth, not just in-memory data
- Authorization: Fine-grained control over who can use which tools
- Scaling: Load balancing across multiple instances of MCP servers

The foundation you've learned here scales up to these production requirements.
-->

---

# Questions & Discussion

**Resources for continued learning:**

- MCP Specification: https://modelcontextprotocol.io/
- Anthropic MCP Course: https://anthropic.skilljar.com/introduction-to-model-context-protocol
- Python SDK Documentation: https://github.com/modelcontextprotocol/python-sdk
- Community Examples: https://github.com/modelcontextprotocol

**This companion app demonstrates all core MCP concepts through working code examples**

<!--
Speaker Notes:
This concludes our hands-on exploration of MCP. We've seen how the companion app implements every major MCP concept:

- MCP client and server architecture
- All three primitives: tools, resources, and prompts
- Async patterns for managing multiple server connections
- Real CLI integration with auto-completion and user-friendly interactions
- Error handling and production considerations

The beautiful thing about this companion app is that it's not just a demo - it's a fully functional MCP implementation that you can extend and build upon. You can:

- Add new tools to the MCP server
- Connect additional MCP servers
- Modify the CLI interface
- Experiment with different transport mechanisms

I encourage you to explore the codebase, run the app yourself, and try implementing your own MCP servers. The resources listed here will help you dive deeper into specific aspects of MCP.

What questions do you have about MCP implementation, architecture, or the companion app we've explored?
-->

---

# Thank You!

**Happy learning with MCP! 🚀**

*The future of AI application development is collaborative, composable, and community-driven.*