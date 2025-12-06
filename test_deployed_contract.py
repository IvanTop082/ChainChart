#!/usr/bin/env python
"""
Test the deployed contract to confirm it's working
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generator.config import get_rpc_url, get_contract_hash
from neo3.api import NeoRpcClient
from neo3.core.types import UInt160

async def test_contract():
    """Test the deployed contract"""
    
    print("=" * 60)
    print("🧪 Testing Deployed Contract")
    print("=" * 60)
    print()
    
    rpc_url = get_rpc_url()
    contract_hash_str = get_contract_hash()
    
    print(f"🔗 RPC URL: {rpc_url}")
    print(f"📝 Contract Hash: {contract_hash_str}")
    print()
    
    try:
        rpc = NeoRpcClient(rpc_url)
        
        # Convert contract hash to UInt160
        hash_str = contract_hash_str.replace("0x", "").replace("0X", "")
        contract_hash_uint = UInt160.from_string(hash_str)
        
        # Test 1: Call the 'get' method (lowercase - this is what works)
        print("🔧 Calling method: get")
        result = await rpc.invoke_function(contract_hash_uint, "get", [])
        
        if hasattr(result, 'state'):
            print(f"   📊 Execution state: {result.state}")
            
            if result.state == 'HALT':
                print("   ✅ Method call successful!")
                
                if hasattr(result, 'stack') and result.stack:
                    for i, item in enumerate(result.stack):
                        print(f"   📊 Stack[{i}]: {item}")
                        if hasattr(item, 'value'):
                            print(f"      Value: {item.value}")
                
                if hasattr(result, 'gas_consumed'):
                    print(f"   ⛽ Gas consumed: {result.gas_consumed}")
                
                print()
                print("=" * 60)
                print("✅ CONTRACT IS DEPLOYED AND WORKING!")
                print("=" * 60)
                print()
                print("📋 Summary:")
                print(f"   ✅ Contract exists on TestNet")
                print(f"   ✅ Contract hash: {contract_hash_str}")
                print(f"   ✅ Method 'get' is callable")
                print(f"   ✅ Returns value: {result.stack[0].value if result.stack else 'N/A'}")
                print()
                print("🔍 View on TestNet Explorer:")
                print(f"   https://dora.coz.io/neotracker/testnet/contract/{contract_hash_str}")
                print()
                print("✅ Your backend can use this contract!")
                print("   The contract hash in .env is correct and working.")
                return True
            else:
                print(f"   ⚠️  Method call failed: {result.exception if hasattr(result, 'exception') else 'Unknown error'}")
                return False
        else:
            print(f"   ❌ Unexpected result format: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing contract: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_contract())
    sys.exit(0 if success else 1)

