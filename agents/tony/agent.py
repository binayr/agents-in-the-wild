# code of agent one
import json
from typing import Any

from core.model import MASTOpenAIModel
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import State
from pydantic import BaseModel, Field

#########  AI MODEL #########
model = MASTOpenAIModel.get_model("gpt-4o")


#########  DATA MODEL  ##############
class ActionAgentOut(BaseModel):
    output: str = Field(description="output of the message")
    tool_call: str = Field(description="tool call to be made")
    tool_output: str = Field(description="output of the tool call")


#########  AGENTS  ##############
@tool
def take_action(action: str) -> dict[str, Any]:
    """
    Take an action based on the user's intention in question.
    """
    print(">>>>>>>>>>>>>>>>>>>>>>>> Tool Called >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(f"Taking action: {action}")
    return {"action": action, "status": "success"}


def action_agent(state: State) -> dict[str, Any]:
    print("Invoking action agent")
    question = state["question"]

    system_prompt = """
    You are a helpful assistant that can take actions based on user's questions.
    You have tools available at your disposal to take actions.
    Always use the take_action tool to execute the user's request.
    """

    # Create agent with HumanInTheLoopMiddleware for approval
    agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[take_action],
        checkpointer=InMemorySaver()
    )

    query = f"""User query: {question}"""

    inputs = {"messages": [("human", query)]}

    # Invoke the agent - it will interrupt if approval is needed
    result = agent.invoke(inputs)

    print(f"action_agent_result: {result}")

    return {"output": result.output, "tool_call": result.tool_call, "tool_output": result.tool_output}



########### Action Agent with HITL ##############
def action_agent_hitl(state: State) -> dict[str, Any]:
    print("Invoking action agent")
    question = state["question"]

    system_prompt = """
    You are a helpful assistant that can take actions based on user's questions.
    You have tools available at your disposal to take actions.
    Always use the take_action tool to execute the user's request.
    """

    # Create agent with HumanInTheLoopMiddleware for approval
    # The middleware will interrupt when take_action is about to be called
    agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=[take_action],
        checkpointer=InMemorySaver(),
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "take_action": {
                        "allowed_decisions": ["approve", "edit", "reject"],
                    }
                }
            ),
        ],
    )

    query = f"""User query: {question}"""

    inputs = {"messages": [("human", query)]}

    # Invoke the agent - it will interrupt if approval is needed
    # The interrupt will bubble up to the graph level
    result = agent.invoke(inputs)

    print(f"action_agent_result: {result}")

    # Extract the ToolMessage from the result
    messages = result.get("messages", [])
    tool_message = None
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_message = msg
            break

    # Default values
    output = "Action completed"
    tool_call = ""
    tool_output = ""

    if tool_message:
        print(f"ToolMessage found: {tool_message}")

        # Check if the action was rejected (status='error')
        if hasattr(tool_message, "status") and tool_message.status == "error":
            print("Action was rejected by user")
            output = "Action was rejected by user"
            tool_call = ""
            tool_output = "rejected"
        else:
            # Action was approved - parse the JSON content
            try:
                content_data = json.loads(tool_message.content)
                output = content_data.get("action", "Action completed")
                tool_call = tool_message.name
                tool_output = content_data.get("status", "success")
                print(f"Action approved: {output}, status: {tool_output}")
            except json.JSONDecodeError:
                # Fallback if content is not JSON
                output = tool_message.content
                tool_call = tool_message.name
                tool_output = "completed"

    return {"output": output, "tool_call": tool_call, "tool_output": tool_output}

