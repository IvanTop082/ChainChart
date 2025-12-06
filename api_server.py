"""
FastAPI server for ChainChart backend execution.
Handles workflow execution requests from the UI.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import asyncio

from agent.chainchart_agent import ChainChartAgent

app = FastAPI(title="ChainChart API", version="1.0.0")

# CORS middleware to allow UI to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DiagramRequest(BaseModel):
    """Request model for diagram execution"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class ExecutionResponse(BaseModel):
    """Response model for execution results"""
    execution_logs: List[Dict[str, Any]]
    final_memory: Dict[str, Any]
    success: bool
    error: str = None


def transform_ui_to_backend_format(ui_diagram: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform UI diagram format to backend expected format.
    
    UI Format:
        nodes: [{id, type, label, value, position, metadata}]
        edges: [{from: "nodeId:position", to: "nodeId:position"}]
    
    Backend Format:
        nodes: [{id, type, data: {...}}]
        edges: [{from: "nodeId", to: "nodeId"}]
    """
    transformed_nodes = []
    
    for node in ui_diagram["nodes"]:
        node_type = node["type"]
        node_data = {}
        
        # Transform based on node type
        if node_type == "state":
            # Backend expects "label" as the storage key name
            node_data = {
                "label": node.get("label", "") or "state_" + node["id"]
            }
        elif node_type == "condition":
            node_data = {
                "expression": node.get("metadata", {}).get("expression", "true")
            }
        elif node_type == "operation":
            # Parse operation expression to extract op, a, b
            expr = node.get("value", "").strip()
            node_data = {
                "op": "add",  # Default
                "a": node.get("label", ""),
                "b": node.get("label", "")  # Default to same value for testing
            }
            
            # Simple parsing - can be enhanced
            if "+" in expr or "add" in expr.lower():
                node_data["op"] = "add"
            elif "-" in expr or "sub" in expr.lower() or "subtract" in expr.lower():
                node_data["op"] = "sub"
            elif "*" in expr or "mul" in expr.lower() or "multiply" in expr.lower():
                node_data["op"] = "mul"
            elif "/" in expr or "div" in expr.lower() or "divide" in expr.lower():
                node_data["op"] = "div"
            elif "and" in expr.lower():
                node_data["op"] = "and"
            elif "or" in expr.lower():
                node_data["op"] = "or"
            
            # Extract operands (simple extraction)
            # Look for patterns like "a + b" or "balance += amount"
            expr_clean = expr.replace("+=", "+").replace("-=", "-").replace("*=", "*").replace("/=", "/")
            parts = expr_clean.replace("+", " ").replace("-", " ").replace("*", " ").replace("/", " ").replace("=", " ").split()
            if len(parts) >= 1:
                node_data["a"] = parts[0].strip()
            if len(parts) >= 2:
                node_data["b"] = parts[1].strip()
            else:
                # If no second operand, use same as first (for operations like balance + balance)
                node_data["b"] = node_data["a"]
        elif node_type == "function":
            node_data = {
                "name": node.get("label", "").replace(" ", ""),
                "params": node.get("metadata", {}).get("params", "").split(",") if node.get("metadata", {}).get("params") else []
            }
        elif node_type == "event":
            node_data = {
                "name": node.get("label", "Event")
            }
        elif node_type == "modifier":
            node_data = {
                "name": node.get("label", "Modifier"),
                "expression": node.get("metadata", {}).get("expression", "true")
            }
        
        transformed_nodes.append({
            "id": node["id"],
            "type": node_type,
            "data": node_data
        })
    
    # Transform edges: "nodeId:position" -> "nodeId"
    transformed_edges = []
    for edge in ui_diagram["edges"]:
        from_node = edge["from"].split(":")[0]  # Extract node ID
        to_node = edge["to"].split(":")[0]      # Extract node ID
        
        transformed_edges.append({
            "from": from_node,
            "to": to_node
        })
    
    return {
        "nodes": transformed_nodes,
        "edges": transformed_edges
    }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "ChainChart API"}


@app.post("/execute-chainchart", response_model=ExecutionResponse)
async def execute_chainchart(request: DiagramRequest):
    """
    Execute a ChainChart diagram and return execution trace.
    
    Request body should contain:
        - nodes: array of node objects
        - edges: array of edge objects
    """
    try:
        # Transform UI format to backend format
        ui_diagram = {
            "nodes": request.nodes,
            "edges": request.edges
        }
        
        backend_diagram = transform_ui_to_backend_format(ui_diagram)
        
        # Validate diagram has nodes
        if not backend_diagram["nodes"]:
            raise HTTPException(status_code=400, detail="Diagram must contain at least one node")
        
        # Create agent and execute workflow
        agent = ChainChartAgent()
        result = await agent.run_workflow(backend_diagram)
        
        return ExecutionResponse(
            execution_logs=result["execution_logs"],
            final_memory=result["final_memory"],
            success=True
        )
        
    except Exception as e:
        import traceback
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        return ExecutionResponse(
            execution_logs=[],
            final_memory={},
            success=False,
            error=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

