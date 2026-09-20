import json
import os
import subprocess
import time

from openai import OpenAI
from skills.skills import skills_prompt
from tools.tools_with_skills_2 import TOOL_SCHEMAS
try:
    from . import config
except ImportError:
    import config

client = OpenAI(
    base_url=config.BASE_URL,
    api_key=config.API_KEY,
)

SYSTEM_PROMPT = f"""
You are a coding agent focused on implementing solutions. 
Prioritize writing clear, effective code for every task.
Use the bash tool to inspect files.

Your current working directory is: {os.getcwd()}

You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it.

{skills_prompt()}
"""


def bash(command):
    """Run a shell command and return its combined stdout and stderr"""
    if os.name == "nt":
        #If it is windows
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
        )
    else:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

    return result.stdout + result.stderr


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    with open(path) as f:
        return f.read()

TOOLS = {
    "bash": bash,
    "read_file":read_file
}


def call_llm(messages, tools=None):

    start_time = time.perf_counter()

    response = client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
        tools=tools or TOOL_SCHEMAS,
    )

    total_time_seconds = time.perf_counter() - start_time

    message = response.choices[0].message

    completion_details = response.usage.completion_tokens_details
    prompt_details = response.usage.prompt_tokens_details

    usage = {
        "model": config.MODEL,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
        "cached_tokens": getattr(prompt_details, "cached_tokens", None),
        "total_time_seconds": round(total_time_seconds, 3),
    }

    return message, usage


if __name__ == "__main__":
    user_input = input("Enter your prompt> ")

    message, usage = call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ])

    print("\nAgent: ", message.content, "\n")

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

    print(usage)
