import os
from typing import Optional


class Config:
    # Embedding settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

    # Vector database settings
    VECTOR_DIR: str = os.getenv("VECTOR_DIR", "/app/chroma")

    # LLM settings - Support for OpenRouter
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL_NAME: str = os.getenv(
        "OPENROUTER_MODEL_NAME", "google/gemini-2.5-flash"
    )
    OPENROUTER_API_BASE: str = os.getenv(
        "OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"
    )

    # Backward compatibility with existing environment variables
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "")

    # Auto-configure for OpenRouter if OpenRouter variables are set
    @property
    def API_BASE(self) -> str:
        # Prioritize OpenRouter, fallback to OpenAI
        if self.OPENROUTER_API_BASE:
            return self.OPENROUTER_API_BASE
        return self.OPENAI_API_BASE

    @property
    def API_KEY(self) -> str:
        # Prioritize OpenRouter, fallback to OpenAI
        if self.OPENROUTER_API_KEY:
            return self.OPENROUTER_API_KEY
        return self.OPENAI_API_KEY

    @property
    def MODEL(self) -> str:
        # Prioritize OpenRouter, fallback to OpenAI
        if self.OPENROUTER_MODEL_NAME:
            return self.OPENROUTER_MODEL_NAME
        elif self.OPENAI_MODEL:
            return self.OPENAI_MODEL
        # Default to Gemini if no model specified
        return "google/gemini-2.5-flash"

    # Retrieval settings
    TOP_K: int = int(os.getenv("TOP_K", "4"))
    MAX_CHUNK_CHARS: int = int(os.getenv("MAX_CHUNK_CHARS", "1024"))

    # LLM generation settings
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "800"))

    # Data paths
    DATA_DIR: str = "data"

    # Document sources
    DOCUMENT_SOURCES = [
        "ai_test_bug_report.txt",
        "ai_test_user_feedback.txt",
    ]

    def get_api_config(self) -> dict:
        """Get API configuration with proper headers for OpenRouter."""
        config = {
            "api_base": self.API_BASE,
            "api_key": self.API_KEY,
            "model": self.MODEL,
        }

        # # Add OpenRouter specific headers
        # if self.OPENROUTER_API_KEY and self.OPENROUTER_API_BASE:
        #     config["headers"] = {
        #         "HTTP-Referer": "https://your-domain.com",  # Replace with your domain
        #         "X-Title": "Internal AI Assistant",
        #     }

        return config


config = Config()
