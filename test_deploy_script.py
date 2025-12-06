"""
Test the deployment script format using invokescript
"""

import json
import base64
from pathlib import Path
from neo3_contract_builder import ScriptBuilder

def build_deploy_script(nef_bytes: bytes, manifest_str: str) -> bytes:
    """Build deployment script"""
    sb = ScriptBuilder()
    
    # Push NEF as bytes first
    sb.emit_push(nef_bytes)
    
    # Push manifest as bytes
    manifest_bytes = manifest_str.encode('utf-8') if isinstance(manifest_str, str) else manifest_str
    sb.emit_push(manifest_bytes)
    
    # Call ContractManagement.deploy using CALLT
    contract_hash_hex = "fffdc93764dbaddd97c48f252a53ea4643faa3fd"
    contract_hash_bytes = bytes.fromhex(contract_hash_hex)
    contract_hash_bytes = contract_hash_bytes[::-1]  # little-endian
    
    sb.emit_contract_call(contract_hash_bytes, "deploy")
    
    return sb.to_array()

def test_script():
    """Test the deployment script using invokescript"""
    import requests
    import os
    
    rpc_url = os.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")
    
    # Load NEF and manifest
    nef_path = Path("generated_contracts/contract.nef")
    manifest_path = Path("generated_contracts/contract.manifest.json")
    
    if not nef_path.exists() or not manifest_path.exists():
        print("❌ Contract files not found!")
        return
    
    with open(nef_path, "rb") as f:
        nef_bytes = f.read()
    
    with open(manifest_path, "r", encoding='utf-8') as f:
        manifest_json = json.load(f)
        manifest_str = json.dumps(manifest_json, separators=(',', ':'))
    
    print("=" * 60)
    print("Testing Deployment Script")
    print("=" * 60)
    print(f"NEF size: {len(nef_bytes)} bytes")
    print(f"Manifest size: {len(manifest_str)} bytes")
    print()
    
    # Build script
    script = build_deploy_script(nef_bytes, manifest_str)
    script_b64 = base64.b64encode(script).decode('utf-8')
    
    print(f"Script size: {len(script)} bytes")
    print(f"Script (first 100 hex): {script[:100].hex()}...")
    print()
    
    # Test with invokescript
    print("Testing with invokescript...")
    payload = {
        "jsonrpc": "2.0",
        "method": "invokescript",
        "params": [script_b64],
        "id": 1
    }
    
    try:
        response = requests.post(rpc_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print("Response:")
        print(json.dumps(result, indent=2))
        
        if "error" in result:
            print()
            print("❌ Error:", result["error"])
        elif "result" in result:
            print()
            print("✅ Script executed (check result for details)")
            if "exception" in result.get("result", {}):
                print("⚠️  Exception:", result["result"]["exception"])
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_script()

