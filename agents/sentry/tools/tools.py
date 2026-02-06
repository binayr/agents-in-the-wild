from typing import Any

from langchain_core.tools import tool


#########  Tools  ##############
@tool
def create_ticket(action: str) -> dict[str, Any]:
    """
    Take an action based on the user's intention in question.
    """
    print(">>>>>>>>>>>>>>>>>>>>>>>> Create ticket Tool Called >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(f"Taking action: {action}")
    return {"action": action, "status": "success"}


@tool
def find_form(action: str) -> dict[str, Any]:
    """
    Find the correct form and send to user.
    """
    print(">>>>>>>>>>>>>>>>>>>>>>>> Find form Tool Called >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(f"Taking action: {action}")
    return {"name": "form name", "region": "us-east-1"}


@tool
def classify_incident_severity(action: str) -> dict[str, Any]:
    """
    Classify the incident severity based on the user's input.
    """
    print(
        ">>>>>>>>>>>>>>>>>>>>>>>> classify incident severity Tool Called >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    )
    print(f"Taking action: {action}")
    return {"severity": "P1"}
