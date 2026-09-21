"""Keep tool output and conversation history within manageable limits."""

import json
import tempfile
from pathlib import Path


CAP = 20_000
STUB = 300
TRIMMED = "[output trimmed:"
SUMMARY = "<summary>"
SPILLS: list[Path] = []


def spill(text: str) -> str:
    """Save oversized output temporarily and return its file path."""
    handle = tempfile.NamedTemporaryFile(
        mode="w", prefix="kiran-code-", suffix=".txt", delete=False, encoding="utf-8"
    )
    handle.write(text)
    handle.close()
    path = Path(handle.name)
    SPILLS.append(path)
    return str(path)


def cap(text: str) -> str:
    """Keep tool output bounded while leaving a pointer to the full output."""
    if len(text) <= CAP:
        return text

    try:
        path = spill(text)
    except OSError:
        return text[:CAP] + f"\n\n{TRIMMED} output was truncated.]"

    return (
        text[:CAP]
        + f"\n\n{TRIMMED} {len(text) - CAP} chars were cut. "
        f"The full output is at {path}.]"
    )


def sweep() -> None:
    """Delete temporary files created for the completed turn."""
    for path in SPILLS:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    SPILLS.clear()


def locked(messages: list[dict]) -> int:
    """Return the length of the system/summary prefix that must be preserved."""
    for index in range(len(messages) - 1, -1, -1):
        if SUMMARY in (messages[index].get("content") or ""):
            return index + 1
    return 0


def strip(messages: list[dict]) -> int:
    """Shrink completed tool results while preserving recent context."""
    shrunk = 0
    for message in messages[locked(messages) :]:
        content = message.get("content") or ""
        if message.get("role") != "tool" or TRIMMED in content or len(content) <= STUB:
            continue
        message["content"] = (
            content[:STUB]
            + f"\n\n{TRIMMED} {len(content) - STUB} more chars. "
            "Run the command again if you need them.]"
        )
        shrunk += 1
    return shrunk


def estimate(messages: list[dict]) -> int:
    """Return a rough token estimate for a message list."""
    return sum(len(json.dumps(message, default=str)) for message in messages) // 4


def fit(messages: list[dict], budget: int) -> int:
    """Drop oldest tool results until the message list fits the budget."""
    dropped = 0
    for message in messages[locked(messages) :]:
        if estimate(messages) <= budget:
            break
        if message.get("role") == "tool" and TRIMMED not in (message.get("content") or ""):
            message["content"] = f"{TRIMMED} dropped to fit the context window.]"
            dropped += 1
    return dropped
