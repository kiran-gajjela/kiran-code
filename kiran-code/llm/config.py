"""Configuration for the OpenAI-compatible LLM endpoint."""

import os


BASE_URL = os.getenv("BASE_URL", "http://localhost:11434/v1/")
API_KEY = os.getenv("API_KEY", "ollama")
MODEL = os.getenv("MODEL", "qwen3.5:0.8b")
