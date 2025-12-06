from spoon_ai.tools.base import BaseTool
from typing import Any, Dict, Optional
import sys
from pathlib import Path

# Import centralized Neo configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
from generator.config import (
    NEO_RPC_URL,
    NEO_CONTRACT_HASH,
    get_rpc_url,
    get_contract_hash,
    has_contract_hash
)

# Try to import neo3 for real RPC calls (supports both neo-mamba and neo3-python)
try:
    # Try neo-mamba first (recommended, works with Python 3.13)
    try:
        from neo3.api import NeoRpcClient as RPCClient
        from neo3.core.types import UInt160
        NEO3_AVAILABLE = True
        NEO3_LIBRARY = "neo-mamba"
    except ImportError:
        # Fallback to neo3-python
        from neo3.api import RPCClient
        from neo3.core.types import UInt160
        NEO3_AVAILABLE = True
        NEO3_LIBRARY = "neo3-python"
except ImportError:
    NEO3_AVAILABLE = False
    NEO3_LIBRARY = None
    print("Warning: neo3 library not installed. Install with: pip install neo-mamba")

class ReadNeoStateTool(BaseTool):
    """
    Retrieve a storage value from Neo blockchain.
    
    Connects to Neo TestNet RPC and reads from the deployed contract.
    """
    name: str = "read_neo_state"
    description: str = "Retrieve a storage value from Neo blockchain."
    parameters: dict = {
        "type": "object",
        "properties": {"key": {"type": "string"}},
        "required": ["key"]
    }

    async def execute(self, key: str) -> Any:
        """
        Read storage value from Neo blockchain using real RPC calls.
        """
        # Validate configuration
        if not NEO3_AVAILABLE:
            raise RuntimeError(
                "neo3 library is not installed. Install with: pip install neo-mamba"
            )
        
        contract_hash_str = get_contract_hash()
        if not contract_hash_str:
            raise ValueError(
                "NEO_CONTRACT_HASH not set. Set it in .env or environment variables."
            )
        
        if not has_contract_hash():
            raise ValueError(
                f"Invalid contract hash format: {contract_hash_str}. "
                "Expected 40-character hex string (with or without 0x prefix)."
            )
        
        rpc_url = get_rpc_url()
        
        # Debug messages
        print(f"🔗 Using RPC: {rpc_url}")
        print(f"📝 Using Contract Hash: {contract_hash_str}")
        print(f"🔍 Reading storage key: {key}")
        if NEO3_LIBRARY:
            print(f"📚 Using library: {NEO3_LIBRARY}")
        
        try:
            rpc = RPCClient(rpc_url)
            
            # Convert contract hash string to UInt160
            hash_str = contract_hash_str.replace("0x", "").replace("0X", "")
            contract_hash_uint = UInt160.from_string(hash_str)
            
            # Convert storage key to bytes
            storage_key = key.encode('utf-8')
            
            # Call getStorage RPC method
            storage_value = await rpc.get_storage(contract_hash_uint, storage_key)
            
            if storage_value:
                # Decode storage bytes to integer (Neo storage is typically BigInteger)
                if len(storage_value) <= 8:
                    # Small integer, decode as little-endian
                    result = int.from_bytes(storage_value, 'little', signed=False)
                    print(f"✅ Storage value: {result}")
                    return result
                else:
                    # Large integer, return as hex string for now
                    result = storage_value.hex()
                    print(f"✅ Storage value (hex): {result}")
                    return result
            else:
                # Storage not found, return 0
                print(f"⚠️  Storage key '{key}' not found, returning 0")
                return 0
                
        except Exception as e:
            error_msg = f"Failed to read from Neo blockchain: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e

