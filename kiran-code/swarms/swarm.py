"""Parallel, isolated, read-only repository explorers."""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from history import history


MAX_WORKERS = int(os.getenv("SWARM_MAX_WORKERS", "2"))
MAX_TASKS = int(os.getenv("SWARM_MAX_TASKS", "3"))
MAX_TURNS = int(os.getenv("SWARM_MAX_TURNS", "4"))
ALLOWED_TOOLS = {"bash", "read_file", "read_skill"}

SYSTEM_PROMPT = f"""
You are one worker in a read-only repository investigation swarm.
Your working directory is {os.getcwd()}.

Answer only the assigned investigation question. You have no memory of the
lead agent or other workers. Inspect files and report concrete findings with
relative paths and function names. Do not edit, create, delete, or rename
files. Do not create TODOs and do not delegate work.

Prefer read_file when an exact path is provided. On Windows, do not use Unix
shell syntax such as `ls -la`, `/c/...`, or `&&`. If bash is needed, restrict
it to safe read-only inspection. Stop as soon as you can answer. Return a
concise report, ideally under 150 words.
"""


def toolset() -> list[dict]:
    """Expose only read-only schemas; workers cannot spawn or edit."""
    from tools.tools_with_edit_and_todos_3 import TOOL_SCHEMAS

    return [
        schema
        for schema in TOOL_SCHEMAS
        if schema["function"]["name"] in ALLOWED_TOOLS
    ]


def _inside_project(path: str) -> bool:
    project = Path.cwd().resolve()
    resolved = Path(path).expanduser().resolve()
    return resolved == project or project in resolved.parents


def execute_readonly(tool_call) -> tuple[dict, str]:
    """Run a worker tool call without UI prompts or write capability."""
    from permissions.permissions import check
    from tools.tools_with_edit_and_todos_3 import TOOLS

    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as error:
        return {}, f"Error: tool arguments were not valid JSON: {error}"

    if not isinstance(args, dict):
        return {}, "Error: tool arguments must be a JSON object."
    if name not in ALLOWED_TOOLS:
        return args, f"Blocked: swarm workers cannot use '{name}'."

    if name == "read_file":
        path = args.get("path")
        if not isinstance(path, str) or not path:
            return args, "Error: read_file requires a path."
        if not _inside_project(path):
            return args, f"Blocked: read_file must stay inside the project: {path}"

    if name == "bash":
        action, reason = check(name, args)
        if action != "allow":
            return args, (
                "Blocked: swarm bash commands must be pre-approved read-only "
                f"commands ({reason}). Use read_file or a safer inspection command."
            )

    try:
        return args, str(TOOLS[name](**args))
    except Exception as error:  # workers receive failures as evidence and can retry
        return args, f"Error: {name} failed: {type(error).__name__}: {error}"


def worker(description: str) -> str:
    """Run one bounded, isolated worker and return its final report only."""
    from llm.llm_with_todo_5 import call_llm

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]
    report = None

    for _ in range(MAX_TURNS):
        history.fit(messages, 12_000)
        message, _usage = call_llm(messages, tools=toolset())
        messages.append(message.model_dump(exclude_none=True))
        report = message.content or report

        if not message.tool_calls:
            return report or "(worker returned no findings)"

        for tool_call in message.tool_calls:
            _args, result = execute_readonly(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": history.cap(result),
                }
            )

    if report:
        return f"(worker stopped after {MAX_TURNS} turns)\n{report}"
    return f"(worker stopped after {MAX_TURNS} turns with no findings)"


def swarm(tasks: list[str], max_workers: int | None = None) -> str:
    """Explore independent questions concurrently and combine their reports."""
    clean_tasks = [task.strip() for task in tasks if isinstance(task, str) and task.strip()]
    if not clean_tasks:
        return "Error: swarm needs at least one non-empty task."
    if len(clean_tasks) > MAX_TASKS:
        return f"Error: swarm accepts at most {MAX_TASKS} tasks."

    workers = max_workers if isinstance(max_workers, int) else MAX_WORKERS
    workers = max(1, min(workers, MAX_WORKERS, len(clean_tasks)))
    reports = ["(worker did not return a report)"] * len(clean_tasks)

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="swarm") as pool:
        futures = {
            pool.submit(worker, description): index
            for index, description in enumerate(clean_tasks)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                reports[index] = future.result()
            except Exception as error:  # one worker must not fail the swarm
                reports[index] = f"Error: worker failed: {type(error).__name__}: {error}"

    blocks = []
    for index, (description, report) in enumerate(zip(clean_tasks, reports), start=1):
        blocks.append(f"## Worker {index}\nTask: {description}\nReport: {report}")
    return "\n\n".join(blocks)


SWARM_SCHEMA = {
    "type": "function",
    "function": {
        "name": "swarm",
        "description": (
            "Delegate two or three independent, read-only repository questions "
            "to isolated workers that explore concurrently. Returns one report "
            "per worker. Use for parallel investigation; do edits yourself."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "description": "Independent, self-contained investigation questions.",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 3,
                },
                "max_workers": {
                    "type": "integer",
                    "description": "Optional concurrent-worker limit, from 1 to 2.",
                    "minimum": 1,
                    "maximum": 2,
                },
            },
            "required": ["tasks"],
        },
    },
}
