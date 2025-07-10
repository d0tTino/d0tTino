"""Echo recipe plug-in."""
from llm.backends.plugin_sdk import register_recipe

def run(goal: str):
    """Return a command that echoes the goal."""
    return [f"echo {goal}"]

register_recipe("echo", run)

__all__ = ["run"]
