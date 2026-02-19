import logging
from a2a_utils import a2a_comm_with_output


logger = logging.getLogger(__name__)

async def outer_agent(agent_name, state):
    logger.info(f"------------------------{agent_name} Agent (External: Remote)------------------------")
    query = state.get("input")
    email = state.get("email")

    payload = {
        'message': {
            'role': 'user',
            'parts': [
                {'kind': 'text', 'text': query}
            ],
        }
    }

    try:
        _responses, final_output = await a2a_comm_with_output(payload, agent_name)
        logger.debug(f"{agent_name} Agent Response: {final_output}")
        final_output.pop('messages', None)
    except Exception as e:
        logger.error(f"Error calling {agent_name} agent: {e}")
        return {"error": str(e)}

    logger.info(f"Final output: {final_output}")
    return final_output


async def outer_agent_local(agent_name, state):
    logger.info(f"------------------------{agent_name} Agent (External: Local)------------------------")

    # Get the graph and invoke the specific node by name
    # Can not take this import to top because of circular import
    from core.graph import get_graph

    graph = get_graph()

    # Get the node function from the graph's nodes
    if agent_name in graph.nodes:
        node_func = graph.nodes[agent_name]
        result = await node_func.ainvoke(state)
        return result
    else:
        logger.error(f"Node '{agent_name}' not found in graph")
        return {"error": f"Node '{agent_name}' not found in graph"}
