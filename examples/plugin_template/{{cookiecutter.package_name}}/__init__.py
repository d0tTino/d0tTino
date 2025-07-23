"""{{ cookiecutter.description }}"""

{%- if cookiecutter.plugin_type == 'backend' %}
from llm.backends.plugin_sdk import register_backend


def run(prompt: str, model: str | None = None) -> str:
    """Generate a completion for the given prompt."""
    return "response"

register_backend("{{ cookiecutter.plugin_name }}", run)
{%- else %}
from llm.backends.plugin_sdk import register_recipe


def run(goal: str):
    """Return shell commands for the given goal."""
    return [f"echo {goal}"]

register_recipe("{{ cookiecutter.plugin_name }}", run)
{%- endif %}

__all__ = ["run"]
