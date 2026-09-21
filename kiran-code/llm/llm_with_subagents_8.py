"""LLM configuration that exposes the isolated subagent task."""

from . import config
from .llm_with_todo_5 import SYSTEM_PROMPT as TODO_SYSTEM_PROMPT
from .llm_with_todo_5 import call_llm as _call_llm
from tools.tools_with_subagents_5 import TOOL_SCHEMAS


SYSTEM_PROMPT = TODO_SYSTEM_PROMPT + """

For repository investigation, delegate a focused, read-only question to the
task subagent when that is more efficient than exploring everything yourself.
Give task a standalone description with the exact paths or symbols to inspect.
The subagent reports findings only; you remain responsible for all edits.
"""


def call_llm(messages, tools=None):
    """Call the existing client with the subagent-enabled tool schema."""
    return _call_llm(messages, tools=tools or TOOL_SCHEMAS)
