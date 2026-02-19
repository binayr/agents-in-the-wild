"""
Hub.py - LangGraph workflow definition for TORI conversational AI system

This module defines the core workflow graph for the TORI system, connecting various
agent components into a complete conversation pipeline. It specifies how user inputs
flow through different processing steps including summarization, information retrieval,
document grading, and response generation.

The workflow is built using LangGraph's StateGraph system, which manages the flow of
state between different processing nodes and supports both synchronous and asynchronous
execution paths with MongoDB-based persistence.

Key components:
- StateGraph definition with input/output schema based on data models
- Parallel execution of RAG retrieval and summarization for efficiency
- Document grading to filter relevant information
- Response generation with suggested follow-up questions
- Graph persistence using MongoDB checkpoints
"""

import logging

from agents_2_0.Summeriser import summerise
from agents_2_0.PlannerAgent import plan
from agents_2_0.Executor import execute_plan

from agents_2_0.RAGSubGraph import rag_subgraph
from agents_2_0.FormLookup import form_lookup
from agents_2_0.Generate import generate
from agents_2_0.OuterAgents import outer_agent

from core.data_model import InputState, OutputState, OverallState
from db.checkpoints import checkpointer
from langgraph.graph import END, START, StateGraph

from agents.local_agents import local_agent1


logger = logging.getLogger(__name__)


def build_graph_nodes():
    # Initialize the builder for the StateGraph
    builder = StateGraph(OverallState, input=InputState, output=OutputState)

    # Add nodes to the graph
    # builder.add_node("greeting", welcome)                  # Welcome agent to greet the user
    builder.add_node("summeriser", summerise)             # Summarize history to understand user's intent
    builder.add_node("planner", plan)    # EDI conversation agent node
    builder.add_node("excutor", execute_plan)    # AVD conversation agent node

    builder.add_node("rag_subgraph", rag_subgraph)        # RAG subgraph to handle retrieval and grading
    builder.add_node("outer_agent", outer_agent)          # Outer agent to handle outer agent calls
    builder.add_node("generate", generate)

    # builder.add_node("local1", local_agent1)    # Local agent node

    # Modified flow to run retrieval and summarization in parallel
    builder.add_edge(START, "summeriser")
    builder.add_edge("summeriser", "planner")
    builder.add_edge("planner", "excutor")
    builder.add_edge("excutor", END)

    logger.info("INFO - Graph build completed")

    logger.info("INFO - Compiling the graph")
    graph_workflow = builder.compile(checkpointer=checkpointer)

    return graph_workflow


graph = build_graph_nodes()
nodes  = graph.nodes

def get_graph():
    """Get the global graph instance."""
    global graph
    if graph is None:
        graph = build_graph_nodes()
    return graph

