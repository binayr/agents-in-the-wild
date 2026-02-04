import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from core.model import AzureOpenAIModel
from agents.element.PromptTemplate import SCHEMA_PROMPT


logger = logging.getLogger(__name__)
model = AzureOpenAIModel.get_model("o1")


# Data model
class EntityOut(BaseModel):
    code: str = Field(
        description="User and AI conversation history, summarized for a meaningful response."
    )


# LLM with function call
structured_llm_grader = model.with_structured_output(EntityOut)

# Prompt
_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SCHEMA_PROMPT),
        ("human", "{schema_name}\n\n{schema}"),
    ]
)

schema_agent = _prompt | structured_llm_grader
