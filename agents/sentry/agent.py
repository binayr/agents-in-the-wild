# code of agent one
from typing import Any

import mlflow
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from core.model import AzureOpenAIModel
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

from sentry.tools.tools import classify_incident_severity, create_ticket, find_form


class FormData(BaseModel):
    form: dict[str, Any] = Field(description="form to be filled by the user")
    form_values: dict[str, Any] = Field(description="values filled by the user")


class IncidentData(BaseModel):
    incident: dict[str, Any] = Field(description="incident details")
    severity: str = Field(description="severity of the incident")


class AgentResponse(BaseModel):
    form: FormData | None = Field(default=None, description="form to be filled by the user")
    incident: IncidentData | None = Field(default=None, description="incident details")
    severity: str | None = Field(default=None, description="severity of the incident")


# Data Model
class AgentState(MessagesState):
    input: str = Field(description="input from the user")
    output: str = Field(description="final response to be returned")
    justification: str = Field(description="justification for the response")
    documents: list[str] = Field(
        default=[],
        description="context retrieved from knowledge base or other sources for RAG evaluation",
    )
    agent_response: AgentResponse = Field(description="response from the agent")


class AgentOut(BaseModel):
    output: str = Field(description="output of the message")
    form: dict[str, Any] | None = Field(default=None, description="form to be filled by the user")
    incident: dict[str, Any] | None = Field(default=None, description="incident details")
    severity: str | None = Field(default=None, description="severity of the incident")


# System prompt (loaded once at module import)
def read_prompt(prompt_path):
    with open(prompt_path, 'r') as file:
        return file.read()

system_prompt = read_prompt("prompt/mim-prompt.txt")


def _get_agent():
    """Get or create the agent with a fresh token."""
    # Create model with fresh token on each call
    model = AzureOpenAIModel.get_model("gpt-4o")

    # Agent
    return create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[find_form, classify_incident_severity, create_ticket],
        checkpointer=InMemorySaver(),
        response_format=AgentOut,
    )


# Agent caller function
def mim_agent_caller(state) -> dict[str, Any]:
    print("Invoking mim agent")
    print(state)
    question = state["input"]
    form_filled_values = state.get("form_filled_values", {})

    query = f"""
User query: {question}
form_filled_values: {form_filled_values}
"""

    inputs = {"messages": [("human", query)]}

    # Get agent with fresh token
    mim_agent = _get_agent()

    # Invoke the agent - it will interrupt if approval is needed
    result = mim_agent.invoke(inputs)

    structured_response = result.get("structured_response", AgentOut(output=""))
    print(f"agent_result: {structured_response}")

    return {
        "output": structured_response.output,
        "tool_call": result.get("tool_call"),
        "tool_output": result.get("tool_output"),
        "agent_response": {
            "form": structured_response.form,
            "incident": structured_response.incident,
            "severity": structured_response.severity,
        },
    }


#########  GRAPH  ##############
graph = StateGraph(AgentState)
graph.add_node("mim_agent", mim_agent_caller)

graph.add_edge(START, "mim_agent")
graph.add_edge("mim_agent", END)

checkpointer = InMemorySaver()
mim_agent_graph = graph.compile(checkpointer=checkpointer)  # code of agent one
