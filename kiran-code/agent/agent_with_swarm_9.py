"""Kiran agent entry point with subagents and parallel swarm exploration."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compact import compact
from context.context_with_todo_2 import reminder
from history import history
from llm import config
from llm.llm_with_swarm_9 import SYSTEM_PROMPT, call_llm
from tools.tools_with_swarm_6 import TOOL_SCHEMAS, execute
from ui.ui_with_hitl import ui


def run_turn(messages: list[dict]) -> dict:
    usage = {}
    for _ in range(config.MAX_TOOL_ROUNDS):
        injection = reminder()
        ui.injection(injection["content"])
        history.fit(messages, int(compact.CONTEXT_WINDOW * compact.COMPACT_AT))

        with ui.working():
            message, usage = call_llm(messages + [injection], tools=TOOL_SCHEMAS)

        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)
        if message.content:
            ui.agent(message.content)
        if not message.tool_calls:
            return usage

        for tool_call in message.tool_calls:
            args, result = execute(tool_call)
            result = history.cap(result)
            ui.tool(tool_call.function.name, args, result)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return usage


def main():
    ui.banner()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = ui.ask()
        if not user_input:
            break

        ui.user(user_input)
        messages.append({"role": "user", "content": user_input})
        usage = run_turn(messages)

        history.sweep()
        history.strip(messages)
        if compact.needed(usage):
            with ui.compacting():
                messages = compact.compact(messages)

    ui.summary()


if __name__ == "__main__":
    main()
