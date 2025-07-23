# TODO List

## Temporary Feature Limitations

### Document Features (When No Documents Server Loaded)
**Status**: Temporarily disabled for calculator-only mode
**Reason**: Removed tight coupling between CliChat and documents server

When running with only non-document servers (e.g., `uv run main.py mcp_servers/calculator_mcp_server.py`):

❌ **@ Mentions**: `@document.pdf` references will not fetch document content
❌ **/ Commands**: `/format document.pdf` commands will not work

**Why This is Correct Behavior**:
- These features should only work when a documents server is available
- Clean architecture: no fake dependencies or hardcoded assumptions
- Graceful degradation: other features work normally

**Expected Behavior**:
- ✅ Calculator tools work fine: "what is 2+2?"
- ✅ General chat works: "hello", "explain math concepts"
- ✅ When documents server IS loaded: @ mentions and / commands work normally

## Future Enhancements

### 1. Better User Feedback
**Priority**: Low
**Description**: When user tries @mentions or /commands without documents server, provide helpful error message explaining they need to load documents server.

### 2. Feature Detection UI
**Priority**: Low  
**Description**: CLI could show which features are available based on loaded servers:
```
Available features:
  ✅ Mathematical calculations (calculator server)
  ❌ Document operations (no documents server loaded)
```

### 3. Dynamic Server Loading
**Priority**: Very Low
**Description**: Allow adding/removing servers during runtime without restart.

## Architecture Notes

The clean solution implemented:
- ✅ Removed `doc_client` parameter from CliChat constructor
- ✅ CliChat now dynamically discovers document capabilities from available clients  
- ✅ No artificial coupling between CliChat and specific server types
- ✅ Works with any combination of MCP servers
- ✅ True capability-based feature availability

This is the correct architectural approach vs. the previous band-aid fix.
