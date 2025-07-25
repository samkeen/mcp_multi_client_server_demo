#!/bin/bash
# Test runner script for the MCP CLI Demo project

echo "🧪 MCP CLI Demo - Unit Test Runner"
echo "================================="
echo ""

echo "📊 Running all unit tests with coverage..."
uv run python -m pytest tests/unit/ --cov=core --cov-report=term-missing --cov-report=html -v

echo ""
echo "📁 Coverage report generated in htmlcov/index.html"
echo ""

echo "📖 See tests/README.md for detailed information"
echo "⚠️  See tests/TODO_REFACTORING.md for architectural improvements needed"
