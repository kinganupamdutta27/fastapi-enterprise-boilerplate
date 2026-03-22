"""
Example LangChain custom tool.

Shows how to define tools that can be used by LangChain agents.
Tools can call internal APIs, databases, external services, etc.
"""

from __future__ import annotations

from langchain_core.tools import tool


@tool
def search_items(query: str) -> str:
    """Search items in the database by name.

    This is a placeholder — replace the body with actual DB calls
    or API integrations.
    """
    return f"Found items matching '{query}': [item_1, item_2]"


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"
