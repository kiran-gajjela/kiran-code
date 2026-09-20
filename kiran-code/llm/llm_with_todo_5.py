import json
import os
import time

from openai import OpenAI
from skills.skills import skills_prompt
from tools.tools_with_edit_and_todos_3 import TOOL_SCHEMAS, TOOLS

try:
    from . import config
except ImportError:
    import config


client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)

SYSTEM_PROMPT = f"""
You are a coding agent. Your job is to code. Always code.
Use bash to inspect files, write_file to create files, and str_replace to edit
existing files.

For any task that takes more than one step, call write_todos first. Send the
whole list every time; it replaces the previous list. Keep exactly one task
in_progress, mark it done immediately when finished, and move the next task
to in_progress in the same call. Skip todos for a single-step task.

The current todo list is injected on every turn inside <todos> tags.
The current working directory is: {os.getcwd()}

If a skill matches the user's task, call read_skill first and follow it.
Available skills:
{skills_prompt()}
"""


def call_llm(messages, tools=None):
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
        tools=tools or TOOL_SCHEMAS,
    )
    elapsed = time.perf_counter() - start
    message = response.choices[0].message
    usage_data = response.usage
    completion_details = getattr(usage_data, "completion_tokens_details", None)
    prompt_details = getattr(usage_data, "prompt_tokens_details", None)
    usage = {
        "model": config.MODEL,
        "prompt_tokens": getattr(usage_data, "prompt_tokens", 0),
        "completion_tokens": getattr(usage_data, "completion_tokens", 0),
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
        "cached_tokens": getattr(prompt_details, "cached_tokens", None),
        "total_time_seconds": round(elapsed, 3),
    }
    return message, usage


if __name__ == "__main__":
    user_input = input("Enter your prompt> ")
    message, usage = call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ])
    print("\nAgent:", message.content or "")
    print(usage)
