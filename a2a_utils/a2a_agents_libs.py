import os
import json
import logging
from typing import Any, Optional
from uuid import uuid4
from importlib.resources import files

import httpx
from a2a.client.client_factory import ClientFactory, ClientConfig
from a2a.client import Client
from a2a.types import Message, AgentCard
from a2a_utils.auth_provider import AzureAuthProvider

logger = logging.getLogger(__name__)
AGENT_URL = "https://mim-tbmagents-pipedream.maersk-digital.net/a2a/"


def create_message_parts(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Create A2A message parts from a list of part dictionaries.

    Handles different part types:
    - text: Uses 'text' field
    - json/data: Uses 'data' field (A2A spec uses 'data' kind, not 'json')
    - file: Uses 'file' field
    - other: Copies all fields except 'kind'/'type'

    Args:
        parts: List of part dictionaries, each with 'kind'/'type' and relevant fields

    Returns:
        List of properly formatted A2A message parts

    Example:
        ```python
        parts = [
            {'kind': 'text', 'text': 'Hello'},
            {'kind': 'json', 'data': {'key': 'value'}}  # 'json' gets converted to 'data'
        ]
        message_parts = create_message_parts(parts)
        ```
    """
    message_parts = []
    for part in parts:
        # Convert 'type' to 'kind' if needed (A2A spec uses 'kind')
        part_kind = part.get('kind') or part.get('type', 'text')

        # Build part based on kind
        if part_kind in ('json', 'data'):
            # Handle JSON/data parts - A2A spec uses 'data' not 'json'
            part_dict = {
                'kind': 'data',
                'data': part.get('data') or part.get('json') or {}
            }
            # Preserve additional fields like 'name'
            for key, value in part.items():
                if key not in ('kind', 'type', 'data', 'json'):
                    part_dict[key] = value
        elif part_kind == 'text':
            # Handle text parts
            part_dict = {
                'kind': 'text',
                'text': part.get('text', '')
            }
            # Preserve additional fields
            for key, value in part.items():
                if key not in ('kind', 'type', 'text'):
                    part_dict[key] = value
        elif part_kind == 'file':
            # Handle file parts
            part_dict = {
                'kind': 'file',
                'file': part.get('file', {})
            }
            # Preserve additional fields
            for key, value in part.items():
                if key not in ('kind', 'type', 'file'):
                    part_dict[key] = value
        else:
            # Handle other part types - copy all fields
            part_dict = {'kind': part_kind}
            # Copy all other fields from the part
            for key, value in part.items():
                if key not in ('kind', 'type'):
                    part_dict[key] = value

        message_parts.append(part_dict)

    return message_parts

def override_agent_card_url(client: Client) -> Client:
    # CRITICAL FIX: Override the agent card URL if it points to localhost
    # The remote server's agent card may be misconfigured with localhost
    # Access the internal card (BaseClient stores it as _card)
    if hasattr(client, '_card'):
        card = client._card
        logger.info(f"Agent card URL (before override): {card.url}")

        if "localhost" in card.url or "127.0.0.1" in card.url:
            logger.warning(f"Agent card URL contains localhost: {card.url}")
            logger.warning(f"Overriding with AGENT_URL: {AGENT_URL}")
            card.url = AGENT_URL

            # Also fix additional interfaces if they contain localhost
            if hasattr(card, 'additional_interfaces') and card.additional_interfaces:
                for iface in card.additional_interfaces:
                    if "localhost" in iface.url or "127.0.0.1" in iface.url:
                        logger.warning(f"Overriding additional interface URL: {iface.url} -> {AGENT_URL}")
                        iface.url = AGENT_URL

            logger.info(f"Agent card URL (after override): {card.url}")

    # Also fix the transport URL (JsonRpcTransport stores URL in self.url)
    if hasattr(client, '_transport') and hasattr(client._transport, 'url'):
        transport_url = client._transport.url
        logger.info(f"Transport URL (before override): {transport_url}")
        if "localhost" in transport_url or "127.0.0.1" in transport_url:
            logger.warning(f"Transport URL contains localhost: {transport_url}")
            logger.warning(f"Overriding transport URL with: {AGENT_URL}")
            client._transport.url = AGENT_URL
            logger.info(f"Transport URL (after override): {client._transport.url}")
    return client


class A2AClientWrapper:
    """
    Reusable A2A client wrapper that forwards authentication tokens.

    This class provides a convenient interface for creating A2A clients that
    automatically forward authentication tokens from incoming requests to
    A2A endpoints.

    Example:
        ```python
        # Extract token from FastAPI request
        auth_header = request.headers.get("Authorization")
        token = auth_header.replace("Bearer ", "") if auth_header else None

        # Create client with token forwarding
        async with httpx.AsyncClient() as httpx_client:
            a2a_client = A2AClientWrapper.create(
                httpx_client=httpx_client,
                agent_url="http://localhost:5001/a2a/",
                token=token
            )

            # Send a message
            message = Message(
                role="user",
                parts=[{"kind": "text", "text": "Hello!"}]
            )
            async for response in a2a_client.send_message(message):
                print(response)
        ```
    """

    def __init__(
        self,
        client: Client,
        httpx_client: httpx.AsyncClient,
    ):
        """
        Initialize the A2A client wrapper.

        Args:
            client: The underlying A2A client
            httpx_client: The httpx client used for HTTP requests
        """
        self._client = client
        self._httpx_client = httpx_client

    @classmethod
    async def create(
        cls,
        httpx_client: httpx.AsyncClient,
        token: Optional[str] = None,
        config: Optional[ClientConfig] = None,
        timeout: Optional[float] = None,
    ) -> "A2AClientWrapper":
        """
        Create a new A2A client wrapper.

        Args:
            httpx_client: The httpx async client to use for HTTP requests
            token: Optional bearer token to forward (without 'Bearer ' prefix)
            config: Optional client configuration
            timeout: Optional timeout in seconds for requests (default: None uses httpx_client's timeout)

        Returns:
            An A2AClientWrapper instance

        Raises:
            Exception: If the agent card cannot be resolved or client creation fails
        """
        # Create default config if not provided
        if config is None:
            config = ClientConfig(httpx_client=httpx_client)

        # Update httpx_client timeout if provided
        if timeout is not None:
            httpx_client.timeout = httpx.Timeout(timeout, connect=10.0)


        # Prepare resolver HTTP kwargs with Authorization header for agent card resolution
        resolver_http_kwargs: dict[str, Any] = {}
        if token:
            resolver_http_kwargs["headers"] = {
                "Authorization": f"Bearer {token}"
            }

        # Create client using ClientFactory
        logger.info(f"Creating A2A client for agent URL: {AGENT_URL}")
        try:
            client = await ClientFactory.connect(
                agent=AGENT_URL,
                client_config=config,
                resolver_http_kwargs=resolver_http_kwargs if resolver_http_kwargs else None,
            )

            # client = override_agent_card_url(client)
        except Exception as e:
            logger.error(f"Failed to create A2A client: {e}")
            logger.error(f"Agent URL: {AGENT_URL}")
            raise

        return cls(client, httpx_client)

    async def send_message(
        self,
        message: Message,
        thread_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ):
        """
        Send a message to the A2A agent.

        Args:
            message: The message to send
            thread_id: Optional thread ID for conversation continuity
            message_id: Optional message ID (auto-generated if not provided)

        Yields:
            Response events (Task, Message, or update events) from the agent
        """
        # Generate message ID if not provided
        if message_id is None:
            message_id = uuid4().hex

        # Log before sending
        try:
            card = await self._client.get_card()
            logger.info(f"Sending message to agent at URL: {card.url}")
        except Exception:
            pass  # Ignore errors when fetching card for logging

        # Send message and yield responses
        # The client.send_message expects a Message object directly
        try:
            async for response in self._client.send_message(message):
                yield response
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            # Try to get more info about the URL being used
            try:
                card = await self._client.get_card()
                logger.error(f"Agent card URL when error occurred: {card.url}")
            except Exception:
                pass
            raise

    async def get_card(self) -> AgentCard:
        """
        Get the agent card.

        Returns:
            The agent's card
        """
        return await self._client.get_card()

    async def close(self):
        """
        Close the underlying A2A client.

        Note: The httpx_client is not closed here as it may be managed
        externally (e.g., in a context manager). The caller should manage
        the httpx_client lifecycle separately.
        """
        await self._client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


def find_agent_details(agent_name: str, registry_path: str = None) -> dict[str, Any]:
    """
    Find the agent details from the agent registry.

    Args:
        agent_name: The name of the agent to find (e.g., "mim", "service_now")
        registry_path: Optional path to the agent registry JSON file

    Returns:
        Dictionary containing agent details with keys:
        - agent: Agent name
        - agent_url: Agent URL
        - is_active: Whether the agent is active
        - inputs: (optional) Sample inputs
        - output: (optional) Sample output

    Raises:
        ValueError: If agent is not found in registry
        FileNotFoundError: If registry file doesn't exist
    """

    # Default to agent_registry.json using importlib.resources for package data
    if registry_path is None:
        try:
            # Use importlib.resources to access package data
            # This works correctly when the package is installed
            registry_file = files('tori_agent.mast_utils').joinpath('agent_registry.json')
            registry_content = registry_file.read_text()
            agent_registry = json.loads(registry_content)
        except Exception as e:
            # Fallback to old method for development/editable installs
            logger.warning(f"Could not load registry using importlib.resources: {e}")
            logger.warning("Falling back to file-based loading")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            registry_path = os.path.join(current_dir, 'agent_registry.json')
            with open(registry_path, 'r') as f:
                agent_registry = json.load(f)
    else:
        # Use provided path
        with open(registry_path, 'r') as f:
            agent_registry = json.load(f)

    # Search through the registry by agent name
    for key, agent_data in agent_registry.items():
        if agent_data.get('agent') == agent_name:
            return agent_data

    # If not found, raise error
    raise ValueError(f"Agent '{agent_name}' not found in registry. Available agents: {[v.get('agent') for v in agent_registry.values()]}")


# Example usage function (for testing)
async def a2a_comm(payload, agent: str, timeout: float = 300.0):
    """
    Example usage of the A2A client wrapper.

    Args:
        payload: Message payload with 'message' containing 'role' and 'parts'
        agent_name: Name of the agent to communicate with (e.g., "mim", "service_now")
        token: Optional bearer token for authentication (if None, uses AzureAuthProvider)
        timeout: Request timeout in seconds (default: 300 seconds / 5 minutes)

    Yields:
        A2A response events (streaming)

    Returns:
        Final output dict containing the agent's response data
    """
    # Get agent details from registry
    agent_details = find_agent_details(agent)

    if not agent_details.get('is_active', False):
        raise ValueError(f"Agent '{agent}' is not active")

    # Create httpx client with longer timeout for A2A requests
    timeout_config = httpx.Timeout(timeout, connect=10.0)

    # Create auth provider instance if token is not provided
    # If token is provided, pass it to A2AClientWrapper.create instead
    auth = AzureAuthProvider()

    async with httpx.AsyncClient(auth=auth, timeout=timeout_config) as httpx_client:
        a2a_client = await A2AClientWrapper.create(
            httpx_client=httpx_client,
            timeout=timeout
        )

        # Create message from payload using helper function
        logger.info(f"Original payload parts: {payload['message']['parts']}")
        message_parts = create_message_parts(payload['message']['parts'])
        logger.info(f"Processed message parts: {message_parts}")

        # Generate message ID (required field)
        message_id = uuid4().hex

        message = Message(
            role=payload['message']['role'],
            parts=message_parts,
            messageId=message_id
        )
        logger.info(f"Created Message object with {len(message_parts)} parts")

        async for response in a2a_client.send_message(message):
            yield response


async def a2a_comm_with_output(payload, agent: str, timeout: float = 300.0):
    """
    Helper function that returns both streaming responses and final output dict.

    Args:
        payload: Message payload with 'message' containing 'role' and 'parts'
        agent: Name of the agent to communicate with
        timeout: Request timeout in seconds

    Returns:
        Tuple of (responses_list, final_output_dict)

    The final_output_dict contains:
        - message_id: The message ID from the task
        - input: The original user input text
        - output: The agent's text response
        - thread_id: The context/thread ID
        - messages: List of message history with role, message_id, and parts
        - agent_response: The structured data response from the agent
    """
    responses = []
    final_output = {}

    # Extract original input from payload
    original_input = ""
    for part in payload.get('message', {}).get('parts', []):
        if part.get('kind') == 'text' or part.get('type') == 'text':
            original_input = part.get('text', '')
            break

    async for response in a2a_comm(payload, agent, timeout):
        responses.append(response)

        # Response is typically a tuple (Task, None)
        # Extract the Task object
        task = None
        if isinstance(response, tuple):
            task = response[0]
        elif hasattr(response, 'artifacts'):
            task = response

        # Extract data from Task
        if task and hasattr(task, 'artifacts') and task.artifacts:
            # Get message_id and thread_id from task
            message_id = getattr(task, 'id', None)
            thread_id = getattr(task, 'context_id', None)

            # Extract text output and data from artifacts
            text_output = ""
            agent_data = {}

            for artifact in task.artifacts:
                if hasattr(artifact, 'parts') and artifact.parts:
                    for part in artifact.parts:
                        # Check if part has a root attribute (DataPart or TextPart)
                        if hasattr(part, 'root'):
                            root = part.root

                            # Extract text from TextPart
                            if hasattr(root, 'kind') and root.kind == 'text':
                                if hasattr(root, 'text'):
                                    text_output = root.text

                            # Extract data from DataPart
                            elif hasattr(root, 'kind') and root.kind == 'data':
                                if hasattr(root, 'data'):
                                    agent_data = root.data

            # Extract message history from task
            messages = []
            if hasattr(task, 'history') and task.history:
                for msg in task.history:
                    msg_dict = {
                        "role": str(msg.role.value) if hasattr(msg, 'role') else None,
                        "message_id": getattr(msg, 'message_id', None),
                        "parts": []
                    }

                    # Extract parts from message
                    if hasattr(msg, 'parts') and msg.parts:
                        for part in msg.parts:
                            if hasattr(part, 'root'):
                                root = part.root
                                if hasattr(root, 'kind') and root.kind == 'text':
                                    msg_dict['parts'].append({
                                        "kind": "text",
                                        "text": getattr(root, 'text', '')
                                    })
                                elif hasattr(root, 'kind') and root.kind == 'data':
                                    msg_dict['parts'].append({
                                        "kind": "data",
                                        "data": getattr(root, 'data', {})
                                    })

                    messages.append(msg_dict)

            # Build the complete output dict
            final_output = {
                "message_id": message_id,
                "input": original_input,
                "output": text_output,
                "thread_id": thread_id,
                "messages": messages
            }

            # Merge agent_data into final_output
            # If agent_data has 'agent_response', add it at top level
            # Otherwise, merge all fields from agent_data
            if 'agent_response' in agent_data:
                final_output['agent_response'] = agent_data['agent_response']
            else:
                final_output.update(agent_data)

    return responses, final_output


async def main():
    send_message_payload = {
        'message': {
            'role': 'user',
            'parts': [
                {'kind': 'text', 'text': 'I want to raise an incident'},
                # {'kind': 'json', 'data': {'ticket_id': '12345', 'priority': 'high'}, 'name': 'form_filled_values'}
            ],
        }
    }

    # Option 1: Get both streaming responses AND final output dict
    print("=== Option 1: Using helper function to get all responses + final output ===")
    responses, final_output = await a2a_comm_with_output(send_message_payload, "mim")
    print(f"Total responses received: {len(responses)}")
    print(f"Final Output Dict: {final_output}")

    # print("\n=== Option 2: Stream responses in real-time (original behavior) ===")
    # # Option 2: Just stream responses (if you only need streaming)
    # async for response in a2a_comm(send_message_payload, "mim"):
    #     print(f"Streaming Response: {response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
