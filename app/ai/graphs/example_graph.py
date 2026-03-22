"""
Example LangGraph stateful agent graph.

Demonstrates a minimal node-based graph using LangGraph's StateGraph.
Replace the nodes and edges with your domain-specific agent logic.

Typical patterns:
- Router node that picks the next step
- Tool-calling node that invokes LangChain tools
- Human-in-the-loop checkpoint
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.ai.llm import get_chat_model


class AgentState(TypedDict):
    question: str
    answer: str
    steps: list[str]


async def think_node(state: AgentState) -> dict[str, Any]:
    """LLM reasoning step."""
    llm = get_chat_model()
    response = await llm.ainvoke(state["question"])
    return {
        "answer": response.content,
        "steps": state.get("steps", []) + ["think"],
    }


async def review_node(state: AgentState) -> dict[str, Any]:
    """Post-processing / review step."""
    return {
        "steps": state.get("steps", []) + ["review"],
    }


def build_example_graph() -> Any:
    """Construct and compile the example LangGraph agent."""
    graph = StateGraph(AgentState)
    graph.add_node("think", think_node)
    graph.add_node("review", review_node)
    graph.set_entry_point("think")
    graph.add_edge("think", "review")
    graph.add_edge("review", END)
    return graph.compile()


async def run_agent(question: str) -> AgentState:
    """Run the example agent and return the final state."""
    agent = build_example_graph()
    result = await agent.ainvoke({
        "question": question,
        "answer": "",
        "steps": [],
    })
    return result
