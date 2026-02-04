from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from core.model import AzureOpenAIModel
from agents.element.PromptTemplate import DOCUMENTATION_SYS_PROMPT

model = AzureOpenAIModel.get_model("o1")


# Data model
class OutputFormat(BaseModel):
    documentation: str = Field(
        description="Code documentation with details."
    )


# LLM with function call
structured_model = model.with_structured_output(OutputFormat)

# Prompt
_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", DOCUMENTATION_SYS_PROMPT),
        ("human", "Code: ```{code}```")
    ]
)

code_documentation_agent = _prompt | structured_model

