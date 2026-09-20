import json
import os
import subprocess
import time

from openai import OpenAI

from . import config

client = OpenAI(
    base_url=config.BASE_URL,
    api_key=config.API_KEY,
)

SYSTEM_PROMPT = f"""
You are a coding agent focused on implementing solutions. 
Prioritize writing clear, effective code for every task.
Use the bash tool to inspect files.
"""

BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a PowerShell command and return its combined stdout and stderr.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run",
                }
            },
            "required": ["command"],
        },
    },
}


def bash(command):
    """Run a shell command and return its combined stdout and stderr"""
    if os.name == "nt":
        #If it is windows
        result = subprocess.run(
            ["powershell.exe", command],
            capture_output=True,
            text=True,
        )
    else:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

    return result.stdout + result.stderr


TOOLS = {
    "bash": bash,
}


def call_llm(messages, tools=None):

    start_time = time.perf_counter()

    response = client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
        tools=tools or [BASH_TOOL],
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
