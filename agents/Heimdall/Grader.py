import asyncio
import logging
from core.model import AzureOpenAIModel
from agents.Heimdall.prompt import GRADER_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

# Data model
class GradeDocuments(BaseModel):
    """
    Binary scoring model for document relevance check.

    Attributes:
        binary_score (str): "yes" if document is relevant to question, "no" otherwise
    """

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )
    absolute_score: float = Field(
        description="Absolute score of the document relevance, 0.0 to 1.0"
    )
    reasoning: str = Field(
        description="Reasoning for the relevance score"
    )


grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", GRADER_PROMPT),
        ("human", "User question: {messages}\n\n User's intent: {intent} \n\n Retrieved document: \n\n {document}"),

    ]
)

async def grade_single_document(query, document, intent):
    model = AzureOpenAIModel.get_model("gpt-4.1")
    structured_llm_grader = model.with_structured_output(GradeDocuments)
    retrieval_grader = grade_prompt | structured_llm_grader

    logger.info(f"------------------------Grade Single Document------------------------")
    score = await retrieval_grader.ainvoke(
        {"messages": query, "document": document['content'], "intent": intent}
    )
    return (document, score)


async def grade_documents(state):
    logger.info("------------------------CHECK DOCUMENT RELEVANCE TO QUESTION------------------------")
    logger.info(state)
    documents = state["documents"]
    query = state["input"]
    intent = state.get("intent", "")

    tasks = []
    for doc in documents:
        tasks.append(grade_single_document(query, doc, intent))

    # Wait for all grading tasks to complete
    results = await asyncio.gather(*tasks)

    # Filter documents based on grades
    filtered_docs = []
    logger.info(f"--- GRADE: {len(results)} documents to grade")
    for doc, score in results:
        logger.info(f"--- GRADE: Document: {doc}")
        doc_name = doc.get("metadata").get("name", "Unknown")
        if score.binary_score == "yes":
            logger.info("--"*10)
            logger.info(f"--- GRADE: DOCUMENT {doc_name}, RELEVANT: {score.absolute_score}")
            logger.info(f"--- GRADE: REASONING: {score.reasoning}")
            filtered_docs.append(doc)
        else:
            logger.info("--"*10)
            logger.info(f"--- GRADE: DOCUMENT {doc_name}, NOT RELEVANT: {score.absolute_score}")
            logger.info(f"--- GRADE: REASONING: {score.reasoning}")

    logger.info(f"--- GRADE: Returning {len(filtered_docs)} relevant documents")
    # logger.info(filtered_docs)
    return {"documents": filtered_docs}