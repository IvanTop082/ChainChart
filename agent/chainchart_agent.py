from typing import Dict, Any, List
import os

from .chainchart_tools import ReadNeoStateTool, CallNeoContractTool, OperationTool, DebugLogTool
from .flowgraph import FlowGraph, Memory, build_flowgraph
from .chainchart_executor import execute_node

# Debug mode - can be enabled via environment variable
DEBUG = os.getenv("CHAINCHART_DEBUG", "False").lower() == "true"

class ChainChartAgent:
    """
    Phase 2 Complete Execution Layer:
    - Loads FlowGraph
    - Holds Memory
    - Executes nodes in order
    - Produces full execution trace
    - Runs deterministically without LLM dependencies
    """

    def __init__(self, debug: bool = None):
        """
        Initialize ChainChart agent.
        
        Args:
            debug: Enable debug mode (overrides CHAINCHART_DEBUG env var)
        """
        tools = [
            ReadNeoStateTool(),
            CallNeoContractTool(),
            OperationTool(),
            DebugLogTool(),
        ]

        # Create tool registry for direct tool execution
        # No LLM agent needed - we execute tools directly and deterministically
        self.tool_registry = {tool.name: tool for tool in tools}
        
        self.memory = Memory()
        self.debug = debug if debug is not None else DEBUG
        self.debug_logs = []  # Store debug information

    async def run_tool(self, tool_name: str, params: dict):
        """Execute a tool by name with given parameters."""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Call tool's execute method with unpacked parameters
        return await tool.execute(**params)

    async def run_workflow(self, diagram_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow from diagram JSON.
        Returns execution logs, final memory, and optionally debug info.
        """
        if self.debug:
            self.debug_logs = []
            self.debug_logs.append(f"[DEBUG] Starting workflow execution")
            self.debug_logs.append(f"[DEBUG] Diagram nodes: {len(diagram_json.get('nodes', []))}")
            self.debug_logs.append(f"[DEBUG] Diagram edges: {len(diagram_json.get('edges', []))}")
        
        graph: FlowGraph = build_flowgraph(diagram_json)
        current = list(graph.nodes.keys())[0] if graph.nodes else None
        
        if not current:
            raise ValueError("No nodes found in diagram")
        
        logs: List[Dict[str, Any]] = []
        step = 0
        execution_trace = []  # Detailed execution trace for debug mode

        while current:
            step += 1
            node = graph.nodes[current]
            node_type = node["type"]
            node_data = node.get("data", {})
            
            if self.debug:
                self.debug_logs.append(f"[DEBUG] Step {step}: Executing node {current} (type: {node_type})")
                self.debug_logs.append(f"[DEBUG] Node data: {node_data}")
                self.debug_logs.append(f"[DEBUG] Memory before execution: {dict(self.memory)}")
            
            # Execute the node
            result = await execute_node(self, node, self.memory, debug=self.debug)
            
            if self.debug:
                self.debug_logs.append(f"[DEBUG] Node execution result: {result}")
                self.debug_logs.append(f"[DEBUG] Memory after execution: {dict(self.memory)}")
            
            # Build type-specific log entry
            log_entry = {
                "step": step,
                "node": current,  # Node ID
                "type": node_type
            }
            
            # Add type-specific fields
            if node_type == "state":
                log_entry["output"] = result
                log_entry["key"] = node_data.get("label", "")
                if self.debug:
                    self.debug_logs.append(f"[DEBUG] State node: Read value {result} for key '{node_data.get('label', '')}'")
            elif node_type == "function":
                log_entry["output"] = result
                log_entry["method"] = node_data.get("name", "")
                if self.debug:
                    self.debug_logs.append(f"[DEBUG] Function node: Called method '{node_data.get('name', '')}' -> {result}")
            elif node_type == "condition":
                log_entry["result"] = result
                log_entry["expression"] = node_data.get("expression", "")
                if self.debug:
                    self.debug_logs.append(f"[DEBUG] Condition node: Expression '{node_data.get('expression', '')}' -> {result}")
            elif node_type == "operation":
                log_entry["output"] = result
                log_entry["operation"] = node_data.get("op", "")
                if self.debug:
                    self.debug_logs.append(f"[DEBUG] Operation node: {node_data.get('op', '')} -> {result}")
            elif node_type == "event":
                log_entry["emitted"] = node_data.get("name", "")
                log_entry["output"] = result
                if self.debug:
                    self.debug_logs.append(f"[DEBUG] Event node: Emitted '{node_data.get('name', '')}'")
            elif node_type == "modifier":
                log_entry["applied"] = node_data.get("name", "")
                log_entry["output"] = result
                if self.debug:
                    self.debug_logs.append(f"[DEBUG] Modifier node: Applied '{node_data.get('name', '')}'")
            else:
                log_entry["output"] = result
            
            logs.append(log_entry)
            
            # Add to execution trace for debug mode
            if self.debug:
                execution_trace.append({
                    "step": step,
                    "node_id": current,
                    "node_type": node_type,
                    "node_data": node_data,
                    "result": result,
                    "memory_snapshot": dict(self.memory)
                })

            next_nodes = graph.edges.get(current, [])
            if not next_nodes:
                if self.debug:
                    self.debug_logs.append(f"[DEBUG] No more nodes to execute. Workflow complete.")
                break
            current = next_nodes[0]
            if self.debug:
                self.debug_logs.append(f"[DEBUG] Moving to next node: {current}")

        result_dict = {
            "execution_logs": logs,
            "final_memory": dict(self.memory),
        }
        
        # Add debug information if debug mode is enabled
        if self.debug:
            result_dict["execution_trace"] = execution_trace
            result_dict["memory_state"] = dict(self.memory)
            result_dict["logs"] = self.debug_logs
            result_dict["debug_info"] = {
                "total_steps": step,
                "nodes_executed": len(logs),
                "final_memory_keys": list(self.memory.keys()),
                "debug_logs": self.debug_logs
            }
        
        return result_dict
