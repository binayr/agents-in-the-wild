import json
import logging
import os
from typing import List
from importlib.resources import files

from alfred.prompt import PLANNER_PROMPT, USER_PROMPT
from core.model import AzureOpenAIModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Step(BaseModel):
    """
    Pydantic model for a step in the planner agent output.
    """
    step_id: str = Field(
        description="Unique identifier for the step."
    )
    action: str = Field(
        description="Action to be executed in the step."
    )


# Data model
class PlannerResponse(BaseModel):
    """
    Pydantic model for planner agent output.

    This model enforces a structured output format from the language model,
    ensuring consistent and parseable planner data.
    """

    intent: str = Field(
        description="User intent extracted from the conversation history, used for context."
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1, indicating the confidence of the intent."
    )
    steps: List[Step] = Field(
        description="List of steps to be executed in the order of execution."
    )


def get_planner_agent():
    # Use GPT-4o for planner agent
    model = AzureOpenAIModel.get_model("gpt-4o")

    # LLM with function call
    structured_llm_grader = model.with_structured_output(PlannerResponse)

    # Prompt
    planner_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PLANNER_PROMPT),
            ("human", USER_PROMPT),
        ]
    )

    planner_agent = planner_prompt | structured_llm_grader
    return planner_agent

def get_external_capabilities():
    # Load agent registry using importlib.resources (works in both dev and production)
    try:
        registry_file = files('alfred').joinpath('agent-registry.json')
        registry_content = registry_file.read_text()
        agents = json.loads(registry_content)
    except Exception as e:
        # Fallback to file-based loading for development/editable installs
        logger.warning(f"Could not load registry using importlib.resources: {e}")
        logger.warning("Falling back to file-based loading")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        registry_path = os.path.join(current_dir, 'agent-registry.json')
        with open(registry_path, 'r') as f:
            agents = json.load(f)

    external_capabilities = []
    for agent in agents:
        if agents[agent]["is_active"]:
            external_capabilities.append(f"-{agents[agent]}: {agents[agent]["description"]}")
    return "\n".join(external_capabilities)


async def plan(state):
    """
    LangGraph node function that summarizes conversation history.

    This function:
    1. Extracts conversation history and the current query from the workflow state
    2. Applies optimization logic to skip processing for new conversations
    3. Focuses on recent messages (last 6) to prioritize recency and reduce processing time
    4. Generates a structured summary using the language model
    5. Times the execution for performance monitoring

    The function is optimized to handle conversation history efficiently by:
    - Skipping summarization entirely for new conversations (fewer than 2 messages)
    - Using a smaller model (gpt-4o-mini) for better performance
    - Limiting the history context to recent messages

    Args:
        state (dict): Current workflow state with conversation history and user query

    Returns:
        dict: Updated state with the conversation summary for context in subsequent nodes
    """

    logger.info("------------------------Planning the next step------------------------")

    query = state.get("input", "")
    messages = state.get("messages", [])
    summary = state.get("summary", "")
    intent = state.get("intent", "")
    external_capabilities = get_external_capabilities()

    planner_agent = get_planner_agent()

    # Only do full summarization for longer conversations
    plan = await planner_agent.ainvoke({
        "input": query,
        "query": query,
        "intent": intent,
        "summary": summary,
        "messages": messages,
        "external_capabilities": external_capabilities
    })

    logger.info(plan.confidence)
    logger.info(plan.steps)

    return {"plan": plan}


if __name__ == "__main__":
    import asyncio
    plan = asyncio.run(plan({
        "query": "order a pizza for me",
        "intent": "User wants to order a pizza",
        "summary": "",
        "messages": [
            HumanMessage(content="order a pizza for me")
        ]
    }))
    print(plan)
