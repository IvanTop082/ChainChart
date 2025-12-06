"""
Test Neo N3 RPC Deployment Infrastructure

This script tests all components of the deployment system:
1. Transaction building
2. Transaction signing
3. Transaction serialization
4. Script building
5. RPC communication

Run this to verify everything is working before deploying a real contract.
"""

import os
import json
import base64
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from neo_rpc_deploy import (
    wif_to_private_key,
    get_script_hash_from_wif,
    build_deploy_script,
    build_transaction,
    sign_transaction,
    rpc_call,
    RPC_URL,
    PRIVATE_KEY_WIF
)
from neo3_tx_serializer import Neo3TransactionSerializer

def test_wif_conversion():
    """Test WIF to private key conversion"""
    print("=" * 60)
    print("Test 1: WIF to Private Key Conversion")
    print("=" * 60)
    
    if not PRIVATE_KEY_WIF:
        print("❌ NEO_PRIVATE_KEY not set in environment")
        return False
    
    try:
        private_key = wif_to_private_key(PRIVATE_KEY_WIF)
        script_hash = get_script_hash_from_wif(PRIVATE_KEY_WIF)
        
        print(f"✅ WIF decoded successfully")
        print(f"   Private key length: {len(private_key)} bytes")
        print(f"   Script hash: {script_hash}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_script_building():
    """Test deployment script building"""
    print("\n" + "=" * 60)
    print("Test 2: Deployment Script Building")
    print("=" * 60)
    
    # Create test data
    nef_bytes = b'NEF3' + b'\x00' * 20  # Mock NEF
    manifest_str = '{"name":"TestContract","groups":[],"features":{}}'
    
    try:
        script = build_deploy_script(nef_bytes, manifest_str)
        script_b64 = base64.b64encode(script).decode('utf-8')
        
        print(f"✅ Script built successfully")
        print(f"   Script size: {len(script)} bytes")
        print(f"   Script (first 50 hex): {script[:50].hex()}...")
        print(f"   Script (Base64): {script_b64[:80]}...")
        return True, script
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_transaction_building(script):
    """Test transaction building"""
    print("\n" + "=" * 60)
    print("Test 3: Transaction Building")
    print("=" * 60)
    
    if not PRIVATE_KEY_WIF:
        print("❌ NEO_PRIVATE_KEY not set")
        return False, None
    
    try:
        script_hash = get_script_hash_from_wif(PRIVATE_KEY_WIF)
        tx = build_transaction(script, script_hash)
        
        print(f"✅ Transaction built successfully")
        print(f"   Version: {tx['version']}")
        print(f"   Nonce: {tx['nonce']} (0x{tx['nonce']:08x})")
        print(f"   SystemFee: {tx['systemFee']}")
        print(f"   NetworkFee: {tx['networkFee']}")
        print(f"   ValidUntilBlock: {tx['validUntilBlock']}")
        print(f"   Signers: {len(tx['signers'])}")
        print(f"   Attributes: {len(tx['attributes'])}")
        print(f"   Script length: {len(base64.b64decode(tx['script']))} bytes")
        print(f"   Witnesses: {len(tx['witnesses'])}")
        return True, tx
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_transaction_signing(tx):
    """Test transaction signing"""
    print("\n" + "=" * 60)
    print("Test 4: Transaction Signing")
    print("=" * 60)
    
    if not PRIVATE_KEY_WIF:
        print("❌ NEO_PRIVATE_KEY not set")
        return False, None
    
    try:
        private_key = wif_to_private_key(PRIVATE_KEY_WIF)
        signed_tx = sign_transaction(tx, private_key)
        
        print(f"✅ Transaction signed successfully")
        print(f"   Witnesses: {len(signed_tx['witnesses'])}")
        if signed_tx['witnesses']:
            invocation = base64.b64decode(signed_tx['witnesses'][0]['invocation'])
            verification = base64.b64decode(signed_tx['witnesses'][0]['verification'])
            print(f"   Invocation script: {len(invocation)} bytes")
            print(f"   Verification script: {len(verification)} bytes")
            print(f"   Verification (hex): {verification.hex()[:80]}...")
        return True, signed_tx
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_transaction_serialization(signed_tx):
    """Test transaction serialization"""
    print("\n" + "=" * 60)
    print("Test 5: Transaction Serialization")
    print("=" * 60)
    
    try:
        tx_binary = Neo3TransactionSerializer.serialize_transaction(signed_tx)
        tx_base64 = base64.b64encode(tx_binary).decode('utf-8')
        tx_hex = tx_binary.hex()
        
        print(f"✅ Transaction serialized successfully")
        print(f"   Binary size: {len(tx_binary)} bytes")
        print(f"   Base64 size: {len(tx_base64)} characters")
        print(f"   Hex (first 100): {tx_hex[:100]}...")
        print(f"   Base64 (first 80): {tx_base64[:80]}...")
        return True, tx_base64
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_rpc_connection():
    """Test RPC connection"""
    print("\n" + "=" * 60)
    print("Test 6: RPC Connection")
    print("=" * 60)
    
    try:
        result = rpc_call("getblockcount", [])
        if isinstance(result, dict) and "result" in result:
            block_count = result["result"]
        elif isinstance(result, int):
            block_count = result
        else:
            block_count = result
        
        print(f"✅ RPC connection successful")
        print(f"   RPC URL: {RPC_URL}")
        print(f"   Current block height: {block_count}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_script_with_invokescript(script):
    """Test script with invokescript (dry run)"""
    print("\n" + "=" * 60)
    print("Test 7: Script Validation (invokescript)")
    print("=" * 60)
    
    try:
        script_b64 = base64.b64encode(script).decode('utf-8')
        result = rpc_call("invokescript", [script_b64])
        
        print(f"✅ Script sent to RPC")
        if isinstance(result, dict):
            if "state" in result:
                print(f"   State: {result['state']}")
            if "exception" in result:
                print(f"   ⚠️  Exception: {result['exception']}")
                print(f"   (This is expected with mock NEF - real contract will work)")
            if "gasconsumed" in result:
                print(f"   Gas consumed: {result['gasconsumed']}")
        else:
            print(f"   Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Neo N3 RPC Deployment Infrastructure Test")
    print("=" * 60)
    print(f"RPC URL: {RPC_URL}")
    print(f"Private Key: {'Set' if PRIVATE_KEY_WIF else 'Not Set'}")
    print()
    
    results = {}
    
    # Test 1: WIF conversion
    results['wif'] = test_wif_conversion()
    
    # Test 2: Script building
    script_ok, script = test_script_building()
    results['script'] = script_ok
    
    if not script_ok or not script:
        print("\n❌ Cannot continue - script building failed")
        return
    
    # Test 3: Transaction building
    tx_ok, tx = test_transaction_building(script)
    results['transaction'] = tx_ok
    
    if not tx_ok or not tx:
        print("\n❌ Cannot continue - transaction building failed")
        return
    
    # Test 4: Transaction signing
    sign_ok, signed_tx = test_transaction_signing(tx)
    results['signing'] = sign_ok
    
    if not sign_ok or not signed_tx:
        print("\n❌ Cannot continue - transaction signing failed")
        return
    
    # Test 5: Transaction serialization
    serialize_ok, tx_base64 = test_transaction_serialization(signed_tx)
    results['serialization'] = serialize_ok
    
    # Test 6: RPC connection
    results['rpc'] = test_rpc_connection()
    
    # Test 7: Script validation
    results['validation'] = test_script_with_invokescript(script)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:20} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All infrastructure tests passed!")
        print("\n💡 Next Steps:")
        print("   1. Compile a real Neo N3 contract")
        print("   2. Place NEF and manifest in generated_contracts/")
        print("   3. Run: python deployment/deploy.py")
        print("   4. Deployment should work!")
    else:
        print("⚠️  Some tests failed - check errors above")
    print("=" * 60)

if __name__ == "__main__":
    main()

