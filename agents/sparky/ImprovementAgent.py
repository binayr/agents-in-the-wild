import logging
from langchain_core.prompts import ChatPromptTemplate
from core.model import AzureOpenAIModel
from agents.sparky.PyConverterAgent import OutFiles
from agents.sparky.prompts import IMPROVEMENT_SYS_PROMPT, IMPROVEMENT_USER_PROMPT

logger = logging.getLogger(__name__)
model = AzureOpenAIModel.get_model("o1")

spark_improvement_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", IMPROVEMENT_SYS_PROMPT),
        ("human", IMPROVEMENT_USER_PROMPT),
    ]
)


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

    logger.info("✅ Improvement Completed ...")
    return {
        "converted_files": result.files,
        "iteration": state["iteration"] + 1
    }






