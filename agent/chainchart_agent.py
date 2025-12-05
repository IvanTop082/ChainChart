import os
from typing import Dict, Any, List
from spoon_ai.agents import SpoonReactAI
from spoon_ai.chat import ChatBot

from .chainchart_tools import ReadNeoStateTool, CallNeoContractTool, OperationTool, DebugLogTool
from .flowgraph import FlowGraph, Memory, build_flowgraph
from .chainchart_executor import execute_node

class ChainChartAgent:
    """
    Phase 2 Complete Execution Layer:
    - Loads FlowGraph
    - Holds Memory
    - Executes nodes in order
    - Produces full execution trace
    """

    def __init__(self):
        llm = ChatBot(
            llm_provider=os.getenv("LLM_PROVIDER") or "gemini",
            model_name=os.getenv("LLM_MODEL") or "gemini-2.5-pro",
            temperature=0,
        )

        tools = [
            ReadNeoStateTool(),
            CallNeoContractTool(),
            OperationTool(),
            DebugLogTool(),
        ]

        self.agent = SpoonReactAI(
            llm=llm,
            tools=tools,
        )

        # Create tool registry for run_tool() method
        self.tool_registry = {tool.name: tool for tool in tools}
        
        self.memory = Memory()

    async def run_tool(self, tool_name: str, params: dict):
        """Execute a tool by name with given parameters."""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Call tool's execute method with unpacked parameters
        return await tool.execute(**params)

    async def run_workflow(self, diagram_json: Dict[str, Any]) -> Dict[str, Any]:
        graph: FlowGraph = build_flowgraph(diagram_json)
        current = list(graph.nodes.keys())[0]
        logs: List[Dict[str, Any]] = []
        step = 0

        while current:
            step += 1
            node = graph.nodes[current]
            result = await execute_node(self, node, self.memory)
            logs.append({
                "step": step,
                "node": current,
                "type": node["type"],
                "result": result,
                "memory": dict(self.memory)
            })

            next_nodes = graph.edges.get(current, [])
            if not next_nodes:
                break
            current = next_nodes[0]

        return {
            "execution_logs": logs,
            "final_memory": dict(self.memory),
        }
