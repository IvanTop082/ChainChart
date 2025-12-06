# Neo Blockchain Integration Guide

## Current Status

The ChainChart execution engine currently uses **mocked Neo tools** for testing. The tools return hardcoded values instead of reading from/writing to the actual Neo blockchain.

## Mocked Tools

1. **ReadNeoStateTool** - Returns hardcoded values from a dictionary
2. **CallNeoContractTool** - Returns a mock response without calling a real contract

## How to Integrate Real Neo Blockchain

### Option 1: Using neo3-python (Recommended)

```python
# Install: pip install neo3-python
from neo3.api import RPCClient
from neo3.core.types import UInt160

class ReadNeoStateTool(BaseTool):
    async def execute(self, key: str) -> Any:
        # Connect to Neo RPC node
        rpc = RPCClient("https://seed1t4.neo.org:20331")  # TestNet
        
        # Get contract hash (you need to know which contract to read from)
        contract_hash = UInt160.from_string("your_contract_hash_here")
        
        # Read storage value
        storage_key = key.encode('utf-8')
        result = await rpc.get_storage(contract_hash, storage_key)
        
        # Convert Neo storage format to Python value
        if result:
            return int.from_bytes(result, 'little')  # For numeric values
        return 0
```

### Option 2: Using neo-mamba

```python
# Install: pip install neo-mamba
from mamba import NeoRPC

class ReadNeoStateTool(BaseTool):
    def __init__(self):
        self.rpc = NeoRPC("https://seed1t4.neo.org:20331")
    
    async def execute(self, key: str) -> Any:
        # Read from contract storage
        contract_hash = "your_contract_hash_here"
        storage_key = key.encode('utf-8')
        
        result = await self.rpc.get_storage(contract_hash, storage_key)
        return int.from_bytes(result, 'little') if result else 0
```

### Option 3: Using HTTP RPC directly

```python
import aiohttp
import base64

class ReadNeoStateTool(BaseTool):
    async def execute(self, key: str) -> Any:
        rpc_url = "https://seed1t4.neo.org:20331"
        
        # Neo RPC call to getStorage
        payload = {
            "jsonrpc": "2.0",
            "method": "getstorage",
            "params": ["contract_hash_here", base64.b64encode(key.encode()).decode()],
            "id": 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(rpc_url, json=payload) as response:
                data = await response.json()
                if data.get("result"):
                    # Decode the storage value
                    storage_bytes = base64.b64decode(data["result"])
                    return int.from_bytes(storage_bytes, 'little')
        return 0
```

## For Contract Calls

```python
class CallNeoContractTool(BaseTool):
    async def execute(self, method: str, args: Optional[list] = None) -> Dict[str, Any]:
        rpc = RPCClient("https://seed1t4.neo.org:20331")
        contract_hash = UInt160.from_string("your_contract_hash_here")
        
        # Invoke contract method
        result = await rpc.invoke_function(
            contract_hash,
            method,
            args or []
        )
        
        return {
            "status": "success",
            "result": result,
            "method": method
        }
```

## Configuration

Add environment variables for Neo connection:

```python
import os

NEO_RPC_URL = os.getenv("NEO_RPC_URL", "https://seed1t4.neo.org:20331")
NEO_CONTRACT_HASH = os.getenv("NEO_CONTRACT_HASH", "")
NEO_NETWORK = os.getenv("NEO_NETWORK", "testnet")  # testnet or mainnet
```

## Testing

1. **With Mocked Tools** (Current):
   - Works without blockchain connection
   - Good for development and testing
   - Fast execution

2. **With Real Neo TestNet**:
   - Requires Neo TestNet RPC access
   - Need deployed contract hash
   - Slower (network calls)
   - Real blockchain state

3. **With Neo Express (Local)**:
   - Run local Neo blockchain
   - Fast, no network needed
   - Good for development

## Next Steps

1. Choose a Neo RPC client library
2. Update `ReadNeoStateTool.execute()` to use RPC calls
3. Update `CallNeoContractTool.execute()` to invoke real contracts
4. Add configuration for RPC URL and contract hash
5. Handle errors (network failures, contract not found, etc.)
6. Add authentication if needed (for private nodes)

