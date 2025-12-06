#!/usr/bin/env python
"""
Test script to verify live Neo TestNet connectivity.

This script:
1. Loads configuration from generator/config.py
2. Reads from contract storage
3. Calls a public method on the contract
4. Prints raw RPC responses

Usage:
    python test_live_chain.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from generator.config import (
    NEO_RPC_URL,
    NEO_CONTRACT_HASH,
    get_rpc_url,
    get_contract_hash,
    has_contract_hash
)

# Try to import neo3 (supports both neo-mamba and neo3-python)
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
    print("❌ ERROR: neo3 library is not installed")
    print("   Install with: pip install neo-mamba")
    print("   (neo-mamba works better with Python 3.13)")
    sys.exit(1)


async def test_rpc_connection():
    """Test basic RPC connectivity"""
    print("=" * 60)
    print("🔗 Testing Neo RPC Connection")
    print("=" * 60)
    
    rpc_url = get_rpc_url()
    print(f"RPC URL: {rpc_url}")
    
    try:
        rpc = RPCClient(rpc_url)
        
        # Test with getblockcount
        block_count = await rpc.get_block_count()
        print(f"✅ RPC connection successful!")
        print(f"   Current block height: {block_count}")
        return True
    except Exception as e:
        print(f"❌ RPC connection failed: {e}")
        return False


async def test_contract_hash():
    """Test contract hash configuration"""
    print("\n" + "=" * 60)
    print("📝 Testing Contract Hash Configuration")
    print("=" * 60)
    
    contract_hash = get_contract_hash()
    print(f"Contract Hash: {contract_hash}")
    
    if not contract_hash:
        print("❌ Contract hash is not set")
        print("   Set NEO_CONTRACT_HASH in .env or environment variables")
        return False
    
    if not has_contract_hash():
        print(f"❌ Invalid contract hash format: {contract_hash}")
        print("   Expected 40-character hex string (with or without 0x prefix)")
        return False
    
    print("✅ Contract hash is valid")
    return True


async def test_read_storage():
    """Test reading from contract storage"""
    print("\n" + "=" * 60)
    print("📖 Testing Contract Storage Read")
    print("=" * 60)
    
    rpc_url = get_rpc_url()
    contract_hash_str = get_contract_hash()
    
    print(f"RPC URL: {rpc_url}")
    print(f"Contract Hash: {contract_hash_str}")
    
    try:
        rpc = RPCClient(rpc_url)
        
        # Convert contract hash to UInt160
        hash_str = contract_hash_str.replace("0x", "").replace("0X", "")
        contract_hash_uint = UInt160.from_string(hash_str)
        
        # Try reading a common storage key (adjust based on your contract)
        test_keys = ["value", "counter", "version", "balance"]
        
        for key in test_keys:
            storage_key = key.encode('utf-8')
            print(f"\n🔍 Reading storage key: '{key}'")
            
            try:
                storage_value = await rpc.get_storage(contract_hash_uint, storage_key)
                
                if storage_value:
                    if len(storage_value) <= 8:
                        value = int.from_bytes(storage_value, 'little', signed=False)
                        print(f"   ✅ Value: {value} (as integer)")
                    else:
                        print(f"   ✅ Value (hex): {storage_value.hex()}")
                else:
                    print(f"   ⚠️  Key not found in storage")
                    
            except Exception as e:
                print(f"   ❌ Error reading key: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to read storage: {e}")
        return False


async def test_invoke_function():
    """Test calling a contract method"""
    print("\n" + "=" * 60)
    print("🔧 Testing Contract Method Invocation")
    print("=" * 60)
    
    rpc_url = get_rpc_url()
    contract_hash_str = get_contract_hash()
    
    print(f"RPC URL: {rpc_url}")
    print(f"Contract Hash: {contract_hash_str}")
    
    try:
        rpc = RPCClient(rpc_url)
        
        # Convert contract hash to UInt160
        hash_str = contract_hash_str.replace("0x", "").replace("0X", "")
        contract_hash_uint = UInt160.from_string(hash_str)
        
        # Try calling common methods (adjust based on your contract)
        test_methods = [
            ("Get", []),
            ("GetVersion", []),
            ("get", []),
        ]
        
        for method, args in test_methods:
            print(f"\n🔧 Calling method: {method}")
            if args:
                print(f"   Arguments: {args}")
            
            try:
                result = await rpc.invoke_function(contract_hash_uint, method, args)
                
                # Check if method call was successful
                if hasattr(result, 'state'):
                    state = result.state
                    print(f"   📊 Execution state: {state}")
                    
                    if state == 'HALT':
                        print(f"   ✅ Method call successful!")
                        
                        # Extract stack values
                        if hasattr(result, 'stack') and result.stack:
                            print(f"\n   📊 Stack values:")
                            for i, item in enumerate(result.stack):
                                print(f"      [{i}] {item}")
                                # Try to extract value if it's a StackItem
                                if hasattr(item, 'value'):
                                    print(f"         Value: {item.value}")
                        
                        if hasattr(result, 'gas_consumed'):
                            print(f"   ⛽ Gas consumed: {result.gas_consumed}")
                    else:
                        # FAULT state - method doesn't exist or error occurred
                        if hasattr(result, 'exception'):
                            print(f"   ⚠️  Method call failed: {result.exception}")
                        else:
                            print(f"   ⚠️  Method call failed (state: {state})")
                else:
                    # Fallback for dict-like responses
                    print(f"   ✅ Method call successful")
                    print(f"   📋 Raw RPC Response:")
                    import json
                    print(json.dumps(result, indent=4, default=str))
                    
                    # Extract stack values
                    stack = result.get("stack", []) if isinstance(result, dict) else []
                    if stack:
                        print(f"\n   📊 Stack values:")
                        for i, item in enumerate(stack):
                            print(f"      [{i}] {item}")
                    
                    gas = result.get('gas_consumed', 0) if isinstance(result, dict) else 0
                    print(f"   ⛽ Gas consumed: {gas}")
                
                # If we found a working method, return success
                return True
                
            except Exception as e:
                print(f"   ❌ Method call failed: {e}")
                continue
        
        print("\n⚠️  None of the test methods worked")
        print("   This might be normal if your contract has different method names")
        return False
        
    except Exception as e:
        print(f"❌ Failed to invoke function: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 Neo TestNet Live Chain Test")
    print("=" * 60)
    print()
    
    # Test 1: RPC Connection
    rpc_ok = await test_rpc_connection()
    if not rpc_ok:
        print("\n❌ RPC connection failed. Cannot continue.")
        sys.exit(1)
    
    # Test 2: Contract Hash
    hash_ok = await test_contract_hash()
    if not hash_ok:
        print("\n❌ Contract hash configuration invalid. Cannot continue.")
        sys.exit(1)
    
    # Test 3: Read Storage
    storage_ok = await test_read_storage()
    
    # Test 4: Invoke Function
    invoke_ok = await test_invoke_function()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"RPC Connection: {'✅' if rpc_ok else '❌'}")
    print(f"Contract Hash: {'✅' if hash_ok else '❌'}")
    print(f"Storage Read: {'✅' if storage_ok else '⚠️'}")
    print(f"Method Invocation: {'✅' if invoke_ok else '⚠️'}")
    print()
    
    if rpc_ok and hash_ok:
        print("✅ Basic connectivity is working!")
        print("   Your backend can connect to Neo TestNet")
    else:
        print("❌ Basic connectivity failed")
        print("   Check your RPC URL and contract hash configuration")


if __name__ == "__main__":
    asyncio.run(main())

