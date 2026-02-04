import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from core.model import AzureOpenAIModel
from agents.element.PromptTemplate import POM_CREATION_SYS_PROMPT


logger = logging.getLogger(__name__)
model = AzureOpenAIModel.get_model("o1")


class POMOut(BaseModel):
    """Schema for the POM.xml generation output."""
    code: str = Field(description="The Maven POM.xml content")

    class Config:
        """Configuration for this pydantic object."""
        extra = "forbid"  # This sets additionalProperties to false


# LLM with function call
structured_model = model.with_structured_output(POMOut)

# Prompt
_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", POM_CREATION_SYS_PROMPT),
        ("user", "Code: ```{code}```")
    ]
)

pom_agent = _prompt | structured_model

