import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from core.model import AzureOpenAIModel
from agents.element.PromptTemplate import SP_CONVERSION_SYS_PROMPT_V2, SP_CONVERSION_USER_PROMPT_V2, IMPROVEMENT_SYS_PROMPT, IMPROVEMENT_USER_PROMPT


logger = logging.getLogger(__name__)
model = AzureOpenAIModel.get_model("o1")

class OutFile(BaseModel):
    """
    Model representing a converted file output from SQL/Python to PySpark.
    Attributes:
        filepath (str): The path of the converted file
        content (str): The converted PySpark pipeline code content
    """
    filepath: str = Field(
        description="The file path for the converted PySpark code"
    )
    content: str = Field(
        description="The converted PySpark pipeline code content"
    )


class OutFiles(BaseModel):
    files: List[OutFile] = Field(
        description="List of converted files with PySpark pipeline code"
    )


# Prompt
sp_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SP_CONVERSION_SYS_PROMPT_V2),
        ("human", SP_CONVERSION_USER_PROMPT_V2),
    ]
)

spark_improvement_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", IMPROVEMENT_SYS_PROMPT),
        ("human", IMPROVEMENT_USER_PROMPT),
    ]
)

sp_improvement_agent = sp_prompt | model

structure_model = model.with_structured_output(OutFiles)
spark_improvement_agent = spark_improvement_prompt | structure_model

def spark_improve(state):
    input_code = state["input_code"]
    converted_files = state["converted_files"]
    improvements = state["improvements"]
    logger.info("🛠️ Starting Improvement ...")
    logger.info(f"We have {len(improvements)} improvements to apply.")

    # loop to apply max 3 improvements at a time.
    range_value = 7
    for i in range(0, len(improvements), range_value):
        logger.info(f"Applying improvements {i} to {i+range_value}.")
        result = spark_improvement_agent.invoke({
            "input_code": input_code,
            "converted_code": converted_files,
            "improvements": improvements[i:i+range_value]
        })
        converted_files = result.files

    # apply the remaining improvements
    # result = spark_improvement_agent.invoke({
    #     "input_code": input_code,
    #     "converted_code": converted_files,
    #     "improvements": improvements
    # })
    logger.info("✅ Improvement Completed ...")
    return {
        "converted_files": result.files,
        "iteration": state["iteration"] + 1
    }






