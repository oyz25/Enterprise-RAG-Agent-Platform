from typing import Dict, Any, List
from app.tools.base import BaseTool


class ToolRegistry:
    """
    Central registry for registering, discovering, and executing agent tools.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool):
        """
        Register a tool instance in the registry.
        """
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """
        Retrieve a registered tool by name.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def list_tools(self) -> List[Dict[str, str]]:
        """
        List metadata for all registered tools.
        """
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a registered tool by name with keyword arguments.
        """
        tool = self.get_tool(name)
        return tool.execute(**kwargs)