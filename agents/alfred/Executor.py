from functools import partial
import json
import logging
import os
from importlib.resources import files

from alfred.OuterAgents import outer_agent, outer_agent_local
from core.rag import rag_subgraph
from core.generate import generate


logger = logging.getLogger(__name__)

CORE_AGENTS = {
    "RAG-Search": rag_subgraph,
    "Generate": generate
}

def get_external_agents(local: bool = False):
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

    external_agents = {}
    for agent in agents:
        if agents[agent]["is_active"]:
            if agents[agent]["local"] == local == True:
                external_agents[agents[agent]["agent"]] = partial(outer_agent_local, agent_name=agents[agent]["agent"])
            else:
                external_agents[agents[agent]["agent"]] = partial(outer_agent, agent_name=agents[agent]["agent"])
    return external_agents

EXTERNAL_AGENTS = get_external_agents()
EXTERNAL_AGENTS_LOCAL = get_external_agents(local=True)
__AGENTS__MAP__ = {**CORE_AGENTS, **EXTERNAL_AGENTS, **EXTERNAL_AGENTS_LOCAL}


async def execute_plan(state):
    logger.info("------------------------Executing the plan------------------------")
    plan = state.get("plan", {})
    steps = plan.steps
    logger.info("Following below plan")
    logger.info(" -> ".join([step.action for step in steps]))

    for step in steps:
        action = step.action
        logger.info(f"Executing step: {action}")

        try:
            if action == "RAG-Search":
                updated_state = await rag_subgraph.ainvoke(state)
            else:
                updated_state = await __AGENTS__MAP__[action](state=state)

            # Update state with the results
            if updated_state and isinstance(updated_state, dict):
                state.update(updated_state)
                logger.info(f"Successfully executed step: {action}")
            else:
                logger.warning(f"Step {action} returned invalid state: {type(updated_state)}")

        except Exception as e:
            logger.error(f"Error executing step {action}: {e}", exc_info=True)
            # Continue with next step even if this one fails
            state.update({"error": f"Error in {action}: {str(e)}"})

    return state

if __name__ == "__main__":
    import asyncio
    from alfred.PlannerAgent import PlannerResponse, Step
    plan = PlannerResponse(
        intent="User wants to order a pizza",
        confidence=0.95,
        steps=[
            Step(step_id="s1", action="RAG-Search"),
            Step(step_id="s2", action="AgentB")
        ]
    )
    state = {
        "input": "order a pizza for me",
        "intent": "User wants to order a pizza",
        "summary": "",
        "plan": plan
    }
    plan = asyncio.run(execute_plan(state))
    print(plan)