class CallNeoContractTool(BaseTool):
    """
    Call a Neo smart contract function.
    
    Connects to Neo TestNet RPC and invokes methods on the deployed contract.
    """
    name: str = "call_neo_contract"
    description: str = "Call a Neo smart contract function."
    parameters: dict = {
        "type": "object",
        "properties": {"method": {"type": "string"}, "args": {"type": "array"}},
        "required": ["method"]
    }

    async def execute(self, method: str, args: Optional[list] = None) -> Dict[str, Any]:
        """
        Call a Neo smart contract function using real RPC calls.
        """
        # Validate configuration
        if not NEO3_AVAILABLE:
            raise RuntimeError(
                "neo3 library is not installed. Install with: pip install neo-mamba"
            )
        
        contract_hash_str = get_contract_hash()
        if not contract_hash_str:
            raise ValueError(
                "NEO_CONTRACT_HASH not set. Set it in .env or environment variables."
            )
        
        if not has_contract_hash():
            raise ValueError(
                f"Invalid contract hash format: {contract_hash_str}. "
                "Expected 40-character hex string (with or without 0x prefix)."
            )
        
        rpc_url = get_rpc_url()
        
        # Debug messages
        print(f"🔗 Using RPC: {rpc_url}")
        print(f"📝 Using Contract Hash: {contract_hash_str}")
        print(f"🔧 Calling method: {method}")
        if args:
            print(f"📦 Arguments: {args}")
        if NEO3_LIBRARY:
            print(f"📚 Using library: {NEO3_LIBRARY}")
        
        try:
            rpc = RPCClient(rpc_url)
            
            # Convert contract hash string to UInt160
            hash_str = contract_hash_str.replace("0x", "").replace("0X", "")
            contract_hash_uint = UInt160.from_string(hash_str)
            
            # Prepare arguments (convert to Neo VM stack items)
            # For simplicity, we'll pass args as-is and let neo3-python handle conversion
            neo_args = args or []
            
            # Call invokeFunction RPC method
            result = await rpc.invoke_function(contract_hash_uint, method, neo_args)
            
            print(f"✅ Method call successful")
            
            # Handle both dict-like and object-like responses
            if hasattr(result, 'gas_consumed'):
                # ExecutionResultResponse object
                gas_consumed = result.gas_consumed
                stack = result.stack if hasattr(result, 'stack') else []
                state = result.state if hasattr(result, 'state') else 'UNKNOWN'
            elif isinstance(result, dict):
                # Dict response
                gas_consumed = result.get('gas_consumed', 0)
                stack = result.get("stack", [])
                state = result.get("state", "UNKNOWN")
            else:
                # Fallback
                gas_consumed = 0
                stack = []
                state = "UNKNOWN"
            
            print(f"   Gas consumed: {gas_consumed}")
            print(f"   State: {state}")
            
            # Check if execution failed
            if state == "FAULT":
                # Try to get exception message
                exception_msg = None
                if hasattr(result, 'exception'):
                    exception_msg = result.exception
                elif hasattr(result, 'exception_message'):
                    exception_msg = result.exception_message
                
                error_msg = f"Contract method '{method}' execution failed (FAULT state)"
                if exception_msg:
                    error_msg += f": {exception_msg}"
                print(f"   ⚠️  {error_msg}")
                # Still return success=False but with details
                return {
                    "status": "failed",
                    "method": method,
                    "args": args or [],
                    "result": [],
                    "gas_consumed": gas_consumed,
                    "state": state,
                    "error": error_msg,
                    "raw_response": result
                }
            
            # Extract stack values if available
            stack_values = []
            if stack:
                for item in stack:
                    if hasattr(item, 'value'):
                        stack_values.append(item.value)
                    elif isinstance(item, dict):
                        stack_values.append(item.get('value', item))
                    else:
                        stack_values.append(item)
            
            return {
                "status": "success" if state == "HALT" else "failed",
                "method": method,
                "args": args or [],
                "result": stack_values if stack_values else stack,
                "gas_consumed": gas_consumed,
                "state": state,
                "raw_response": result
            }
                
        except Exception as e:
            error_msg = f"Failed to call Neo contract method '{method}': {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e

class OperationTool(BaseTool):
    name: str = "perform_operation"
    description: str = "Execute a math/logic operation."
    parameters: dict = {
        "type": "object",
        "properties": {"op": {"type": "string"}, "a": {}, "b": {}},
        "required": ["op", "a"]
    }

    async def execute(self, op: str, a: Any, b: Any = None) -> Any:
        """
        Execute a math/logic operation.
        Handles string-to-number conversion for operands.
        """
        # Convert operands to numbers if they're strings
        def to_number(val):
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return val
            if isinstance(val, str):
                try:
                    # Try integer first
                    if '.' not in val:
                        return int(val)
                    return float(val)
                except ValueError:
                    return val
            return val
        
        a = to_number(a)
        b = to_number(b)
        
        # Handle operations (support both symbols and names)
        if op in ("add", "+"):
            if b is None:
                raise ValueError(f"Operation 'add' requires two operands, got a={a}, b=None")
            return a + b
        if op in ("sub", "-", "subtract"):
            if b is None:
                raise ValueError(f"Operation 'sub' requires two operands, got a={a}, b=None")
            return a - b
        if op in ("mul", "*", "multiply"):
            if b is None:
                raise ValueError(f"Operation 'mul' requires two operands, got a={a}, b=None")
            return a * b
        if op in ("div", "/", "divide"):
            if b is None:
                raise ValueError(f"Operation 'div' requires two operands, got a={a}, b=None")
            if b == 0:
                raise ValueError("Division by zero")
            return a / b
        if op in ("and", "&&"):
            return bool(a and b)
        if op in ("or", "||"):
            return bool(a or b)
        raise ValueError(f"Unknown operation: {op}")

class DebugLogTool(BaseTool):
    name: str = "debug_log"
    description: str = "Send debug messages to the frontend."
    parameters: dict = {
        "type": "object",
        "properties": {"msg": {"type": "string"}},
        "required": ["msg"]
    }

    async def execute(self, msg: str) -> Dict[str, str]:
        return {"debug": msg}
