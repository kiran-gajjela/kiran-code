"""Terminal presentation layer for the Kiran coding agent."""

import json
from contextlib import contextmanager

from prompt_toolkit import prompt
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text


ACCENT = "#7aa2f7"
USER = "#9ece6a"
TOOL = "#e0af68"
MUTED = "#565f89"
MAX_TOOL_OUTPUT_LINES = 12


class UI:
    def __init__(self):
        self.console = Console()
        self._totals = {}

    def banner(self):
        self.console.print()
        self.console.print(
            Rule(Text(" kiran coding agent ", style=f"bold {ACCENT}"), style=MUTED)
        )
        self.console.print(
            Padding(
                Text("ctrl-d to exit", style=MUTED),
                (0, 0, 0, 2),
            )
        )

    def ask(self):
        try:
            return prompt("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return ""

    def user(self, text):
        self.console.print(
            Padding(Text(text.strip(), style=f"bold {USER}"), (1, 0, 0, 2))
        )

    def agent(self, text):
        self.console.print(
            Padding(
                Group(
                    Text("agent", style=f"bold {ACCENT}"),
                    Padding(Markdown(text.strip()), (1, 0, 0, 0)),
                ),
                (1, 2, 0, 2),
            )
        )

    def tool(self, name, args, result):
        lines = str(result).strip().splitlines() or ["(no output)"]
        shown = lines[:MAX_TOOL_OUTPUT_LINES]
        body = "\n".join(shown)
        if len(lines) > MAX_TOOL_OUTPUT_LINES:
            body += f"\n... {len(lines) - MAX_TOOL_OUTPUT_LINES} more lines"

        header = Text.assemble(
            (f"{name} ", f"bold {TOOL}"),
            (self._format_args(args), MUTED),
        )
        self.console.print(
            Padding(
                Panel(
                    Group(header, Rule(style=MUTED), Text(body, style=MUTED)),
                    border_style=MUTED,
                    padding=(0, 1),
                ),
                (1, 2, 0, 2),
            )
        )

    @contextmanager
    def working(self):
        with self.console.status(
            Text("thinking", style=MUTED),
            spinner="dots",
            spinner_style=ACCENT,
        ):
            yield

    def usage(self, stats):
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                self._totals[key] = self._totals.get(key, 0) + (value or 0)

        parts = []
        for key, value in stats.items():
            if value is not None and not isinstance(value, str):
                parts.append(f"{key.replace('_', ' ')}: {value}")
        self.console.print(Padding(Text(" · ".join(parts), style=MUTED), (1, 0, 0, 2)))

    def summary(self):
        if self._totals:
            values = " · ".join(
                f"{key.replace('_', ' ')}: {value}"
                for key, value in self._totals.items()
            )
            self.console.print(Padding(Text(values, style=MUTED), (1, 2)))
        self.console.print(Rule(style=MUTED))

    @staticmethod
    def _format_args(args):
        if len(args) == 1:
            return str(next(iter(args.values())))
        return json.dumps(args)

    def injection(self, text):
        self.console.print(
            Padding(
                Panel(
                    Text(text.strip(), style=MUTED),
                    title=Text("late injection", style=f"italic {MUTED}"),
                    title_align="left",
                    border_style=MUTED,
                    padding=(0, 1),
                ),
                (1, 2, 0, 2),
            )
        )


ui = UI()
