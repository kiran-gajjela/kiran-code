"""Summarize old conversation history when the context grows too large."""

from history.history import estimate, strip
from llm import config
from llm.llm_with_todo_5 import client


CONTEXT_WINDOW = config.CONTEXT_WINDOW
COMPACT_AT = config.COMPACT_AT
COMPACT_TO = config.COMPACT_TO

SYSTEM_PROMPT = """
You are compacting the transcript of a coding session. Write a precise handoff
note that lets a fresh agent continue without rereading the removed messages.

Use these sections when relevant:
## Goal
## What happened
## Files
## State
## Next

Include real paths, function names, errors, decisions, and unfinished work.
Never invent progress. Do not add a preamble or sign-off.
"""

HANDOFF = """<summary>
Everything before this point was compacted to free context space. Treat this
note as the working memory of the session.

{summary}
</summary>"""

ROLES = {"user": "USER", "assistant": "ASSISTANT", "tool": "TOOL RESULT"}


def needed(usage: dict) -> bool:
    """Return whether the latest request crossed the compaction threshold."""
    return usage.get("prompt_tokens", 0) > CONTEXT_WINDOW * COMPACT_AT


def render(messages: list[dict]) -> str:
    """Flatten messages into text for the summarizer."""
    lines = []
    for message in messages:
        if message.get("role") == "system":
            continue

        content = message.get("content") or ""
        for call in message.get("tool_calls") or []:
            function = call.get("function", {})
            content += f"\n[called {function.get('name')}: {function.get('arguments')}]"
        lines.append(f"{ROLES.get(message.get('role'), message.get('role'))}: {content}")
    return "\n\n".join(lines)


def summarize(messages: list[dict]) -> str:
    """Ask the model for a handoff note without exposing tools."""
    response = client.chat.completions.create(
        model=config.MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": render(messages)},
        ],
    )
    return response.choices[0].message.content or "No summary was produced."


def safe_boundary(messages: list[dict], start: int) -> int:
    """Find a cut point that does not separate tool calls from their results."""
    for index in range(max(start, 1), len(messages)):
        previous = messages[index - 1]
        if messages[index].get("role") == "tool" or previous.get("tool_calls"):
            continue
        return index
    return len(messages)


def tail_start(messages: list[dict], budget: int) -> int:
    """Find where the recent tail should begin."""
    total = 0
    for index in range(len(messages) - 1, 0, -1):
        total += estimate([messages[index]])
        if total > budget:
            return safe_boundary(messages, index)
    return safe_boundary(messages, 1)


def compact(messages: list[dict]) -> list[dict]:
    """Replace old messages with a summary and retain a recent tail."""
    cut = tail_start(messages, int(CONTEXT_WINDOW * COMPACT_TO))
    if cut <= 1:
        return messages

    summary = summarize(messages[1:cut])
    kept = [
        messages[0],
        {"role": "user", "content": HANDOFF.format(summary=summary)},
        *messages[cut:],
    ]
    strip(kept)
    return kept
