"""Configuration for the OpenAI-compatible LLM endpoint."""

import os


BASE_URL = os.getenv("BASE_URL", "http://localhost:11434/v1/")
API_KEY = os.getenv("API_KEY", "ollama")
MODEL = os.getenv("MODEL", "qwen3.5:0.8b")

# Conversation history and compaction settings.
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", "2000"))
COMPACT_AT = float(os.getenv("COMPACT_AT", "0.70"))
COMPACT_TO = float(os.getenv("COMPACT_TO", "0.10"))

# Maximum model/tool exchanges allowed for one user turn.
MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "3"))
