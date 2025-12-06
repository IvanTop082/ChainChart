"""
Test script for Phase 3 - Contract Generation, Compilation, and Deployment
Tests all three endpoints: generate-contract, compile-contract, deploy-contract
"""

import asyncio
import json
import requests
from typing import Dict, Any

# API base URL
API_BASE = "http://localhost:8000"

# Test diagram - simple contract with state, function, and event
TEST_DIAGRAM = {
    "nodes": [
        {
            "id": "1",
            "type": "state",
            "data": {
                "label": "balance",
                "dataType": "BigInteger",
                "visibility": "public"
            }
        },
        {
            "id": "2",
            "type": "function",
            "data": {
                "name": "transfer",
                "params": ["BigInteger amount", "ByteString to"],
                "visibility": "public"
            }
        },
        {
            "id": "3",
            "type": "event",
            "data": {
                "name": "Transfer",
                "params": "ByteString from, ByteString to, BigInteger amount"
            }
        },
        {
            "id": "4",
            "type": "operation",
            "data": {
                "op": "sub",
                "a": "balance",
                "b": "amount"
            }
        }
    ],
    "edges": [
        {"from": "1", "to": "2"},
        {"from": "2", "to": "4"},
        {"from": "4", "to": "3"}
    ]
}


def test_generate_contract():
    """Test contract generation endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Generate Contract")
    print("="*60)
    
    url = f"{API_BASE}/generate-contract"
    
    # Transform to UI format (as the endpoint expects)
    ui_nodes = []
    for node in TEST_DIAGRAM["nodes"]:
        ui_node = {
            "id": node["id"],
            "type": node["type"],
            "label": node["data"].get("name") or node["data"].get("label", ""),
            "value": "",
            "position": {"x": 0, "y": 0},
            "metadata": node["data"]
        }
        ui_nodes.append(ui_node)
    
    payload = {
        "nodes": ui_nodes,
        "edges": TEST_DIAGRAM["edges"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Success: {result.get('success')}")
        
        if result.get("contract_text"):
            contract = result["contract_text"]
            print(f"\n📄 Generated Contract ({len(contract)} chars):")
            print("-" * 60)
            # Show first 500 chars
            print(contract[:500])
            if len(contract) > 500:
                print(f"\n... ({len(contract) - 500} more characters)")
            print("-" * 60)
            
            return contract
        else:
            print(f"❌ Error: {result.get('error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def test_compile_contract(contract_text: str):
    """Test contract compilation endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Compile Contract")
    print("="*60)
    
    if not contract_text:
        print("❌ No contract text to compile")
        return None
    
    url = f"{API_BASE}/compile-contract"
    payload = {
        "contract_text": contract_text
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Success: {result.get('success')}")
        print(f"✅ Mock: {result.get('mock', False)}")
        
        if result.get("nef"):
            nef = result["nef"]
            print(f"\n📦 NEF (base64): {len(nef)} chars")
            print(f"   Preview: {nef[:50]}...")
        
        if result.get("manifest"):
            manifest = result["manifest"]
            print(f"\n📋 Manifest (JSON): {len(manifest)} chars")
            try:
                manifest_obj = json.loads(manifest)
                print(f"   Contract Name: {manifest_obj.get('name', 'N/A')}")
                print(f"   Methods: {len(manifest_obj.get('abi', {}).get('methods', []))}")
            except:
                pass
        
        if result.get("error"):
            print(f"\n⚠️  Warning: {result['error']}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def test_deploy_contract(compile_result: Dict[str, Any]):
    """Test contract deployment endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Deploy Contract")
    print("="*60)
    
    if not compile_result or not compile_result.get("nef"):
        print("❌ No compiled contract to deploy")
        return None
    
    url = f"{API_BASE}/deploy-contract"
    payload = {
        "nef": compile_result["nef"],
        "manifest": compile_result["manifest"],
        # wallet_private_key: Optional - only needed for real deployment
        # rpc_url: Optional - defaults to testnet
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Success: {result.get('success')}")
        print(f"✅ Mock: {result.get('mock', False)}")
        
        if result.get("txid"):
            print(f"\n🔗 Transaction ID: {result['txid']}")
        
        if result.get("error"):
            print(f"\n⚠️  Warning: {result['error']}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def test_full_pipeline():
    """Test the complete pipeline: generate → compile → deploy"""
    print("\n" + "="*60)
    print("PHASE 3 FULL PIPELINE TEST")
    print("="*60)
    
    # Step 1: Generate contract
    contract_text = test_generate_contract()
    if not contract_text:
        print("\n❌ Pipeline stopped: Contract generation failed")
        return
    
    # Step 2: Compile contract
    compile_result = test_compile_contract(contract_text)
    if not compile_result:
        print("\n❌ Pipeline stopped: Contract compilation failed")
        return
    
    # Step 3: Deploy contract
    deploy_result = test_deploy_contract(compile_result)
    if not deploy_result:
        print("\n❌ Pipeline stopped: Contract deployment failed")
        return
    
    print("\n" + "="*60)
    print("✅ FULL PIPELINE TEST COMPLETE")
    print("="*60)
    print("\nSummary:")
    print(f"  - Contract Generated: ✅ ({len(contract_text)} chars)")
    print(f"  - Contract Compiled: {'✅' if compile_result.get('success') else '⚠️'} (Mock: {compile_result.get('mock')})")
    print(f"  - Contract Deployed: {'✅' if deploy_result.get('success') else '⚠️'} (Mock: {deploy_result.get('mock')})")
    if deploy_result.get("txid"):
        print(f"  - Transaction ID: {deploy_result['txid']}")


def test_health_check():
    """Test API health check"""
    print("\n" + "="*60)
    print("HEALTH CHECK")
    print("="*60)
    
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        response.raise_for_status()
        result = response.json()
        print(f"✅ API is running: {result}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ API is not running: {e}")
        print(f"\n💡 Make sure to start the API server first:")
        print(f"   python api_server.py")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CHAINCHART PHASE 3 TEST SUITE")
    print("="*60)
    
    # Check if API is running
    if not test_health_check():
        exit(1)
    
    # Run full pipeline test
    test_full_pipeline()
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\n💡 Notes:")
    print("  - If compilation/deployment shows 'mock: true', install Neo tooling")
    print("  - For real compilation: dotnet tool install -g Neo.Compiler.CSharp")
    print("  - For real deployment: pip install neo-mamba")
    print("="*60 + "\n")

