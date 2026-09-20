"""Kiran TODO agent with human approval for permission-sensitive tools."""

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from context.context_with_todo_2 import reminder
from llm.llm_with_todo_5 import SYSTEM_PROMPT, call_llm
from tools.tools_with_hitl_4 import execute
from ui.ui_with_hitl import ui


def main():
    ui.banner()
    user_input = ui.ask()
    if not user_input:
        ui.summary()
        return

    ui.user(user_input)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    while True:
        injection = reminder()
        ui.injection(injection["content"])

        with ui.working():
            message, usage = call_llm(messages + [injection])

        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)

        if message.content:
            ui.agent(message.content)

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            args, result = execute(tool_call)
            ui.tool(tool_call.function.name, args, result)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    ui.summary()


if __name__ == "__main__":
    main()
