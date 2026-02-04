import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List

from core.model import AzureOpenAIModel
from agents.element.PromptTemplate import EVALUATION_SYS_PROMPT, EVALUATION_USER_PROMPT

logger = logging.getLogger(__name__)
model = AzureOpenAIModel.get_model("gpt-5-mini")


# Data model
class EvaluationOut(BaseModel):
    improvements: List[str] = Field(
        description="converted code improvements."
    )
    score: float = Field(
        description="conversion success score."
    )
    reason: str = Field(
        description="Reson behind the score."
    )


# LLM with function call
structured_model = model.with_structured_output(EvaluationOut)

# Prompt
_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", EVALUATION_SYS_PROMPT),
        ("human", EVALUATION_USER_PROMPT),
    ]
)

evaluation_agent = _prompt | structured_model


def evaluate(state):
    input_code = state["input_code"]
    converted_files = state["converted_files"]
    logger.info("🔍 Starting Evaluation ...")
    result = evaluation_agent.invoke({"converted_code": converted_files, "input_code": input_code})
    logger.info("✅ Evaluation Completed ...")
    logger.info(f"🎯 Score: {result.score}")
    return {
        "improvements": result.improvements,
        "score": result.score,
        "reason": result.reason
    }