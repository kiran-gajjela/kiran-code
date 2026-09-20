import time

from openai import OpenAI

from . import config


client = OpenAI(
    base_url=config.BASE_URL,
    api_key=config.API_KEY,
)

SYSTEM_PROMPT = f"""
You are a coding agent focused on implementing solutions. Prioritize writing clear, effective code for every task.
"""


def call_llm(messages):
    start_time = time.perf_counter()

    response = client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
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

    print(usage)
