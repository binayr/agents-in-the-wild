import os
from dotenv import load_dotenv

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_VERSION")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
EMBEDDING_OPENAI_API_BASE = os.getenv("EMBEDDING_OPENAI_API_BASE")
EMBEDDING_OPENAI_API_KEY = os.getenv("EMBEDDING_OPENAI_API_KEY")
EMBEDDING_OPENAI_API_VERSION = os.getenv("EMBEDDING_OPENAI_API_VERSION")


collection_count = os.getenv("COLLECTION_COUNT")
collection_name = os.getenv("COLLECTION_NAME")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_endpoint = os.getenv("QDRANT_ENDPOINT")
vector_name = os.getenv("VECTOR_NAME")