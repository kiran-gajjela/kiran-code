"""Tool adapter that adds parallel read-only swarm exploration."""

import json

from rich.text import Text

from swarms.swarm import SWARM_SCHEMA, swarm
from .tools_with_subagents_5 import TOOL_SCHEMAS as SUBAGENT_SCHEMAS
from .tools_with_subagents_5 import execute as execute_with_subagent


TOOL_SCHEMAS = [*SUBAGENT_SCHEMAS, SWARM_SCHEMA]


def execute(tool_call):
    """Execute existing tools or run a bounded parallel swarm."""
    if tool_call.function.name != "swarm":
        return execute_with_subagent(tool_call)

    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as error:
        return {}, f"Error: swarm arguments were not valid JSON: {error}"

    tasks = args.get("tasks") if isinstance(args, dict) else None
    if not isinstance(tasks, list):
        return args if isinstance(args, dict) else {}, "Error: swarm requires a tasks array."

    max_workers = args.get("max_workers")
    if max_workers is not None and (
        not isinstance(max_workers, int) or isinstance(max_workers, bool)
    ):
        return args, "Error: max_workers must be an integer."

    from ui.ui_with_hitl import ui

    ui.console.print(Text(f"[swarm] exploring {len(tasks)} task(s)", style="italic #565f89"))
    with ui.working():
        return args, swarm(tasks, max_workers=max_workers)
