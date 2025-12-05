from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class FlowGraph:
    nodes: Dict[str, dict]
    edges: Dict[str, List[str]]

class Memory(dict):
    """
    Simple dict-based memory store for ChainChart execution.
    Can later be replaced with SpoonOS memory.
    """
    pass

def build_flowgraph(diagram_json: dict) -> FlowGraph:
    nodes = {node["id"]: node for node in diagram_json["nodes"]}
    edges: Dict[str, List[str]] = {}
    for edge in diagram_json["edges"]:
        edges.setdefault(edge["from"], []).append(edge["to"])
    return FlowGraph(nodes=nodes, edges=edges)

