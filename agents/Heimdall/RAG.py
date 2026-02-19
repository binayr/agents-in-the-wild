import json
import logging
import qdrant_client
from typing import Any, Dict, List
from core.config import collection_count, collection_name, qdrant_api_key, qdrant_endpoint, vector_name
from core.model import AzureOpenAIModel
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder


logger = logging.getLogger(__name__)


# Qdrant client setup
client = qdrant_client.QdrantClient(url=qdrant_endpoint, api_key=qdrant_api_key, timeout=60)  # Reduced timeout
aclient = qdrant_client.AsyncQdrantClient(url=qdrant_endpoint, api_key=qdrant_api_key, timeout=60)

# Create embedding model
embedding_llm = AzureOpenAIModel.get_embedding_model()
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

async def _internal_rag_search_with_context(query: str) -> List[Document]:
    logger.info(f"--- RAG: Performing enhanced search with context reconstruction for query: {query}")

    # Generate embeddings for the query
    vector = embedding_llm.embed_query(query)

    # Perform initial search using named vector
    points = await aclient.query_points(
        collection_name=collection_name,
        with_vectors=False,
        with_payload=True,
        query=vector,
        using=vector_name,
        limit=collection_count
    )

    docs = []
    for point in points.points:
        doc = point.dict()
        node = json.loads(doc["payload"]["_node_content"])
        doc = Document(page_content=node["text"], metadata=node["metadata"])
        docs.append(doc)
    return docs


def rerank(query, documents, top_k=5):
   if not documents:
      return []

   pairs = [(query, doc.page_content) for doc in documents]
   scores = reranker.predict(pairs)
   # attach scores
   scored_docs = list(zip(documents, scores))
   # sort descending
   scored_docs.sort(key=lambda x: x[1], reverse=True)
   # return top_k
   return [doc for doc, score in scored_docs[:top_k]]


async def simple_rag_search(state) -> Dict[str, Any]:
    logger.info("------------------------Simple RAG Search-------------------------")

    question = state.get("input")
    intent = state.get("intent", [])

    query = f"Main query: {question}\nUser Intent: {intent}"

    logger.info(f"Query: {query}")
    try:
        docs = await _internal_rag_search_with_context(query)
        reranked_docs = rerank(query, docs, top_k=8)
    except Exception as e:
        logger.error(f"Error during RAG search: {e}", exc_info=True)
        docs = []
    documents = [{"content": doc.page_content, "metadata": doc.metadata} for doc in reranked_docs]
    return {"documents": documents}

