"""
ContractGenerateTool - Extract structure from ChainChart diagram
"""

from spoon_ai.tools.base import BaseTool
from typing import Dict, Any, List


class ContractGenerateTool(BaseTool):
    """
    Extract variables, events, functions, and logic from ChainChart JSON.
    This tool does NOT write C# code - it only returns structured data.
    """
    
    name: str = "generate_contract_structure"
    description: str = "Extract variables, events, functions, and logic from ChainChart JSON"
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "diagram": {
                "type": "object",
                "description": "ChainChart diagram containing nodes and edges"
            }
        },
        "required": ["diagram"]
    }
    
    async def execute(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse ChainChart diagram and extract contract structure.
        
        Returns:
            {
                "variables": [...],  # State nodes → storage variables
                "functions": [...],  # Function nodes → function signatures
                "events": [...],     # Event nodes → event declarations
                "operations": [...], # Operation nodes → arithmetic/logic
                "conditions": [...], # Condition nodes → if logic
                "edges": [...],      # Control flow edges
                "nodes": [...]       # All nodes with metadata
            }
        """
        nodes = diagram.get("nodes", [])
        edges = diagram.get("edges", [])
        
        variables = []
        functions = []
        events = []
        operations = []
        conditions = []
        modifiers = []
        
        # Parse nodes by type
        for node in nodes:
            node_type = node.get("type")
            node_data = node.get("data", {})
            node_id = node.get("id")
            
            if node_type == "state":
                # State node → storage variable
                label = node_data.get("label", f"state_{node_id}")
                data_type = node_data.get("dataType", "BigInteger")
                visibility = node_data.get("visibility", "public")
                
                variables.append({
                    "id": node_id,
                    "name": label,
                    "type": data_type,
                    "visibility": visibility,
                    "value": node_data.get("value", ""),
                    "node": node
                })
            
            elif node_type == "function":
                # Function node → function signature
                name = node_data.get("name", f"function_{node_id}")
                params = node_data.get("params", [])
                visibility = node_data.get("visibility", "public")
                payable = node_data.get("payable", False)
                
                # Parse params string if it's a string
                if isinstance(params, str):
                    params = [p.strip() for p in params.split(",") if p.strip()]
                elif not isinstance(params, list):
                    params = []
                
                functions.append({
                    "id": node_id,
                    "name": name,
                    "parameters": params,
                    "visibility": visibility,
                    "payable": payable,
                    "node": node
                })
            
            elif node_type == "event":
                # Event node → Neo N3 event declaration
                name = node_data.get("name", f"Event_{node_id}")
                params = node_data.get("params", "")
                
                events.append({
                    "id": node_id,
                    "name": name,
                    "parameters": params,
                    "node": node
                })
            
            elif node_type == "operation":
                # Operation node → arithmetic or logical expression
                op = node_data.get("op", "add")
                a = node_data.get("a", "")
                b = node_data.get("b")
                
                operations.append({
                    "id": node_id,
                    "operation": op,
                    "operand_a": a,
                    "operand_b": b,
                    "node": node
                })
            
            elif node_type == "condition":
                # Condition node → if logic
                expression = node_data.get("expression", "true")
                
                conditions.append({
                    "id": node_id,
                    "expression": expression,
                    "node": node
                })
            
            elif node_type == "modifier":
                # Modifier node → access control
                name = node_data.get("name", f"modifier_{node_id}")
                expression = node_data.get("expression", "true")
                
                modifiers.append({
                    "id": node_id,
                    "name": name,
                    "expression": expression,
                    "node": node
                })
        
        # Process edges to understand control flow
        processed_edges = []
        for edge in edges:
            from_node = edge.get("from", "")
            to_node = edge.get("to", "")
            
            # Find source and target node types
            source_node = next((n for n in nodes if n.get("id") == from_node), None)
            target_node = next((n for n in nodes if n.get("id") == to_node), None)
            
            processed_edges.append({
                "from": from_node,
                "to": to_node,
                "from_type": source_node.get("type") if source_node else None,
                "to_type": target_node.get("type") if target_node else None,
                "edge": edge
            })
        
        return {
            "variables": variables,
            "functions": functions,
            "events": events,
            "operations": operations,
            "conditions": conditions,
            "modifiers": modifiers,
            "edges": processed_edges,
            "nodes": nodes
        }


