#!/usr/bin/env python
"""
Test Neo N3 Contract Deployment

This script tests the deployed contract by calling a method via RPC.

Usage:
    python test_deployment.py [method_name] [args...]

Example:
    python test_deployment.py getBalance
    python test_deployment.py transfer "from_address" "to_address" 100
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from neo3.api import RPCClient
    from neo3.core.types import UInt160
    NEO3_AVAILABLE = True
except ImportError:
    print("❌ ERROR: neo3-python is not installed")
    print("\nInstall it with:")
    print("  pip install neo3-python")
    sys.exit(1)

from deployment.config import get_contract_hash, NEO_RPC_URL, has_contract_hash, load_contract_info


async def test_contract_call(method_name: str = None, args: list = None):
    """Test calling a method on the deployed contract"""
    print("=" * 60)
    print("Neo N3 Contract Test")
    print("=" * 60)
    
    # Check if contract is deployed
    if not has_contract_hash():
        print("\n❌ ERROR: No contract hash found")
        print("\nPlease deploy a contract first:")
        print("  python deployment/deploy.py")
        return 1
    
    contract_hash = get_contract_hash()
    contract_info = load_contract_info()
    
    print(f"\n📋 Contract Information:")
    print(f"   Contract hash: {contract_hash}")
    print(f"   Transaction hash: {contract_info.get('tx_hash', 'N/A')}")
    print(f"   RPC URL: {NEO_RPC_URL}")
    
    # Connect to RPC
    print(f"\n🔗 Connecting to Neo RPC: {NEO_RPC_URL}")
    try:
        rpc = RPCClient(NEO_RPC_URL)
        
        # Test RPC connection
        print("   Testing RPC connection...")
        try:
            # Try to get block count
            block_count = await rpc.get_block_count()
            print(f"   ✅ Connected! Current block: {block_count}")
        except AttributeError:
            # Alternative: try getblockcount RPC call
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(NEO_RPC_URL, json={
                    "jsonrpc": "2.0",
                    "method": "getblockcount",
                    "params": [],
                    "id": 1
                }) as resp:
                    data = await resp.json()
                    block_count = data.get("result", "N/A")
                    print(f"   ✅ Connected! Current block: {block_count}")
        
    except Exception as e:
        print(f"   ❌ RPC connection failed: {e}")
        print(f"\nPlease check:")
        print(f"  1. RPC URL is correct: {NEO_RPC_URL}")
        print(f"  2. Network is accessible")
        print(f"  3. Firewall/proxy settings")
        return 1
    
    # Convert contract hash to UInt160
    try:
        hash_str = contract_hash.replace("0x", "")
        contract_hash_uint = UInt160.from_string(hash_str)
        print(f"\n✅ Contract hash parsed: {contract_hash_uint}")
    except Exception as e:
        print(f"\n❌ ERROR: Invalid contract hash format: {e}")
        return 1
    
    # Get method name from args or use default
    if not method_name:
        method_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not method_name:
        # Try to get a method from the contract manifest
        print(f"\n📝 No method specified. Testing contract existence...")
        try:
            # Try to get contract state
            contract_state = await rpc.get_contract_state(contract_hash_uint)
            print(f"   ✅ Contract found!")
            print(f"   Name: {contract_state.get('name', 'N/A')}")
            print(f"   Methods: {len(contract_state.get('methods', []))}")
            
            # List available methods
            methods = contract_state.get('methods', [])
            if methods:
                print(f"\n   Available methods:")
                for method in methods[:10]:  # Show first 10
                    print(f"     - {method.get('name', 'N/A')}")
            
            return 0
            
        except Exception as e:
            print(f"   ⚠️  Could not get contract state: {e}")
            print(f"\n   This might mean:")
            print(f"   - Contract is not yet confirmed on chain")
            print(f"   - Contract hash is incorrect")
            print(f"   - RPC method not available")
            return 1
    
    # Call the specified method
    print(f"\n📞 Calling contract method: {method_name}")
    if args:
        print(f"   Arguments: {args}")
    else:
        args = []
        # Parse additional args from command line
        if len(sys.argv) > 2:
            args = sys.argv[2:]
    
    try:
        # Convert string args to appropriate types
        neo_args = []
        for arg in args:
            # Try to convert to int if numeric
            try:
                if '.' in arg:
                    neo_args.append(float(arg))
                else:
                    neo_args.append(int(arg))
            except ValueError:
                # Keep as string
                neo_args.append(arg)
        
        # Invoke function
        print(f"   Invoking function...")
        result = await rpc.invoke_function(contract_hash_uint, method_name, neo_args)
        
        print(f"\n✅ Method call successful!")
        print(f"   Gas consumed: {result.get('gas_consumed', 'N/A')}")
        
        # Parse result stack
        stack = result.get('stack', [])
        if stack:
            print(f"   Result:")
            for i, item in enumerate(stack):
                print(f"     [{i}]: {item}")
        else:
            print(f"   Result: (empty)")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Method call failed: {e}")
        print(f"\nPossible reasons:")
        print(f"  - Method '{method_name}' does not exist")
        print(f"  - Wrong number or type of arguments")
        print(f"  - Contract execution error")
        print(f"  - RPC error")
        return 1


async def main():
    """Main test function"""
    method_name = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    return await test_contract_call(method_name, args)


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))

