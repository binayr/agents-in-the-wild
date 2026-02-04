import logging
from langchain_core.prompts import ChatPromptTemplate

from core.model import AzureOpenAIModel
from agents.element.PromptTemplate import (
    SP_CONVERSION_SYS_PROMPT,
    SP_CONVERSION_USER_PROMPT,
    SP_CONVERSION_SYS_PROMPT_FLASK,
    SP_CONVERSION_SYS_PROMPT_FASTAPI,
)

logger = logging.getLogger(__name__)
model = AzureOpenAIModel.get_model("gpt-5-mini")


def _resolve_system_prompt(target_framework: str | None) -> str:
    if not target_framework:
        return SP_CONVERSION_SYS_PROMPT
    key = target_framework.strip().lower()
    if key in ("java", "springboot", "java/springboot"):
        return SP_CONVERSION_SYS_PROMPT
    if key in ("python/flask", "flask"):
        return SP_CONVERSION_SYS_PROMPT_FLASK
    if key in ("python/fastapi", "fastapi"):
        return SP_CONVERSION_SYS_PROMPT_FASTAPI
    # Default to Java/Spring Boot if unknown
    return SP_CONVERSION_SYS_PROMPT


def get_conversion_chain(target_framework: str | None = None):
    system_prompt = _resolve_system_prompt(target_framework)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", SP_CONVERSION_USER_PROMPT),
        ]
    )
    return prompt | model


# Backward-compatible default agent using Java/Spring Boot
conversion_agent = get_conversion_chain("java/springboot")

