import subprocess
import os

from skills.skills import read_skill

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



TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return its combined stdout and stderr.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_skill",
            "description": "Open a skill by name and return its full instructions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the skill to open",
                    }
                },
                "required": ["name"],
            },
        },
    },
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "read_skill": read_skill,
}

