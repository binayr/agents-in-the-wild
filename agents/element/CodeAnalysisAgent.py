import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from core.model import AzureOpenAIModel
from agents.element.PromptTemplate import SP_ANALYSIS_SYS_PROMPT, CODE_ANALYSIS_SYS_PROMPT


logger = logging.getLogger(__name__)
model = AzureOpenAIModel.get_model("o1")


# Data model
class AnalysisOut(BaseModel):
    explanation: str = Field(
        description="SP explained with details."
    )


# LLM with function call
structured_model = model.with_structured_output(AnalysisOut)

# Prompt
sp_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SP_ANALYSIS_SYS_PROMPT),
        ("human", "SQL stored procedure: ```{stored_procedure}```")
    ]
)

code_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CODE_ANALYSIS_SYS_PROMPT),
        ("human", "Java Sringboot Code: ```{code}```")
    ]
)

sp_analysis_agent = sp_prompt | structured_model
code_analysis_agent = code_prompt | structured_model

