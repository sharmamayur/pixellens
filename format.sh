#!/bin/bash

# Format and lint Python code with Ruff
echo "🔧 Formatting and linting code with Ruff..."

# Format all Python files
ruff format .

# Lint and auto-fix issues
ruff check . --fix

echo "✅ Done! Code has been formatted and linted."
