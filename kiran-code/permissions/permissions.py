"""Decide whether a tool call is allowed, needs approval, or is denied.

This module only makes a decision. The caller is responsible for enforcing it
and, for an ``ask`` result, requesting approval from the user.
"""

from fnmatch import fnmatch
from pathlib import Path


PROJECT = Path.cwd().resolve()

# The first matching rule wins only after all matching rules are evaluated;
# therefore the final matching rule has precedence.
BASH_RULES = {
    "*": "ask",
    # Read-only commands.
    "ls*": "allow",
    "pwd": "allow",
    "cd *": "allow",
    "echo *": "allow",
    "sort*": "allow",
    "uniq*": "allow",
    "cut *": "allow",
    "basename *": "allow",
    "dirname *": "allow",
    "date*": "allow",
    "env": "allow",
    "cat *": "allow",
    "head *": "allow",
    "tail *": "allow",
    "wc *": "allow",
    "file *": "allow",
    "which *": "allow",
    "grep *": "allow",
    "rg *": "allow",
    "find *": "allow",
    "tree*": "allow",
    "git status*": "allow",
    "git diff*": "allow",
    "git log*": "allow",
    "git show*": "allow",
    "git ls-files*": "allow",
    "pytest*": "allow",
    "python -m pytest*": "allow",
    # Never allow these commands through the permission layer.
    "rm *": "deny",
    "sudo *": "deny",
    "chmod *": "deny",
    "chown *": "deny",
    "curl *": "deny",
    "wget *": "deny",
    "git push*": "deny",
    "git reset*": "deny",
    "git clean*": "deny",
}


def split_command(command: str) -> list[str]:
    """Split shell commands without splitting separators inside quotes."""
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    index = 0

    while index < len(command):
        char = command[index]
        if quote:
            current.append(char)
            if char == quote:
                quote = None
        elif char == "\\":
            current.append(char)
            index += 1
            if index < len(command):
                current.append(command[index])
        elif char in "\"'":
            quote = char
            current.append(char)
        elif char in "&|;":
            parts.append("".join(current))
            current = []
            while index + 1 < len(command) and command[index + 1] in "&|":
                index += 1
        else:
            current.append(char)
        index += 1

    parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def decide(command: str) -> str:
    """Return ``allow``, ``ask``, or ``deny`` for a shell command."""
    verdicts = []
    for part in split_command(command):
        action = "ask"
        for pattern, rule in BASH_RULES.items():
            if fnmatch(part, pattern):
                action = rule
        verdicts.append(action)

    if "deny" in verdicts:
        return "deny"
    if "ask" in verdicts:
        return "ask"
    return "allow"


def inside_project(path: str | Path) -> bool:
    """Return whether a path is inside the project directory."""
    resolved = Path(path).expanduser().resolve()
    return resolved == PROJECT or PROJECT in resolved.parents


def check(name: str, args: dict) -> tuple[str, str | None]:
    """Return ``(action, reason)`` for a tool call."""
    if name == "bash":
        command = args.get("command", "")
        return decide(command), f"run: {command}"

    if name in {"write_file", "str_replace"}:
        path = args.get("path", "")
        if not inside_project(path):
            return "ask", f"{name} outside {PROJECT}: {path}"

    return "allow", None
