import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from core.model import AzureOpenAIModel
from agents.element.PromptTemplate import IDENTIFICATION_SYS_PROMPT, IDENTIFICATION_USER_PROMPT


logger = logging.getLogger(__name__)
model = AzureOpenAIModel.get_model("gpt-4o")


# Data model
class IdentifyOut(BaseModel):
    entities: List[str] = Field(
        description="Depenent Entities."
    )
    functions: List[str] = Field(
        description="Dependent Functions."
    )
    triggers: List[str] = Field(
        description="Dependent Triggers."
    )
    internal_stored_procedures: List[str] = Field(
        description="Dependent Internal Stored Procedures."
    )


# LLM with function call
structured_model = model.with_structured_output(IdentifyOut)

# Prompt
_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", IDENTIFICATION_SYS_PROMPT),
        ("human", IDENTIFICATION_USER_PROMPT),
    ]
)

identification_agent = _prompt | structured_model

