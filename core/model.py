"""
model.py - Language model interface for TORI conversational AI system

This module provides a factory class for accessing various Azure OpenAI language models
used throughout the application. It encapsulates model initialization logic, implements
caching for model instances, and provides a consistent interface for obtaining different
model types (chat models and embeddings).

The module relies on configuration parameters imported from the config module and
supports multiple Azure OpenAI models including o1, o1-mini, gpt-4o, and gpt-4o-mini.
"""

import logging
import random

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from core.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_VERSION,
    EMBEDDING_OPENAI_API_BASE,
    EMBEDDING_OPENAI_API_KEY,
    EMBEDDING_OPENAI_API_VERSION,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MASTOpenAIModel:
    """
    Factory class for accessing various language models used by the TORI system.

    This class provides static methods to initialize different Azure OpenAI models
    with appropriate configuration parameters. It serves as a centralized access
    point for all language model interactions in the application and implements
    caching to avoid recreating model instances unnecessarily.

    Attributes:
        _model_cache (dict): Internal cache of model instances indexed by model name
    """

    @staticmethod
    def get_model(model: str) -> AzureChatOpenAI | AzureOpenAIEmbeddings:
        """
        Factory method to get the appropriate language model instance based on model name.
        Uses caching to avoid recreating model instances for better performance.

        Args:
            model (str, optional): The model identifier. Supported values are:
                                   "o1", "o1-mini", "gpt-4o", "gpt-4o-mini", "embedding".
                                   Defaults to "o1".

        Returns:
            LangChain model instance: Initialized model for use in the application

        Raises:
            ValueError: When an unsupported model name is provided
        """
        return AzureChatOpenAI(
            openai_api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            openai_api_version=AZURE_OPENAI_VERSION,
            deployment_name=model,
        )

    @staticmethod
    def get_embedding_model(model: str) -> AzureOpenAIEmbeddings:
        """
        Initialize and return an Azure OpenAI embedding model.

        Returns:
            AzureOpenAIEmbeddings: Initialized embedding model instance
        """
        # Create embedding model
        # verbose not supported for this model
        embedding_llm = AzureOpenAIEmbeddings(
            azure_deployment=model,
            azure_endpoint=EMBEDDING_OPENAI_API_BASE,
            openai_api_version=EMBEDDING_OPENAI_API_VERSION,
            openai_api_key=EMBEDDING_OPENAI_API_KEY,
            openai_api_base=None,
            chunk_size=1,
        )
        return embedding_llm
