"""Tool adapter that adds the isolated read-only subagent task."""

import json

from subagents.subagent import TASK_SCHEMA, task
from .tools_with_edit_and_todos_3 import TOOL_SCHEMAS as BASE_SCHEMAS
from .tools_with_hitl_4 import execute as execute_with_hitl


TOOL_SCHEMAS = [*BASE_SCHEMAS, TASK_SCHEMA]


def execute(tool_call):
    """Execute a normal HITL tool or delegate a task to a subagent."""
    if tool_call.function.name != "task":
        return execute_with_hitl(tool_call)

    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as error:
        return {}, f"Error: task arguments were not valid JSON: {error}"

    description = args.get("description")
    if not isinstance(description, str) or not description.strip():
        return args, "Error: task requires a non-empty description."

    try:
        return args, task(description)
    except Exception as error:  # return failures to the lead agent
        return args, f"Error: subagent failed: {type(error).__name__}: {error}"


def execute_subagent(tool_call):
    """Execute only the read-only tools exposed to a subagent."""
    if tool_call.function.name not in {"bash", "read_file", "read_skill"}:
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}
        return args, f"Blocked: subagents cannot use '{tool_call.function.name}'."
    return execute_with_hitl(tool_call)
