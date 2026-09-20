"""UI variant with a human approval prompt for permission checks."""

from prompt_toolkit import prompt

from .ui import UI


class HITLUI(UI):
    """Reuse the normal UI and add human-in-the-loop approval."""

    def approve(self, reason: str) -> bool:
        self.console.print()
        self.console.print(f"Permission required: {reason}", style="bold #e0af68")
        try:
            answer = prompt("Allow? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer in {"y", "yes"}


ui = HITLUI()
