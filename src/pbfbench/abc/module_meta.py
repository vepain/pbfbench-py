"""Meta logic on module."""

from pathlib import Path

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.topic.description as abc_topic_desc

PBFBENCH_ROOT = Path(__file__).parent.parent

TOPICS_MODULE_NAME = "topics"


def topic_module_path(topic_name: str) -> Path:
    """Get topic module path."""
    return PBFBENCH_ROOT / TOPICS_MODULE_NAME / topic_name.lower()


def topic_module_path_from_description(topic: abc_topic_desc.Description) -> Path:
    """Get topic module path."""
    return topic_module_path(topic.name())


def tool_module_path(topic_name: str, tool_name: str) -> Path:
    """Get tool module path."""
    return topic_module_path(topic_name) / tool_name.lower()


def tool_module_path_from_descriptions(
    topic: abc_topic_desc.Description,
    tool: abc_tool_desc.Description,
) -> Path:
    """Get tool module path."""
    return tool_module_path(topic.name(), tool.name())


def path_to_python_path(path: Path) -> str:
    """Get python path."""
    return str(path).replace("/", ".")
