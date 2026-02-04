import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List

from config import logger
from core.model import AzureOpenAIModel
from agents.sparky.prompts import (
    CONVERSION_SYS_PROMPT,
    CONVERSION_USER_PROMPT
)


model = AzureOpenAIModel.get_model("o1")

# Data model
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



def get_conversion_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CONVERSION_SYS_PROMPT),
            ("human", CONVERSION_USER_PROMPT),
        ]
    )
    return prompt | model.with_structured_output(OutFiles)


conversion_agent = get_conversion_chain()


def spark_convert(state):
    input_code = state["input_code"]
    logger.info("👨🏻‍💻 Starting Convertion ...")
    converted_files = conversion_agent.invoke({"input_code": input_code})
    logger.info("✅ Conversion Completed ...")
    return {"converted_files": converted_files}


def spark_export(state):
    # Create output directory
    out_path = state["out_path"]
    code = state["converted_files"]
    output_dir = Path(f"../out/{out_path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export files to out/csls directory
    for file in code:
        # Create the full file path
        file_path = output_dir / file.filepath

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file content
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file.content)
            logger.info(f"✅ Exported: {file.filepath} -> {file_path}")
        except Exception as e:
            logger.info(f"❌ Error exporting {file.filepath}: {str(e)}")

    logger.info(f"\n🎉 Successfully exported {len(code)} files to {output_dir.absolute()}")
