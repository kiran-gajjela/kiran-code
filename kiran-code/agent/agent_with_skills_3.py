"""Kiran coding agent with the Rich terminal UI."""

import json
import sys
from pathlib import Path


from ui import ui

from llm.llm_with_tools_and_skills_4 import SYSTEM_PROMPT, call_llm
from tools.tools_with_skills_2 import TOOLS


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
    print(messages)

    while True:
        with ui.working():
            message, usage = call_llm(messages)

        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)

        if message.content:
            ui.agent(message.content)

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            tool = TOOLS.get(tool_call.function.name)
            if tool is None:
                result = f"Unknown tool: {tool_call.function.name}"
            else:
                try:
                    result = tool(**args)
                except Exception as exc:
                    result = f"Tool error: {exc}"

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
