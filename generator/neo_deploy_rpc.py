"""
Alternative Neo Contract Deployment using Direct RPC Calls
This bypasses neo-mamba's signing issues by using RPC's sendrawtransaction
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
import requests


def deploy_via_rpc_raw(nef_path: str, manifest_path: str, private_key: Optional[str] = None, rpc_url: str = None) -> Dict[str, Any]:
    """
    Deploy contract using direct RPC calls.
    
    NOTE: invokecontract doesn't exist in Neo N3 RPC - this method is deprecated.
    Use neo_rpc_deploy.py instead which uses sendrawtransaction.
    """
    # This method is deprecated - invokecontract doesn't exist in Neo N3
    return {
        "success": False,
        "tx_hash": None,
        "error": "invokecontract method not available in Neo N3 RPC. Use neo_rpc_deploy.py instead.",
        "mock": False
    }
    try:
        # Read files
        nef_file = Path(nef_path)
        manifest_file = Path(manifest_path)
        
        if not nef_file.exists() or not manifest_file.exists():
            return {
                "success": False,
                "tx_hash": None,
                "error": "NEF or manifest file not found",
                "mock": False
            }
        
        nef_content = nef_file.read_bytes()
        manifest_content = json.loads(manifest_file.read_text(encoding='utf-8'))
        
        if not rpc_url:
            rpc_url = os.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")
        
        if not private_key:
            private_key = os.getenv("NEO_PRIVATE_KEY", "")
        
        if not private_key:
            return {
                "success": False,
                "tx_hash": None,
                "error": "Private key required for deployment",
                "mock": False
            }
        
        # ContractManagement script hash
        contract_mgmt_hash = "0xfffdc93764dbaddd97c48f252a53ea4643faa3fd"
        
        # Prepare parameters for deploy
        # Deploy expects: (nef: ByteString, manifest: ByteString)
        params = [
            {
                "type": "ByteString",
                "value": nef_content.hex()
            },
            {
                "type": "ByteString", 
                "value": json.dumps(manifest_content).encode('utf-8').hex()
            }
        ]
        
        # Use RPC invokecontract to build and sign the transaction
        # This RPC method handles transaction building and signing automatically
        rpc_payload = {
            "jsonrpc": "2.0",
            "method": "invokecontract",
            "params": [
                contract_mgmt_hash,
                "deploy",
                params,
                [private_key]  # Signers - RPC will handle signing
            ],
            "id": 1
        }
        
        print(f"🔗 Calling RPC invokecontract at {rpc_url}...")
        response = requests.post(rpc_url, json=rpc_payload, timeout=30)
        
        if response.status_code != 200:
            return {
                "success": False,
                "tx_hash": None,
                "error": f"RPC call failed: HTTP {response.status_code}",
                "mock": False
            }
        
        result = response.json()
        
        if "error" in result:
            return {
                "success": False,
                "tx_hash": None,
                "error": f"RPC error: {result['error']}",
                "mock": False
            }
        
        # Extract transaction hash from result
        tx_hash = result.get("result", {}).get("txid") or result.get("result", {}).get("hash")
        
        if tx_hash:
            if not str(tx_hash).startswith("0x"):
                tx_hash = "0x" + str(tx_hash)
            
            return {
                "success": True,
                "tx_hash": tx_hash,
                "error": None,
                "mock": False
            }
        else:
            return {
                "success": False,
                "tx_hash": None,
                "error": f"RPC did not return transaction hash. Result: {result}",
                "mock": False
            }
            
    except Exception as e:
        return {
            "success": False,
            "tx_hash": None,
            "error": f"Deployment failed: {str(e)}",
            "mock": False
        }

