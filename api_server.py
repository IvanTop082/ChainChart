"""
FastAPI server for ChainChart backend execution.
Handles workflow execution requests from the UI.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio

from agent.chainchart_agent import ChainChartAgent
from agent.contract_agent import ContractAgent
from agent.tools.contract_compile_tool import ContractCompileTool
from agent.tools.contract_deploy_tool import ContractDeployTool
from generator.neo_contract_generator import generate_contract_from_diagram
from generator.neo_compiler import compile_contract as compile_neo_contract, read_compiled_files
from generator.neo_deploy import deploy_to_testnet
from generator.contract_validator import validate_contract, patch_contract
import tempfile
import os
import json
import shutil
import sys
import base64
from pathlib import Path as PathLib

# Load .env file at startup (before Supabase import so env vars are available)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables only

# Add lib directory to path for Supabase helper
sys.path.insert(0, str(PathLib(__file__).parent))
try:
    from lib.supabase_contracts import (
        save_contract_to_supabase,
        get_latest_contract_for_user,
        get_contract_from_supabase,
        update_contract_deployment
    )
    # Test if Supabase client can be created (check env vars)
    from lib.supabase_contracts import get_supabase_client
    client = get_supabase_client()
    if client:
        SUPABASE_AVAILABLE = True
        print("✅ Supabase connected successfully")
    else:
        SUPABASE_AVAILABLE = False
        print("⚠️ Supabase not available - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) must be set in .env file")
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase not available - import failed: {e}")
    print("   Install with: pip install supabase")
except Exception as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase not available - error: {e}")

app = FastAPI(title="ChainChart API", version="1.0.0")

# CORS middleware to allow UI to connect
# Allow all localhost ports for development (more flexible)
# Note: FastAPI's CORSMiddleware supports allow_origin_regex for regex patterns
import re

app.add_middleware(
    CORSMiddleware,
    # Use regex pattern to allow any localhost port (Bug 1 fix: regex patterns now work correctly)
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    # Also allow specific common ports as exact matches
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated_contracts directory for frontend to fetch NEF/manifest files
generated_contracts_dir = Path("generated_contracts")
generated_contracts_dir.mkdir(exist_ok=True)

@app.get("/generated_contracts/{filename}")
async def get_generated_file(filename: str):
    """Serve files from generated_contracts directory"""
    file_path = generated_contracts_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail=f"{filename} is not a file")
    # Security: ensure file is within generated_contracts directory
    try:
        file_path.resolve().relative_to(generated_contracts_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(str(file_path))


@app.get("/api/contract/latest")
async def get_latest_contract(user_id: Optional[str] = None, project_id: Optional[str] = None):
    """
    Get the latest generated NEF and manifest files.
    Returns both as base64-encoded NEF and JSON manifest.
    Tries Supabase first, falls back to local filesystem.
    """
    import base64
    import os
    
    # Try Supabase first if user_id is provided
    if SUPABASE_AVAILABLE and user_id:
        try:
            contract_data = await get_latest_contract_for_user(
                user_id=user_id,
                project_id=project_id
            )
            if contract_data:
                nef_bytes = contract_data.get("nef_data")
                manifest_data = contract_data.get("manifest_data")
                if nef_bytes and manifest_data:
                    return {
                        "nef": base64.b64encode(nef_bytes).decode('utf-8'),
                        "manifest": manifest_data,
                        "contract_name": contract_data.get("contract_name"),
                        "source": "supabase"
                    }
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to fetch from Supabase: {e}, falling back to local filesystem")
    
    # Fallback to local filesystem
    nef_path = generated_contracts_dir / "contract.nef"
    manifest_path = generated_contracts_dir / "contract.manifest.json"
    
    # Resolve to absolute paths
    abs_nef_path = nef_path.resolve()
    abs_manifest_path = manifest_path.resolve()
    
    # Check if directory exists
    if not generated_contracts_dir.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Generated contracts directory not found at: {generated_contracts_dir.resolve()}. Please generate a contract first using the /export-contract endpoint."
        )
    
    # Check if files exist with helpful error messages
    if not nef_path.exists():
        # List what files are in the directory for debugging
        existing_files = list(generated_contracts_dir.glob("*")) if generated_contracts_dir.exists() else []
        file_list = ", ".join([f.name for f in existing_files[:5]]) if existing_files else "none"
        raise HTTPException(
            status_code=404, 
            detail=f"NEF file not found at: {abs_nef_path}. Please click 'Generate Smart Contract' first. Existing files in directory: {file_list}"
        )
    
    if not manifest_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Manifest file not found at: {abs_manifest_path}. Please click 'Generate Smart Contract' first."
        )
    
    try:
        # Read NEF file and encode as base64
        with open(nef_path, 'rb') as f:
            nef_bytes = f.read()
            if len(nef_bytes) == 0:
                raise HTTPException(status_code=500, detail="NEF file is empty. Contract compilation may have failed.")
            nef_base64 = base64.b64encode(nef_bytes).decode('utf-8')
        
        # Read manifest file as JSON
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_json = json.load(f)
        
        return {
            "nefBase64": nef_base64,
            "manifest": manifest_json,
            "success": True,
            "source": "filesystem"
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse manifest JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read contract files: {str(e)}")


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
    # Debug fields (optional, only present if debug mode enabled)
    execution_trace: List[Dict[str, Any]] = None
    memory_state: Dict[str, Any] = None
    logs: List[str] = None
    debug_info: Dict[str, Any] = None


class ContractGenerateRequest(BaseModel):
    """Request model for contract generation"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    user_id: Optional[str] = None  # User ID for Supabase storage
    project_id: Optional[str] = None  # Project ID to associate contract with


class ContractGenerateResponse(BaseModel):
    """Response model for contract generation"""
    contract_text: str
    success: bool
    error: str = None


class ContractCompileRequest(BaseModel):
    """Request model for contract compilation"""
    contract_text: str


class ContractCompileResponse(BaseModel):
    """Response model for contract compilation"""
    contract: str
    nef: str
    manifest: Dict[str, Any]
    success: bool
    compile_errors: List[str] = []
    error: str = None
    mock: bool = False




class ContractDeployRequest(BaseModel):
    """Request model for contract deployment"""
    nef: str = None  # Base64 encoded NEF (optional, will read from disk if not provided)
    manifest: Dict[str, Any] = None  # Manifest JSON (optional, will read from disk if not provided)
    private_key: str = None  # Optional private key for signing
    contract_id: Optional[str] = None  # Supabase contract ID (will fetch from Supabase if provided)
    user_id: Optional[str] = None  # User ID for Supabase lookup
    project_id: Optional[str] = None  # Project ID for Supabase lookup (optional)


