# Calculator MCP Server - Simple Proof of Concept
# This server provides basic mathematical operations as MCP tools

from mcp.server.fastmcp import FastMCP
from pydantic import Field
import math

# Initialize the MCP server
mcp = FastMCP("CalculatorMCP", log_level="ERROR")


@mcp.tool(
    name="add",
    description="Add two numbers together",
)
def add(
    a: float = Field(description="First number"),
    b: float = Field(description="Second number"),
) -> float:
    """Add two numbers and return the result."""
    result = a + b
    print(f"Calculator: {a} + {b} = {result}")
    return result


@mcp.tool(
    name="subtract",
    description="Subtract the second number from the first",
)
def subtract(
    a: float = Field(description="First number (minuend)"),
    b: float = Field(description="Second number (subtrahend)"),
) -> float:
    """Subtract b from a and return the result."""
    result = a - b
    print(f"Calculator: {a} - {b} = {result}")
    return result


@mcp.tool(
    name="multiply",
    description="Multiply two numbers together",
)
def multiply(
    a: float = Field(description="First number"),
    b: float = Field(description="Second number"),
) -> float:
    """Multiply two numbers and return the result."""
    result = a * b
    print(f"Calculator: {a} × {b} = {result}")
    return result


@mcp.tool(
    name="divide",
    description="Divide the first number by the second",
)
def divide(
    a: float = Field(description="Dividend (number to be divided)"),
    b: float = Field(description="Divisor (number to divide by)"),
) -> float:
    """Divide a by b and return the result."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    result = a / b
    print(f"Calculator: {a} ÷ {b} = {result}")
    return result


@mcp.tool(
    name="power",
    description="Raise the first number to the power of the second",
)
def power(
    base: float = Field(description="Base number"),
    exponent: float = Field(description="Exponent"),
) -> float:
    """Calculate base^exponent and return the result."""
    result = base ** exponent
    print(f"Calculator: {base}^{exponent} = {result}")
    return result


@mcp.tool(
    name="square_root",
    description="Calculate the square root of a number",
)
def square_root(
    number: float = Field(description="Number to find square root of"),
) -> float:
    """Calculate the square root of a number."""
    if number < 0:
        raise ValueError("Cannot calculate square root of negative number")
    result = math.sqrt(number)
    print(f"Calculator: √{number} = {result}")
    return result


@mcp.tool(
    name="calculate_expression",
    description="Evaluate a mathematical expression safely (basic operations only)",
)
def calculate_expression(
    expression: str = Field(description="Mathematical expression to evaluate (e.g., '2 + 3 * 4')"),
) -> float:
    """Safely evaluate a mathematical expression."""
    # Simple safety check - only allow basic math characters
    allowed_chars = set("0123456789+-*/().= ")
    if not all(c in allowed_chars for c in expression):
        raise ValueError("Expression contains invalid characters. Only numbers and +, -, *, /, (, ) are allowed.")
    
    try:
        # Use eval with a restricted environment for safety
        result = eval(expression, {"__builtins__": {}}, {})
        print(f"Calculator: {expression} = {result}")
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid mathematical expression: {e}")


# Resource to provide calculator information
@mcp.resource("calculator://info", mime_type="application/json")
def calculator_info():
    """Return information about available calculator operations."""
    return {
        "name": "Simple Calculator MCP Server",
        "version": "1.0.0",
        "operations": [
            "add", "subtract", "multiply", "divide", 
            "power", "square_root", "calculate_expression"
        ],
        "description": "Provides basic mathematical operations as MCP tools"
    }


if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run(transport="stdio")
