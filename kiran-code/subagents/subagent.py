"""Fresh, read-only exploration agents for the main Kiran agent."""

import os

from rich.text import Text

from history import history


MAX_TURNS = int(os.getenv("SUBAGENT_MAX_TURNS", "6"))
WITHHELD = {"task", "write_todos", "write_file", "str_replace"}

SYSTEM_PROMPT = f"""
You are a read-only exploration subagent working in {os.getcwd()}.

Answer the lead agent's question by inspecting the repository. Use bash,
read_file, and read_skill when useful. Do not edit files, create files, change
TODOs, or start another subagent. Search inside the current project only.
Stop when you have enough evidence. Your final answer must be concise and
self-contained, including paths and relevant function names.
"""


def toolset():
    """Return only the tools a read-only subagent may see."""
    from tools.tools_with_edit_and_todos_3 import TOOL_SCHEMAS

    return [
        schema
        for schema in TOOL_SCHEMAS
        if schema["function"]["name"] not in WITHHELD
    ]


def task(description: str) -> str:
    """Run an isolated exploration loop and return only its final report."""
    from llm.llm_with_todo_5 import call_llm
    from tools.tools_with_subagents_5 import execute_subagent
    from ui.ui_with_hitl import ui

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]
    report = None

    ui.console.print(Text("[subagent] exploring", style="italic #565f89"))

    for _ in range(MAX_TURNS):
        history.fit(messages, 12000)
        with ui.working():
            message, _usage = call_llm(messages, tools=toolset())

        messages.append(message.model_dump(exclude_none=True))
        report = message.content or report

        if not message.tool_calls:
            return report or "(subagent returned no findings)"

        for tool_call in message.tool_calls:
            args, result = execute_subagent(tool_call)
            result = history.cap(result)
            ui.tool(tool_call.function.name, args, result)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    if report:
        return f"(subagent stopped after {MAX_TURNS} turns)\n\n{report}"
    return f"(subagent stopped after {MAX_TURNS} turns with no findings)"


TASK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "task",
        "description": (
            "Delegate a self-contained read-only repository investigation to a "
            "fresh subagent. It returns only a concise findings report."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": (
                        "A standalone investigation question with the paths, "
                        "symbols, and evidence the report should include."
                    ),
                }
            },
            "required": ["description"],
        },
    },
}
