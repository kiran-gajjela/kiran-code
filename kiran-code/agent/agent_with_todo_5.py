"""Kiran agent with skills, late context injection, edits, and todos."""

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from context.context_with_todo_2 import reminder
from llm.llm_with_todo_5 import SYSTEM_PROMPT, call_llm
from tools.tools_with_edit_and_todos_3 import TOOLS
from ui import ui


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
            try:
                args = json.loads(tool_call.function.arguments)
                tool = TOOLS.get(tool_call.function.name)
                if tool is None:
                    result = f"Unknown tool: {tool_call.function.name}"
                else:
                    result = tool(**args)
            except Exception as exc:
                args = locals().get("args", {})
                result = f"Tool error: {type(exc).__name__}: {exc}"

            ui.tool(tool_call.function.name, args, result)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })

    ui.summary()


if __name__ == "__main__":
    main()
