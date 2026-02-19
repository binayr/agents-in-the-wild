import logging
from typing import List

from agents.Heimdall.Grader import grade_documents
from agents.Heimdall.RAG import simple_rag_search
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict


logger = logging.getLogger(__name__)


class HeimdallState(TypedDict):
    input: str
    email: str
    messages: List[dict]
    response: str
    intent: str
    documents: List


rag_subgraph = StateGraph(HeimdallState)
rag_subgraph.add_node("search", simple_rag_search)
rag_subgraph.add_node("grade_documents", grade_documents)

rag_subgraph.add_edge(START, "search")
rag_subgraph.add_edge("search", "grade_documents")
rag_subgraph.add_edge("grade_documents", END)

checkpointer = MemorySaver()
rag_subgraph = rag_subgraph.compile(checkpointer=checkpointer)

