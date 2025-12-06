"""
FastAPI server for ChainChart backend execution.
Handles workflow execution requests from the UI.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
    # Debug fields (optional, only present if debug mode enabled)
    execution_trace: List[Dict[str, Any]] = None
    memory_state: Dict[str, Any] = None
    logs: List[str] = None
    debug_info: Dict[str, Any] = None


class ContractGenerateRequest(BaseModel):
    """Request model for contract generation"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


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


class ContractDeployResponse(BaseModel):
    """Response model for contract deployment"""
    tx_hash: Optional[str] = None
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
    try:
        generated_contracts_dir = Path("generated_contracts")
        default_nef = generated_contracts_dir / "contract.nef"
        default_manifest = generated_contracts_dir / "contract.manifest.json"
        
        # Determine source of NEF and manifest
        if request and request.nef and request.manifest:
            # Use provided files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                nef_file = temp_path / "contract.nef"
                manifest_file = temp_path / "contract.manifest.json"
                
                # Decode NEF from base64
                import base64
                nef_bytes = base64.b64decode(request.nef)
                nef_file.write_bytes(nef_bytes)
                
                # Write manifest
                manifest_file.write_text(json.dumps(request.manifest, indent=2), encoding='utf-8')
        elif default_nef.exists() and default_manifest.exists():
            # Use files from generated_contracts directory
            nef_file = default_nef
            manifest_file = default_manifest
        else:
            raise HTTPException(
                status_code=400, 
                detail="No contract files found. Please export the contract first, or provide nef and manifest in the request."
            )
        
        # Step 2: Ensure files are in generated_contracts/ for RPC deployment
        generated_contracts_dir.mkdir(exist_ok=True)
        target_nef = generated_contracts_dir / "contract.nef"
        target_manifest = generated_contracts_dir / "contract.manifest.json"
        
        # Copy files if they're not already in the target location
        if str(nef_file) != str(target_nef):
            shutil.copy2(nef_file, target_nef)
        if str(manifest_file) != str(target_manifest):
            shutil.copy2(manifest_file, target_manifest)
        
        # Step 3: Deploy to testnet using pure RPC deployment
        # Use the new RPC deployment system (bypasses neo-mamba signing issues)
        try:
            from neo_rpc_deploy import deploy_contract as rpc_deploy_contract
            import sys
            from io import StringIO
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info("🚀 Attempting pure RPC deployment (bypasses neo-mamba signing issues)...")
            
            # Capture stdout to get transaction hash
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                # Deploy using pure RPC (no neo-mamba signing issues)
                deploy_result = rpc_deploy_contract()
                output = captured_output.getvalue()
                logger.info(f"RPC deployment output: {output[:500]}")  # Log first 500 chars
            except Exception as rpc_deploy_error:
                output = captured_output.getvalue()
                logger.error(f"Pure RPC deployment failed: {rpc_deploy_error}")
                logger.error(f"RPC deployment output: {output}")
                raise  # Re-raise to trigger fallback
            finally:
                sys.stdout = old_stdout
            
            # Extract transaction hash from result or output
            tx_hash = None
            if isinstance(deploy_result, dict):
                tx_hash = deploy_result.get("tx_hash")
            elif isinstance(deploy_result, str):
                tx_hash = deploy_result
            
            # Try to extract from output if not in result
            if not tx_hash and "Transaction Hash:" in output:
                for line in output.split('\n'):
                    if "Transaction Hash:" in line:
                        tx_hash = line.split("Transaction Hash:")[-1].strip()
                        break
            
            if tx_hash:
                logger.info(f"✅ Pure RPC deployment successful! TX: {tx_hash}")
                return ContractDeployResponse(
                    tx_hash=tx_hash,
                    success=True,
                    error=None,
                    mock=False
                )
            else:
                # Fallback to old method
                error_msg = f"RPC deployment didn't return transaction hash. Output: {output[:200]}"
                logger.warning(error_msg)
                raise Exception(error_msg)
                
        except Exception as rpc_error:
            # Log the error before falling back
            import logging
            logger = logging.getLogger(__name__)
            error_msg = str(rpc_error)
            logger.warning(f"⚠️  Pure RPC deployment failed: {error_msg}")
            
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
                    import os
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
        logger = logging.getLogger(__name__)
        logger.info("Patching contract to add missing using statements...")
        contract_code = patch_contract(contract_code)
        logger.info("Contract patched successfully")
        
        # Validate again to check for any remaining issues
        is_valid, validation_errors, _ = validate_contract(contract_code)
        if validation_errors:
            logger.warning(f"Validation warnings: {validation_errors}")
        
        # Step 3: Write contract to temporary file for compilation
        # (Compiler needs a .cs file, but we'll save the compiled outputs to persistent directory)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            contract_file = temp_path / "Contract.cs"
            contract_file.write_text(contract_code, encoding='utf-8')
            
            # Step 4: Save C# contract to persistent directory (always save, even if compilation fails)
            persistent_contract_file = generated_contracts_dir / "Contract.cs"
            persistent_contract_file.write_text(contract_code, encoding='utf-8')
            
            # Step 5: Try to compile contract (optional - if compiler not installed, just return C# code)
            nef_path, manifest_path, compile_success, compile_errors = compile_neo_contract(str(contract_file))
            
            # If compilation failed, that's OK - we'll just return the C# code
            # The user can compile it manually later or install the compiler
            if not compile_success:
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
                    logger.info("Neo compiler not installed - returning C# code only. User can compile manually later.")
                    return ExportContractResponse(
                        contract=contract_code,
                        manifest={},
                        nef="",
                        success=True,  # Still success - we generated the code!
                        error=None,
                        nef_path=None,
                        manifest_path=None,
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
            
            # Step 5: Copy compiled files to persistent directory
            persistent_nef_path = generated_contracts_dir / "contract.nef"
            persistent_manifest_path = generated_contracts_dir / "contract.manifest.json"
            
            # Copy NEF file
            shutil.copy2(nef_path, persistent_nef_path)
            
            # Copy manifest file
            shutil.copy2(manifest_path, persistent_manifest_path)
            
            # Verify the copied NEF is valid
            if persistent_nef_path.exists():
                copied_size = persistent_nef_path.stat().st_size
                if copied_size <= 24:
                    return ExportContractResponse(
                        contract=contract_code,
                        manifest={},
                        nef="",
                        success=False,
                        error=f"Copied NEF is invalid (only {copied_size} bytes). Compilation may have failed.",
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
            
            # Ensure paths are strings (not None)
            nef_path_str = str(persistent_nef_path) if persistent_nef_path is not None else None
            manifest_path_str = str(persistent_manifest_path) if persistent_manifest_path is not None else None
            
            return ExportContractResponse(
                contract=contract_code,
                manifest=compiled_data.get("manifest", {}),
                nef=compiled_data.get("nef", ""),
                success=True,
                nef_path=nef_path_str,
                manifest_path=manifest_path_str
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