class ContractDeployResponse(BaseModel):
    """Response model for contract deployment"""
    tx_hash: Optional[str] = None
    contract_hash: Optional[str] = None  # Contract hash (0x...)
    success: bool
    error: Optional[str] = None
    mock: bool = False


class ExportContractResponse(BaseModel):
    """Response model for contract export (contract + manifest + NEF)"""
    contract: str
    manifest: Dict[str, Any]
    nef: str
    success: bool
    error: Optional[str] = None
    nef_path: Optional[str] = None  # Path to saved NEF file
    manifest_path: Optional[str] = None  # Path to saved manifest file
    contract_path: Optional[str] = None  # Path to saved C# contract file
    contract_id: Optional[str] = None  # Supabase contract ID
    compile_warning: Optional[str] = None  # Warning message if compiler not installed
    
    model_config = {
        "validate_assignment": True,
    }


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
            metadata = node.get("metadata", {})
            
            # Try to get operands from metadata first (if UI provides them)
            operand_a = metadata.get("operand_a") or metadata.get("a")
            operand_b = metadata.get("operand_b") or metadata.get("b")
            op_from_metadata = metadata.get("op")
            
            node_data = {
                "op": "add",  # Default
                "a": operand_a or "",
                "b": operand_b
            }
            
            # Use operation from metadata if provided
            if op_from_metadata:
                node_data["op"] = op_from_metadata.lower()
            
            # If no operands in metadata, try to parse from expression
            if not operand_a and expr:
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
                
                # Extract operands from expression
                # Look for patterns like "a + b" or "balance += amount"
                expr_clean = expr.replace("+=", "+").replace("-=", "-").replace("*=", "*").replace("/=", "/")
                parts = expr_clean.replace("+", " ").replace("-", " ").replace("*", " ").replace("/", " ").replace("=", " ").split()
                if len(parts) >= 1:
                    node_data["a"] = parts[0].strip()
                if len(parts) >= 2:
                    node_data["b"] = parts[1].strip()
                elif not node_data["b"]:
                    # If no second operand, use same as first (for operations like balance + balance)
                    node_data["b"] = node_data["a"]
            
            # If still no operand_a, use label as fallback (but this will likely cause an error)
            if not node_data["a"]:
                node_data["a"] = node.get("label", "")
        elif node_type == "function":
            # Handle params - can be string or list
            params = node.get("metadata", {}).get("params", [])
            if isinstance(params, str):
                params = [p.strip() for p in params.split(",") if p.strip()]
            elif not isinstance(params, list):
                params = []
            
            node_data = {
                "name": node.get("label", "").replace(" ", ""),
                "params": params
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
    """Root endpoint"""
    return {"status": "ok", "service": "ChainChart API"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify system status.
    
    Returns:
        - status: "ok" if healthy
        - agent_loaded: True if ChainChartAgent can be instantiated
        - neo_tools_loaded: True if Neo tools are available
    """
    try:
        # Check if ChainChartAgent can be instantiated
        agent_loaded = False
        try:
            agent = ChainChartAgent()
            agent_loaded = True
        except Exception as e:
            pass
        
        # Check if Neo tools are available
        neo_tools_loaded = False
        try:
            from agent.chainchart_tools import ReadNeoStateTool, CallNeoContractTool
            neo_tools_loaded = True
        except Exception as e:
            pass
        
        return {
            "status": "ok",
            "agent_loaded": agent_loaded,
            "neo_tools_loaded": neo_tools_loaded
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "agent_loaded": False,
            "neo_tools_loaded": False
        }


@app.post("/execute-chainchart", response_model=ExecutionResponse)
async def execute_chainchart(request: DiagramRequest):
    """
    Execute a ChainChart diagram and return execution trace.
    
    This endpoint uses the REAL ChainChartAgent execution engine - no mocks.
    It executes nodes deterministically using the FlowGraph and Memory system.
    
    Request body should contain:
        - nodes: array of node objects
        - edges: array of edge objects
    
    Returns:
        - execution_logs: List of execution steps with node details
        - final_memory: Final memory state after execution
        - success: True if execution completed
        - error: Error message if execution failed
        - execution_trace: (debug mode) Detailed execution trace
        - memory_state: (debug mode) Memory state snapshots
        - logs: (debug mode) Debug log messages
        - debug_info: (debug mode) Additional debug information
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Check if debug mode is enabled
    debug_mode = os.getenv("CHAINCHART_DEBUG", "False").lower() == "true"
    
    try:
        logger.info("Received execution request")
        if debug_mode:
            logger.debug(f"Debug mode enabled. Request: {request}")
        
        # Transform UI format to backend format
        ui_diagram = {
            "nodes": request.nodes,
            "edges": request.edges
        }
        
        backend_diagram = transform_ui_to_backend_format(ui_diagram)
        
        if debug_mode:
            logger.debug(f"Transformed diagram: {backend_diagram}")
        
        # Validate diagram has nodes
        if not backend_diagram["nodes"]:
            raise HTTPException(status_code=400, detail="Diagram must contain at least one node")
        
        # Create agent and execute workflow - REAL EXECUTION, NO MOCKS
        logger.info("Creating ChainChartAgent instance")
        agent = ChainChartAgent(debug=debug_mode)
        
        logger.info("Starting workflow execution")
        result = await agent.run_workflow(backend_diagram)
        logger.info(f"Workflow execution completed. Steps: {len(result.get('execution_logs', []))}")
        
        # Build response with all available data
        response_data = {
            "execution_logs": result["execution_logs"],
            "final_memory": result["final_memory"],
            "success": True
        }
        
        # Include debug fields if debug mode is enabled
        if debug_mode and "execution_trace" in result:
            response_data["execution_trace"] = result["execution_trace"]
        if debug_mode and "memory_state" in result:
            response_data["memory_state"] = result["memory_state"]
        if debug_mode and "logs" in result:
            response_data["logs"] = result["logs"]
        if debug_mode and "debug_info" in result:
            response_data["debug_info"] = result["debug_info"]
        
        return ExecutionResponse(**response_data)
        
    except Exception as e:
        import traceback
        logger.error(f"Execution error: {str(e)}")
        logger.error(traceback.format_exc())
        
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


@app.post("/generate-contract", response_model=ContractGenerateResponse)
async def generate_contract(request: ContractGenerateRequest):
    """
    Generate Neo N3 smart contract C# code from ChainChart diagram.
    
    Request body should contain:
        - nodes: array of node objects
        - edges: array of edge objects
    
    Returns:
        - contract_text: Complete C# contract source code
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
        
        # Create contract agent and generate contract
        contract_agent = ContractAgent()
        contract_text = await contract_agent.generate_contract(backend_diagram)
        
        return ContractGenerateResponse(
            contract_text=contract_text,
            success=True
        )
        
    except Exception as e:
        import traceback
        return ContractGenerateResponse(
            contract_text="",
            success=False,
            error=str(e)
        )


@app.post("/compile-contract", response_model=ContractCompileResponse)
async def compile_contract_endpoint(request: ContractGenerateRequest):
    """
    Compile ChainChart diagram to C# contract, then compile to NEF + manifest.
    
    This endpoint:
    1. Receives ChainChart JSON
    2. Generates C# contract
    3. Validates and patches contract
    4. Saves to /generated/Contract.cs
    5. Compiles using Neo compiler
    6. Returns contract + NEF + manifest
    
    Request body should contain:
        - nodes: array of node objects
        - edges: array of edge objects
    
    Returns:
        - contract: C# source code
        - nef: Base64 encoded NEF file
        - manifest: JSON manifest object
        - compile_errors: List of compiler warnings/errors
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
        
        # Step 1: Generate contract
        contract_code = generate_contract_from_diagram(backend_diagram)
        
        # Step 2: Validate and patch contract
        is_valid, validation_errors, patched_contract = validate_contract(contract_code)
        # Always use patched version (it fixes issues automatically)
        contract_code = patched_contract
        
        # Step 3: Save to generated/ directory
        generated_dir = Path("generated")
        generated_dir.mkdir(exist_ok=True)
        contract_file = generated_dir / "Contract.cs"
        contract_file.write_text(contract_code, encoding='utf-8')
        
        # Step 4: Compile contract
        nef_path, manifest_path, compile_success, compile_errors = compile_neo_contract(str(contract_file))
        
        if not nef_path or not manifest_path:
            # Filter out compiler installation errors and auto-fixed errors
            filtered_errors = [
                e for e in validation_errors 
                if "compiler" not in e.lower() and "devpack" not in e.lower() and 
                   "install" not in e.lower() and "displayname" not in e.lower()
            ]
            return ContractCompileResponse(
                contract=contract_code,
                nef="",
                manifest={},
                success=False,
                compile_errors=compile_errors + filtered_errors,
                error="Compilation failed. Check that Neo compiler is installed."
            )
        
        # Step 5: Read compiled files
        compiled_data = read_compiled_files(nef_path, manifest_path)
        
        # Filter out compiler installation errors and auto-fixed errors from validation errors
        # (DisplayName errors are automatically fixed, so don't report them)
        filtered_validation_errors = [
            e for e in validation_errors 
            if "compiler" not in e.lower() and "devpack" not in e.lower() and 
               "install" not in e.lower() and "displayname" not in e.lower()
        ]
        
        return ContractCompileResponse(
            contract=contract_code,
            nef=compiled_data["nef"],
            manifest=compiled_data["manifest"],
            success=compile_success,
            compile_errors=compile_errors + filtered_validation_errors,
            mock=not compile_success
        )
        
    except Exception as e:
        import traceback
        return ContractCompileResponse(
            contract="",
            nef="",
            manifest={},
            success=False,
            compile_errors=[str(e)],
            error=str(e),
            mock=True
        )


@app.post("/deploy-contract", response_model=ContractDeployResponse)
async def deploy_contract_endpoint(request: ContractDeployRequest = ContractDeployRequest()):
    """
    Deploy compiled contract (NEF + manifest) to Neo N3 TestNet.
    
    This endpoint:
    1. Reads NEF + manifest from generated_contracts/ (if not provided in request)
    2. Or uses provided NEF (base64) + manifest (JSON)
    3. Calls deploy_to_testnet()
    4. Returns transaction hash
    
    Request body (optional):
        - nef: Base64 encoded NEF file (optional, will read from disk if not provided)
        - manifest: JSON manifest object (optional, will read from disk if not provided)
        - private_key: Optional private key for signing (WIF format)
    
    Returns:
        - tx_hash: Transaction hash of deployment (0x...)
        - success: True if deployment succeeded
        - mock: True if mock deployment (neo-mamba not available)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Step 1: Try to fetch from Supabase FIRST (primary source)
        nef_bytes = None
        manifest_data = None
        
        # Try Supabase if contract_id is provided
        if SUPABASE_AVAILABLE and request.contract_id:
            logger.info(f"📦 Fetching contract from Supabase: {request.contract_id}")
            contract_data = await get_contract_from_supabase(
                contract_id=request.contract_id,
                user_id=request.user_id
            )
            if contract_data:
                nef_bytes = contract_data.get("nef_data")
                manifest_data = contract_data.get("manifest_data")
                logger.info(f"✅ Contract fetched from Supabase: {contract_data.get('contract_name')}")
            else:
                logger.warning(f"⚠️ Contract not found in Supabase: {request.contract_id}")
        
        # If no contract_id but user_id provided, try to get latest contract from Supabase
        if not nef_bytes and SUPABASE_AVAILABLE and request.user_id:
            logger.info(f"📦 Fetching latest contract from Supabase for user: {request.user_id}")
            contract_data = await get_latest_contract_for_user(
                user_id=request.user_id,
                project_id=request.project_id
            )
            if contract_data:
                nef_bytes = contract_data.get("nef_data")
                manifest_data = contract_data.get("manifest_data")
                logger.info(f"✅ Latest contract fetched from Supabase: {contract_data.get('contract_name')}")
        
        # Fallback to local filesystem only if Supabase didn't provide data
        generated_contracts_dir = Path("generated_contracts")
        latest_contract_files = None
        default_nef = generated_contracts_dir / "contract.nef"
        default_manifest = generated_contracts_dir / "contract.manifest.json"
        
        if not nef_bytes or not manifest_data:
            # Try to find the most recent uniquely named contract files (preferred)
            if generated_contracts_dir.exists():
                nef_files = list(generated_contracts_dir.glob("*_*.nef"))
                if nef_files:
                    latest_nef = max(nef_files, key=lambda p: p.stat().st_mtime)
                    contract_base = latest_nef.stem
                    latest_manifest = generated_contracts_dir / f"{contract_base}.manifest.json"
                    if latest_manifest.exists():
                        latest_contract_files = (latest_nef, latest_manifest)
                        logger.info(f"📦 Found latest contract in local filesystem: {contract_base}")
        
        # Determine source of NEF and manifest
        # Note: For deployment, we need files on disk, so we'll create them temporarily
        if nef_bytes and manifest_data:
            # Use data from Supabase - create files in generated_contracts/ for deployment
            # (Deployment tools need files on disk, but Supabase is our primary storage)
            generated_contracts_dir.mkdir(exist_ok=True)
            nef_file = generated_contracts_dir / "contract.nef"
            manifest_file = generated_contracts_dir / "contract.manifest.json"
            
            nef_file.write_bytes(nef_bytes)
            manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding='utf-8')
            
            logger.info(f"📦 Using contract files from Supabase (copied to local for deployment)")
        elif request and request.nef and request.manifest:
            # Use provided files (if passed directly in request)
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                nef_file = temp_path / "contract.nef"
                manifest_file = temp_path / "contract.manifest.json"
                
                # Decode NEF from base64
                import base64
                # Fix base64 padding if needed (must be multiple of 4)
                nef_b64 = request.nef.strip()
                # Add padding if needed
                missing_padding = len(nef_b64) % 4
                if missing_padding:
                    nef_b64 += '=' * (4 - missing_padding)
                nef_bytes = base64.b64decode(nef_b64)
                nef_file.write_bytes(nef_bytes)
                
                # Write manifest
                manifest_file.write_text(json.dumps(request.manifest, indent=2), encoding='utf-8')
                
                # Copy files to persistent location BEFORE temp directory is deleted
                generated_contracts_dir.mkdir(exist_ok=True)
                target_nef = generated_contracts_dir / "contract.nef"
                target_manifest = generated_contracts_dir / "contract.manifest.json"
                shutil.copy2(nef_file, target_nef)
                shutil.copy2(manifest_file, target_manifest)
                nef_file = target_nef
                manifest_file = target_manifest
        elif latest_contract_files:
            # Use the most recent uniquely named contract files (preferred - has correct manifest name)
            nef_file, manifest_file = latest_contract_files
            logger.info(f"📦 Using latest uniquely named contract: {nef_file.name}")
            # Verify the manifest has the correct unique name
            manifest_json = json.loads(manifest_file.read_text(encoding='utf-8'))
            manifest_name = manifest_json.get("name", "Unknown")
            logger.info(f"📝 Contract manifest name: {manifest_name}")
        elif default_nef.exists() and default_manifest.exists():
            # Fallback to generic files (may have old name, but better than nothing)
            logger.warning("⚠️ Using generic contract files - these may have an old manifest name!")
            logger.warning("   Consider generating a new contract to get a unique name.")
            nef_file = default_nef
            manifest_file = default_manifest
            # Check and warn about manifest name
            try:
                manifest_json = json.loads(manifest_file.read_text(encoding='utf-8'))
                manifest_name = manifest_json.get("name", "Unknown")
                logger.warning(f"   Current manifest name: {manifest_name}")
            except:
                pass
        else:
            raise HTTPException(
                status_code=400, 
                detail="No contract files found. Please generate a contract first using 'Generate Smart Contract' button, or provide nef and manifest in the request."
            )
        
        # Step 2: Ensure files are in generated_contracts/ for RPC deployment
        # (Only needed if files came from local filesystem, Supabase files are already there)
        if nef_bytes and manifest_data:
            # Files from Supabase are already in generated_contracts/
            target_nef = nef_file
            target_manifest = manifest_file
        else:
            # Files from local filesystem - ensure they're in the right place
            generated_contracts_dir.mkdir(exist_ok=True)
            target_nef = generated_contracts_dir / "contract.nef"
            target_manifest = generated_contracts_dir / "contract.manifest.json"
            
            # Copy files if they're not already in the target location
            if str(nef_file) != str(target_nef):
                shutil.copy2(nef_file, target_nef)
            if str(manifest_file) != str(target_manifest):
                shutil.copy2(manifest_file, target_manifest)
        
        # Get private key from request or environment (needed for both deployment methods)
        # 1. Get private key from multiple sources
        private_key = None
        
        # Try from request body first
        if request and hasattr(request, 'private_key') and request.private_key:
            private_key = request.private_key
        
        # Fallback to environment variables
        if not private_key:
            try:
                from deployment.config import NEO_PRIVATE_KEY
                private_key = NEO_PRIVATE_KEY
            except ImportError:
                # Try multiple environment variable names
                private_key = (
                    os.getenv('NEO_PRIVATE_KEY') or 
                    os.getenv('PRIVATE_KEY') or 
                    os.getenv('NEOFS_PRIVATE_KEY_WIF')
                )
        
        # Validate private key exists
        if not private_key:
            raise HTTPException(
                status_code=400,
                detail="NEO_PRIVATE_KEY not provided. Set it in .env file or pass in request."
            )
        
        # Safe strip (only if not None)
        private_key = private_key.strip() if private_key else None
        
        if not private_key:
            raise HTTPException(
                status_code=400,
                detail="NEO_PRIVATE_KEY is empty after stripping whitespace"
            )
        
        logger.info(f"[DEBUG] Private key loaded: {private_key[:10]}...")
        
        # 2. Get RPC URL
        rpc_url = None
        if request and hasattr(request, 'rpc_url') and request.rpc_url:
            rpc_url = request.rpc_url
        
        if not rpc_url:
            rpc_url = os.getenv('NEO_RPC_URL')
        
        if not rpc_url:
            # Default to testnet
            rpc_url = 'http://seed3t5.neo.org:20332'
            logger.info(f"[DEBUG] Using default RPC: {rpc_url}")
        
        logger.info(f"[DEBUG] RPC URL: {rpc_url}")
        
        # 3. Get network
        network = None
        if request and hasattr(request, 'network') and request.network:
            network = request.network
        
        if not network:
            network = os.getenv('NEO_NETWORK') or 'testnet'
        
        logger.info(f"[DEBUG] Network: {network}")
        
        # Step 3: Deploy to testnet using neon-js (EXACTLY like NeoNova)
        # NeoNova uses neon-js's experimental.deployContract - we use the same library!
        try:
            # Try neon-js approach first (EXACTLY like NeoNova - same library!)
            try:
                from generator.neonova_deploy_neonjs import deploy_contract_with_neonjs
                logger.info("🚀 Attempting deployment using neon-js (EXACTLY like NeoNova)...")
                deploy_result = deploy_contract_with_neonjs(
                    str(target_nef),
                    str(target_manifest),
                    private_key,
                    rpc_url  # Use the rpc_url we validated above
                )
                if deploy_result.get("success"):
                    # Deployment succeeded - check for tx_hash or contract_hash
                    tx_hash = deploy_result.get("tx_hash")
                    contract_hash = deploy_result.get("contract_hash")
                    
                    # Update Supabase if contract_id is provided
                    if SUPABASE_AVAILABLE and request.contract_id:
                        try:
                            await update_contract_deployment(
                                contract_id=request.contract_id,
                                contract_hash=contract_hash,
                                tx_hash=tx_hash,
                                status="deployed"
                            )
                            logger.info(f"💾 Deployment info saved to Supabase")
                        except Exception as supabase_error:
                            logger.warning(f"⚠️ Error updating Supabase: {supabase_error}")
                    
                    if tx_hash:
                        logger.info(f"✅ neon-js deployment successful! TX: {tx_hash}, Contract: {contract_hash}")
                        return ContractDeployResponse(
                            tx_hash=str(tx_hash),
                            contract_hash=contract_hash,  # Always include contract_hash
                            success=True,
                            error=None,
                            mock=False
                        )
                    elif contract_hash:
                        # Deployment succeeded but no tx_hash - use contract_hash
                        logger.info(f"✅ neon-js deployment successful! Contract: {contract_hash}")
                        logger.info(f"   Note: Transaction hash not available, but contract is deployed")
                        return ContractDeployResponse(
                            tx_hash=None,
                            contract_hash=contract_hash,  # Include contract_hash
                            success=True,
                            error=None,
                            mock=False
                        )
                    else:
                        # Success but no hash info - still return success
                        logger.info(f"✅ neon-js deployment successful! (no hash info)")
                        return ContractDeployResponse(
                            tx_hash=None,
                            success=True,
                            error=None,
                            mock=False
                        )
                elif deploy_result.get("error"):
                    error_msg = deploy_result.get("error", "Unknown error")
                    logger.error(f"❌ neon-js deployment failed: {error_msg}")
                    
                    # If neon-js is available, don't fall back to neo-mamba (which has signing issues)
                    # Return the neon-js error with helpful guidance
                    if "Insufficient GAS" in error_msg or "GAS" in error_msg:
                        # Extract account address from the error or use the account
                        account_address = "your wallet address"
                        try:
                            from neo3.wallet import Wallet
                            temp_wallet = Wallet.from_wif(private_key)
                            account_address = temp_wallet.default_account.address
                        except Exception:
                            pass
                        
                        raise HTTPException(
                            status_code=400,
                            detail=f"Deployment failed: {error_msg}\n\nYour account address: {account_address}\n\nTo get testnet GAS:\n1. Visit https://neotube.org/faucet\n2. Enter your address: {account_address}\n3. Request testnet GAS\n4. Try deploying again"
                        )
                    else:
                        # neon-js failed - don't fall back, return the error directly
                        raise HTTPException(
                            status_code=500,
                            detail=f"neon-js deployment failed: {error_msg}. neon-js is installed, so this is likely a configuration issue (check NEO_PRIVATE_KEY format, RPC URL, or contract files)."
                        )
                else:
                    # deploy_result exists but has no success or error - this shouldn't happen
                    logger.error(f"❌ neon-js deployment returned unexpected result: {deploy_result}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"neon-js deployment returned unexpected result. Check backend logs for details."
                    )
            except ImportError:
                logger.warning("⚠️  neon-js deployment not available (Node.js/neon-js not installed)")
                logger.warning("⚠️  Install Node.js and run: npm install @cityofzion/neon-js")
                logger.warning("⚠️  Falling back to neo-mamba approach...")
                # Only fall back if neon-js is not installed
                fallback_needed = True
            except Exception as neonjs_error:
                error_msg = str(neonjs_error)
                logger.error(f"❌ neon-js deployment exception: {error_msg}")
                # If neon-js is installed but failed, don't fall back to neo-mamba
                # Only fall back if it's a true ImportError (neon-js not available)
                if "ImportError" in error_msg or "not found" in error_msg.lower() or "cannot find module" in error_msg.lower():
                    logger.warning("⚠️  neon-js not available, falling back to neo-mamba...")
                    fallback_needed = True
                else:
                    # neon-js is available but failed - don't fall back, raise the error
                    raise HTTPException(
                        status_code=500,
                        detail=f"neon-js deployment failed: {error_msg}. Check NEO_PRIVATE_KEY format, RPC URL, or contract files."
                    )
            
            # Only fall back to neo-mamba if neon-js is truly not available
            # If we get here without raising an exception, neon-js should have succeeded
            # If it didn't, we should have already raised an HTTPException above
            if 'fallback_needed' in locals() and fallback_needed:
                # Fallback to neo-mamba approach
                from generator.neonova_deploy import deploy_contract_neonova_style
                import logging
                logger = logging.getLogger(__name__)
                
                logger.info("🚀 Attempting NeoNova-style deployment (using neo-mamba, matches neon-js format)...")
                
                # Deploy using neo-mamba (same approach as NeoNova)
                deploy_result = deploy_contract_neonova_style(
                    str(target_nef),
                    str(target_manifest),
                    private_key,
                    os.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")
                )
                
                if deploy_result.get("success") and deploy_result.get("tx_hash"):
                    tx_hash = deploy_result.get("tx_hash")
                    logger.info(f"✅ NeoNova-style deployment successful! TX: {tx_hash}")
                    return ContractDeployResponse(
                        tx_hash=str(tx_hash),
                        success=True,
                        error=None,
                        mock=False
                    )
                else:
                    error_msg = deploy_result.get("error", "Unknown deployment error")
                    logger.error(f"NeoNova-style deployment failed: {error_msg}")
                    raise Exception(f"Deployment failed: {error_msg}")
                
        except HTTPException:
            # Re-raise HTTPException - don't catch it, let it propagate to FastAPI
            raise
        except AttributeError as attr_error:
            # This catches the 'NoneType' has no attribute 'strip' error
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            error_trace = traceback.format_exc()
            logger.error(f"[ERROR] AttributeError: {error_trace}")
            
            return ContractDeployResponse(
                tx_hash=None,
                success=False,
                error=f'Configuration error: A required value is None. Check NEO_PRIVATE_KEY, RPC_URL, and contract files. Details: {str(attr_error)}',
                mock=False
            )
        except Exception as rpc_error:
            # Log the error before falling back
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            error_msg = str(rpc_error)
            error_trace = traceback.format_exc()
            logger.error(f"[ERROR] Deployment failed: {error_trace}")
            
            # Check if it's the NEF size issue
            if "too small" in error_msg.lower() or "24 bytes" in error_msg:
                return ContractDeployResponse(
                    tx_hash=None,
                    success=False,
                    error=f"Deployment failed: Contract NEF is too small (24 bytes = mock/empty). Please export a real contract from the UI first. Error: {error_msg}",
                    mock=False
                )
            
            # Check if it's a missing dependency
            if "ecdsa" in error_msg.lower() or "base58" in error_msg.lower():
                return ContractDeployResponse(
                    tx_hash=None,
                    success=False,
                    error=f"Deployment failed: Missing dependency. Install with: pip install ecdsa base58. Error: {error_msg}",
                    mock=False
                )
            
            # Check if it's a private key issue
            if "private key" in error_msg.lower() or "NEO_PRIVATE_KEY" in error_msg:
                return ContractDeployResponse(
                    tx_hash=None,
                    success=False,
                    error=f"Deployment failed: Private key issue. Check your .env file has NEO_PRIVATE_KEY set. Error: {error_msg}",
                    mock=False
                )
            
            # Check if it's a script format issue - try NeoNova's method
            if "Invalid transaction script" in error_msg or "InvalidScript" in error_msg:
                logger.warning("⚠️  RPC deployment failed, trying NeoNova-compatible method...")
                try:
                    from generator.neonova_deploy import deploy_contract_neonova_style
                    
                    # Get private key - try multiple sources
                    private_key = None
                    if request and request.private_key:
                        private_key = request.private_key
                    else:
                        # Try deployment.config first
                        try:
                            from deployment.config import NEO_PRIVATE_KEY
                            private_key = NEO_PRIVATE_KEY
                        except ImportError:
                            pass
                        
                        # Try environment variable
                        if not private_key:
                            private_key = os.getenv("NEO_PRIVATE_KEY")
                        
                        # Try loading .env file directly
                        if not private_key:
                            try:
                                from dotenv import load_dotenv
                                load_dotenv(override=True)  # Force reload
                                private_key = os.getenv("NEO_PRIVATE_KEY")
                            except ImportError:
                                pass
                        
                        # Clean up private key (remove quotes, whitespace, trailing characters)
                        if private_key:
                            private_key = private_key.strip().strip('"').strip("'")
                            # Remove trailing 'd' if it's a typo (WIF keys are typically 52 chars)
                            if len(private_key) > 52 and private_key.endswith('d'):
                                private_key = private_key.rstrip('d')
                    
                    if private_key:
                        # Get RPC URL - ensure os is accessible
                        import os as os_module
                        rpc_url_for_neonova = os_module.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")
                        
                        neonova_result = deploy_contract_neonova_style(
                            str(nef_file),
                            str(manifest_file),
                            private_key,
                            rpc_url_for_neonova
                        )
                        
                        if neonova_result.get("success"):
                            logger.info("✅ NeoNova-compatible deployment successful!")
                            return ContractDeployResponse(
                                tx_hash=neonova_result.get("tx_hash"),
                                success=True,
                                error=None,
                                mock=False
                            )
                        else:
                            logger.warning(f"⚠️  NeoNova method also failed: {neonova_result.get('error')}")
                except Exception as neonova_error:
                    import traceback
                    error_str = str(neonova_error)
                    logger.warning(f"⚠️  NeoNova method not available: {error_str}")
                    logger.debug(f"NeoNova error traceback: {traceback.format_exc()}")
                
                return ContractDeployResponse(
                    tx_hash=None,
                    success=False,
                    error=f"Deployment failed: Invalid transaction script format. The deployment script builder needs fixing. "
                          f"Your existing contract (0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab) is still working - you can use workflows without deploying again. "
                          f"Original error: {error_msg}",
                    mock=False
                )
            
            logger.warning("⚠️  Falling back to neo-mamba (may have signing issues)...")
            
            # Fallback to old deployment method
            # Try to get private key from request, environment, or config
            private_key = None
            if request and request.private_key:
                private_key = request.private_key
            else:
                # Try to load from environment or config
                try:
                    from deployment.config import NEO_PRIVATE_KEY
                    private_key = NEO_PRIVATE_KEY
                except ImportError:
                    private_key = os.getenv("NEO_PRIVATE_KEY")
            
            if not private_key or private_key == "":
                return ContractDeployResponse(
                    tx_hash=None,
                    success=False,
                    error="NEO_PRIVATE_KEY not found. Please set it in .env file or provide it in the request.",
                    mock=True
                )
            
            result = deploy_to_testnet(
                str(nef_file),
                str(manifest_file),
                private_key
            )
            
            return ContractDeployResponse(
                tx_hash=result.get("tx_hash"),
                success=result.get("success", False),
                error=result.get("error"),
                mock=result.get("mock", False)
            )
        
    except Exception as e:
        import traceback
        return ContractDeployResponse(
            tx_hash=None,
            success=False,
            error=str(e),
            mock=True
        )


@app.post("/export-contract", response_model=ExportContractResponse)
async def export_contract(request: ContractGenerateRequest):
    """
    Export complete Neo contract: generate using SpoonOS LLM, compile, and return contract + manifest + NEF.
    
    This endpoint:
    1. Transforms UI diagram format to backend format
    2. Uses SpoonOS LLM (ContractAgent) to generate C# contract from diagram (including edge-based control flow)
    3. Validates and patches contract
    4. Compiles contract to NEF + manifest
    5. Saves files to generated_contracts/ directory
    6. Returns all three in one response
    
    Request body should contain:
        - nodes: array of node objects
        - edges: array of edge objects (CRITICAL: edges define function logic and control flow)
    
    Returns:
        - contract: Complete C# contract source code
        - manifest: JSON manifest object
        - nef: Base64 encoded NEF file
        - nef_path: Path to saved NEF file
        - manifest_path: Path to saved manifest file
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
        
        # Step 1: Generate contract using SpoonOS LLM (ContractAgent)
        contract_agent = ContractAgent()
        contract_code = await contract_agent.generate_contract(backend_diagram)
        
        # Step 2: Create persistent directory for contract files
        generated_contracts_dir = Path("generated_contracts")
        generated_contracts_dir.mkdir(exist_ok=True)
        
        # Step 2.5: Validate and patch contract
        # Always patch the contract to fix common issues (missing using statements, etc.)
        import logging
        import re
        logger = logging.getLogger(__name__)
        logger.info("Patching contract to add missing using statements...")
        contract_code = patch_contract(contract_code)
        logger.info("Contract patched successfully")
        
        # Extract unique contract class name from the code
        # DO THIS EARLY so we can use it even if compilation fails
        contract_name = "Contract"  # Default fallback
        # Try multiple patterns to find the class name
        patterns = [
            r'public\s+class\s+(\w+)\s*:\s*SmartContract',  # public class Name : SmartContract
            r'class\s+(\w+)\s*:\s*SmartContract',  # class Name : SmartContract
            r'public\s+class\s+(\w+)',  # public class Name
            r'class\s+(\w+)',  # class Name
        ]
        
        for pattern in patterns:
            class_match = re.search(pattern, contract_code, re.MULTILINE | re.DOTALL)
            if class_match:
                contract_name = class_match.group(1)
                logger.info(f"📝 Extracted contract name: {contract_name}")
                break
        else:
            logger.warning("⚠️ Could not extract contract class name, using default 'Contract'")
            logger.debug(f"Contract code preview: {contract_code[:200]}")
            # Even if we can't extract, ensure uniqueness
            import time
            import random
            contract_name = f"Contract_{int(time.time())}_{random.randint(1000, 9999)}"
            logger.info(f"📝 Generated unique fallback contract name: {contract_name}")
        
        # Ensure contract name is ALWAYS unique by appending timestamp if not already unique
        # Check if name already has a timestamp pattern (numbers at the end)
        if not re.search(r'_\d{10,}', contract_name):
            import time
            import random
            contract_name = f"{contract_name}_{int(time.time())}_{random.randint(1000, 9999)}"
            logger.info(f"📝 Added unique identifier to contract name: {contract_name}")
        
        # Sanitize contract name for filesystem (remove invalid characters)
        safe_contract_name = re.sub(r'[^a-zA-Z0-9_]', '_', contract_name)
        
        # Validate again to check for any remaining issues
        is_valid, validation_errors, _ = validate_contract(contract_code)
        if validation_errors:
            logger.warning(f"Validation warnings: {validation_errors}")
        
        # Step 3: Write contract to temporary file for compilation
        # (Compiler needs a .cs file, but we'll save the compiled outputs to persistent directory)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            contract_file = temp_path / f"{safe_contract_name}.cs"
            contract_file.write_text(contract_code, encoding='utf-8')
            
            # Step 4: Save C# contract to persistent directory with unique name
            persistent_contract_file = generated_contracts_dir / f"{safe_contract_name}.cs"
            persistent_contract_file.write_text(contract_code, encoding='utf-8')
            logger.info(f"💾 Saved contract to: {persistent_contract_file}")
            
            # Step 5: Try to compile contract (optional - if compiler not installed, just return C# code)
            logger.info(f"🔨 Starting compilation of contract: {safe_contract_name}")
            nef_path, manifest_path, compile_success, compile_errors = compile_neo_contract(str(contract_file))
            logger.info(f"🔨 Compilation result: success={compile_success}, nef_path={nef_path}, manifest_path={manifest_path}")
            if compile_errors:
                logger.warning(f"🔨 Compilation errors: {compile_errors[:5]}")
            
            # If compilation failed, that's OK - we'll just return the C# code
            # The user can compile it manually later or install the compiler
            if not compile_success:
                logger.warning(f"⚠️ Compilation failed for {safe_contract_name}. Errors: {compile_errors[:3] if compile_errors else 'Unknown'}")
                # Check if it's just a missing compiler issue (not a syntax error)
                is_missing_compiler = any(
                    "not found" in str(e).lower() or 
                    "not detected" in str(e).lower() or
                    "install" in str(e).lower() or
                    "devpack" in str(e).lower()
                    for e in compile_errors
                )
                
                if is_missing_compiler:
                    # Compiler not installed - that's fine, just return the C# code
                    # BUT: Still update/create manifest with unique name so deployment can use it
                    logger.info("Neo compiler not installed - returning C# code only. User can compile manually later.")
                    
                    # Create a basic manifest with the unique contract name
                    # This ensures deployment will use the correct name even if compilation failed
                    basic_manifest = {
                        "name": contract_name,  # Use the unique contract name!
                        "groups": [],
                        "features": {},
                        "supportedstandards": [],
                        "abi": {
                            "methods": [],
                            "events": []
                        },
                        "permissions": [],
                        "trusts": [],
                        "extra": {
                            "Author": "ChainChart",
                            "Description": f"Generated contract: {contract_name} (not yet compiled)"
                        }
                    }
                    
                    # Save manifest with unique name
                    unique_manifest_path = generated_contracts_dir / f"{safe_contract_name}.manifest.json"
                    unique_manifest_path.write_text(json.dumps(basic_manifest, indent=2), encoding='utf-8')
                    logger.info(f"💾 Created basic manifest with unique name: {contract_name}")
                    
                    # Also update generic manifest - FORCE UPDATE
                    generic_manifest = generated_contracts_dir / "contract.manifest.json"
                    # Force write - overwrite whatever is there
                    generic_manifest.write_text(json.dumps(basic_manifest, indent=2), encoding='utf-8')
                    logger.info(f"💾 FORCED UPDATE: Generic manifest with unique name: {contract_name}")
                    
                    # Verify it was actually written
                    verify = json.loads(generic_manifest.read_text(encoding='utf-8'))
                    if verify.get("name") != contract_name:
                        logger.error(f"❌ CRITICAL: Manifest update failed! Expected '{contract_name}', got '{verify.get('name')}'")
                        # Try one more time
                        generic_manifest.write_text(json.dumps(basic_manifest, indent=2), encoding='utf-8')
                    else:
                        logger.info(f"✅ Verified generic manifest has correct name: {contract_name}")
                    
                    return ExportContractResponse(
                        contract=contract_code,
                        manifest=basic_manifest,
                        nef="",
                        success=True,  # Still success - we generated the code!
                        error=None,
                        nef_path=None,
                        manifest_path=str(unique_manifest_path),
                        contract_path=str(persistent_contract_file),
                        compile_warning="Neo compiler not installed. C# contract saved to generated_contracts/Contract.cs. To compile: Install Neo.Compiler.CSharp with 'dotnet tool install -g Neo.Compiler.CSharp', then run 'nccs generated_contracts/Contract.cs'"
                    )
                else:
                    # Actual compilation errors (syntax issues) - return with error
                    error_msg = "Compilation failed. "
                    if compile_errors:
                        error_msg += "Errors: " + "; ".join(compile_errors[:3])  # Show first 3 errors
                    return ExportContractResponse(
                        contract=contract_code,
                        manifest={},
                        nef="",
                        success=False,
                        error=error_msg,
                        nef_path=None,
                        manifest_path=None,
                        contract_path=str(persistent_contract_file)
                    )
            
            # Check if files exist and are valid (not empty/mock)
            if not nef_path or not manifest_path:
                return ExportContractResponse(
                    contract=contract_code,
                    manifest={},
                    nef="",
                    success=False,
                    error="Compilation failed - NEF or manifest file not created. Check that Neo compiler is installed.",
                    nef_path=None,
                    manifest_path=None
                )
            
            # Check if NEF is a real contract (not just 24-byte header)
            nef_file = Path(nef_path)
            if nef_file.exists():
                nef_size = nef_file.stat().st_size
                if nef_size <= 24:
                    return ExportContractResponse(
                        contract=contract_code,
                        manifest={},
                        nef="",
                        success=False,
                        error=f"Compilation produced empty/mock contract (NEF is only {nef_size} bytes). Check compilation errors.",
                        nef_path=None,
                        manifest_path=None
                    )
            
            # Step 5: Read NEF and manifest for Supabase storage
            nef_bytes = None
            if nef_path and Path(nef_path).exists():
                nef_bytes = Path(nef_path).read_bytes()
            
            # Read manifest JSON
            manifest_json = None
            if manifest_path and Path(manifest_path).exists():
                manifest_json = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
            
            # Step 5.5: Save to Supabase FIRST (primary storage)
            contract_id = None
            if SUPABASE_AVAILABLE and request.user_id:
                try:
                    # Update manifest name before saving
                    if manifest_json:
                        manifest_json["name"] = contract_name
                    
                    contract_id = await save_contract_to_supabase(
                        user_id=request.user_id,
                        contract_name=safe_contract_name,
                        contract_code=contract_code,
                        nef_data=nef_bytes,
                        manifest_data=manifest_json or {},
                        project_id=request.project_id,
                        status="compiled" if compile_success else "generated"
                    )
                    if contract_id:
                        logger.info(f"💾 Contract saved to Supabase with ID: {contract_id}")
                    else:
                        logger.warning("⚠️ Failed to save contract to Supabase (check SUPABASE_URL and keys)")
                except Exception as supabase_error:
                    logger.warning(f"⚠️ Error saving to Supabase: {supabase_error} (continuing with filesystem fallback)")
            
            # Step 5.6: Optionally save to local filesystem as backup (only if Supabase save failed or not available)
            persistent_nef_path = None
            persistent_manifest_path = None
            if not contract_id or not SUPABASE_AVAILABLE:
                # Fallback to local storage if Supabase not available or save failed
                persistent_nef_path = generated_contracts_dir / f"{safe_contract_name}.nef"
                persistent_manifest_path = generated_contracts_dir / f"{safe_contract_name}.manifest.json"
                
                # Copy NEF file
                if nef_bytes:
                    persistent_nef_path.write_bytes(nef_bytes)
                    logger.info(f"💾 Saved NEF to local filesystem: {persistent_nef_path}")
                else:
                    shutil.copy2(nef_path, persistent_nef_path)
                    logger.info(f"💾 Saved NEF to local filesystem: {persistent_nef_path}")
            
            # Update manifest name to match the contract class name (if not already done)
            # This is CRITICAL: The manifest name affects the contract hash!
            if manifest_json:
                old_name = manifest_json.get("name", "Contract")
                logger.info(f"🔍 Manifest before update: name='{old_name}', contract_name='{contract_name}'")
                
                # ALWAYS update the manifest name to match the contract class name
                manifest_json["name"] = contract_name
                logger.info(f"🔧 FORCED manifest name to: {contract_name}")
                if old_name != contract_name:
                    logger.info(f"📝 Updated manifest name from '{old_name}' to '{contract_name}' (required for unique contract hash)")
            
            # Save manifest to local filesystem only if Supabase save failed
            if persistent_manifest_path:
                persistent_manifest_path.write_text(json.dumps(manifest_json, indent=2), encoding='utf-8')
                logger.info(f"💾 Saved manifest to local filesystem: {persistent_manifest_path} with name: {manifest_json.get('name') if manifest_json else 'N/A'}")
            
            # Verify the NEF is valid (if we have it)
            if nef_bytes and len(nef_bytes) <= 24:
                return ExportContractResponse(
                    contract=contract_code,
                    manifest={},
                    nef="",
                    success=False,
                    error=f"NEF is invalid (only {len(nef_bytes)} bytes). Compilation may have failed.",
                    nef_path=None,
                    manifest_path=None
                )
            
            # Step 6: Read compiled files for response
            try:
                compiled_data = read_compiled_files(str(persistent_nef_path), str(persistent_manifest_path))
            except Exception as read_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error reading compiled files: {read_error}")
                # Convert paths to strings, handling None case
                nef_path_val = str(persistent_nef_path) if persistent_nef_path is not None else None
                manifest_path_val = str(persistent_manifest_path) if persistent_manifest_path is not None else None
                
                return ExportContractResponse(
                    contract=contract_code,
                    manifest={},
                    nef="",
                    success=False,
                    error=f"Failed to read compiled files: {str(read_error)}",
                    nef_path=nef_path_val,
                    manifest_path=manifest_path_val
                )
            
            # Step 6: Read compiled files for response (from Supabase or local fallback)
            # If saved to Supabase, we already have the data; otherwise read from local files
            if contract_id and SUPABASE_AVAILABLE:
                # Use data we already have (from Supabase)
                compiled_data = {
                    "manifest": manifest_json or {},
                    "nef": base64.b64encode(nef_bytes).decode('utf-8') if nef_bytes else ""
                }
            else:
                # Fallback: read from local files
                try:
                    compiled_data = read_compiled_files(
                        str(persistent_nef_path) if persistent_nef_path else None,
                        str(persistent_manifest_path) if persistent_manifest_path else None
                    )
                except Exception as read_error:
                    logger.error(f"Error reading compiled files: {read_error}")
                    compiled_data = {
                        "manifest": manifest_json or {},
                        "nef": base64.b64encode(nef_bytes).decode('utf-8') if nef_bytes else ""
                    }
            
            # Ensure paths are strings (not None) - only set if local files were created
            nef_path_str = str(persistent_nef_path) if persistent_nef_path and persistent_nef_path.exists() else None
            manifest_path_str = str(persistent_manifest_path) if persistent_manifest_path and persistent_manifest_path.exists() else None
            
            return ExportContractResponse(
                contract=contract_code,
                manifest=compiled_data.get("manifest", {}),
                nef=compiled_data.get("nef", ""),
                success=True,
                nef_path=nef_path_str,
                manifest_path=manifest_path_str,
                contract_id=contract_id  # Add contract_id to response
            )
        
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in export_contract: {e}")
        logger.error(traceback.format_exc())
        return ExportContractResponse(
            contract="",
            manifest={},
            nef="",
            success=False,
            error=str(e),
            nef_path=None,
            manifest_path=None
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

