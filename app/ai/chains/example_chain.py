"""
Example LangChain LCEL chain.

Demonstrates how to build a simple prompt -> LLM -> parser chain
using LangChain Expression Language (LCEL).

Replace or extend this for your domain-specific chains.
"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import get_chat_model

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Answer concisely."),
    ("human", "{question}"),
])


def build_qa_chain():
    """Build a simple question-answering chain."""
    llm = get_chat_model()
    return _PROMPT | llm | StrOutputParser()


async def ask_question(question: str) -> str:
    """Run the Q&A chain with the given question."""
    chain = build_qa_chain()
    return await chain.ainvoke({"question": question})
