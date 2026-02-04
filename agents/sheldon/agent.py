# code of agent one
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


from core.model import MASTOpenAIModel

#########  AI MODEL #########
model = MASTOpenAIModel.get_model("gpt-4o")


#########  DATA MODEL  ##############
class AnswerAgentOut(BaseModel):
    output: str = Field(description="output of the message")
    justification: str = Field(description="justification for the output")


#########  AGENTS  ##############
def answer_agent(state) -> dict[str, Any]:
    print("Invoking answer agent")
    question = state["input"]
    structured_llm = model.with_structured_output(AnswerAgentOut)

    system_prompt = """You are a helpful assistant named Sheldon. You know about everything in this world and can answer questions."""
    user_prompt = """{question}"""

    # Prompt
    _prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )

    agent = _prompt | structured_llm

    response = agent.invoke({"question": question})
    return {"output": response.output, "justification": response.justification}

