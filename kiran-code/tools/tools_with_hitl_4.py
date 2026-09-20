"""Permission-aware execution for the TODO/edit tools."""

import json

from permissions.permissions import check
from ui.ui_with_hitl import ui

from .tools_with_edit_and_todos_3 import TOOLS


def execute(tool_call):
    """Validate, optionally approve, and execute one model tool call."""
    name = tool_call.function.name

    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as error:
        return {}, f"Error: tool arguments were not valid JSON: {error}"

    if name not in TOOLS:
        return args, f"Error: no tool named '{name}'. Available: {', '.join(TOOLS)}."

    try:
        action, reason = check(name, args)
        if action == "deny":
            return args, f"Blocked by permission policy: {reason}"
        if action == "ask" and not ui.approve(reason or f"run {name}"):
            return args, "Denied by user."
        return args, str(TOOLS[name](**args))
    except Exception as error:  # return failures to the model as tool output
        return args, f"Error: {type(error).__name__}: {error}"
