"""LLM wrapper that exposes individual subagents and parallel swarms."""

from .llm_with_subagents_8 import SYSTEM_PROMPT as SUBAGENT_SYSTEM_PROMPT
from .llm_with_todo_5 import call_llm as _call_llm
from tools.tools_with_swarm_6 import TOOL_SCHEMAS


SYSTEM_PROMPT = SUBAGENT_SYSTEM_PROMPT + """

For two or three independent repository investigations, call swarm once with
one standalone question per worker. Workers are read-only and cannot edit or
delegate. Use task for one focused investigation; use swarm only when parallel
reports are genuinely useful. You must combine their findings and make any
edits yourself.
"""


def call_llm(messages, tools=None):
    """Call the existing client with all swarm-enabled tools."""
    return _call_llm(messages, tools=tools or TOOL_SCHEMAS)
