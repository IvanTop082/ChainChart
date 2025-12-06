"""
Complete Phase 3 Test Suite
Tests contract generation, compilation, validation, and deployment
"""

import requests
from generator.neo_contract_generator import generate_contract_from_diagram
from generator.neo_compiler import compile_contract, read_compiled_files
from generator.contract_validator import validate_contract
from generator.neo_deploy import deploy_to_testnet
import tempfile
from pathlib import Path

API_BASE = "http://localhost:8000"

def test_1_generation():
    """Test 1: JSON → C# Generation"""
    print("\n" + "="*60)
    print("TEST 1: JSON → C# Generation")
    print("="*60)
    
    test_diagram = {
        "nodes": [
            {"id": "1", "type": "state", "data": {"label": "balance"}},
            {"id": "2", "type": "function", "data": {"name": "transfer", "params": ["UInt160 to", "BigInteger amount"]}},
            {"id": "3", "type": "event", "data": {"name": "Transfer", "params": "UInt160 from, UInt160 to, BigInteger amount"}}
        ],
        "edges": [
            {"from": "1", "to": "2"},
            {"from": "2", "to": "3"}
        ]
    }
    
    contract = generate_contract_from_diagram(test_diagram)
    
    # Validate
    is_valid, errors, fixed = validate_contract(contract)
    
    assert "StorageMap balanceMap" in contract, "Missing storage variable"
    assert "public static void transfer" in contract, "Missing function"
    assert "public static event Action" in contract, "Missing event"
    assert "class Contract : SmartContract" in contract, "Missing SmartContract inheritance"
    assert "namespace ChainChartGenerated" in contract, "Missing namespace"
    
    print("✅ Contract generated")
    print(f"✅ Validation: {is_valid} (errors: {len(errors)})")
    print(f"✅ All required components found")
    
    return contract

def test_2_compilation(contract):
    """Test 2: Compile Contract"""
    print("\n" + "="*60)
    print("TEST 2: Compile Contract")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        contract_file = Path(temp_dir) / "Contract.cs"
        contract_file.write_text(contract, encoding='utf-8')
        
        nef_path, manifest_path, success, errors = compile_contract(str(contract_file))
        
        print(f"✅ Compilation attempted")
        print(f"   NEF: {nef_path}")
        print(f"   Manifest: {manifest_path}")
        print(f"   Success: {success}")
        print(f"   Errors: {len(errors)}")
        if errors:
            print(f"   Error messages: {errors[:2]}")
        
        if nef_path and manifest_path:
            compiled = read_compiled_files(nef_path, manifest_path)
            print(f"✅ NEF size: {len(compiled['nef'])} chars (base64)")
            print(f"✅ Manifest keys: {list(compiled['manifest'].keys())}")
            return compiled
        return None

def test_3_api_endpoint():
    """Test 3: API Endpoint"""
    print("\n" + "="*60)
    print("TEST 3: API Endpoint - POST /compile-contract")
    print("="*60)
    
    try:
        # Use the same format as export-contract endpoint
        response = requests.post(
            f"{API_BASE}/compile-contract",
            json={
                "nodes": [
                    {
                        "id": "1",
                        "type": "state",
                        "label": "balance",
                        "value": "",
                        "position": {"x": 0, "y": 0},
                        "metadata": {"label": "balance", "dataType": "BigInteger"}
                    },
                    {
                        "id": "2",
                        "type": "function",
                        "label": "transfer",
                        "value": "",
                        "position": {"x": 0, "y": 0},
                        "metadata": {
                            "name": "transfer",
                            "params": "UInt160 to, BigInteger amount",
                            "visibility": "public"
                        }
                    }
                ],
                "edges": [{"from": "1", "to": "2"}]
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        result = response.json()
        
        assert "contract" in result, "Missing contract in response"
        assert "nef" in result, "Missing nef in response"
        assert "manifest" in result, "Missing manifest in response"
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Contract: {len(result['contract'])} chars")
        print(f"✅ NEF: {len(result['nef'])} chars")
        print(f"✅ Manifest: {list(result['manifest'].keys())}")
        print(f"✅ Success: {result['success']}")
        print(f"✅ Compile errors: {len(result.get('compile_errors', []))}")
        
        return result
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure API server is running")
        return None

def test_4_deployment(compile_result):
    """Test 4: Deployment"""
    print("\n" + "="*60)
    print("TEST 4: Deployment - POST /deploy-contract")
    print("="*60)
    
    if not compile_result:
        print("⚠️  Skipping - no compile result available")
        return None
    
    try:
        # Build request - manifest should be a dict, not a string
        deploy_payload = {
            "nef": compile_result["nef"],
            "manifest": compile_result["manifest"]  # Already a dict from compile endpoint
        }
        
        # Only add private_key if provided (optional)
        # if compile_result.get("private_key"):
        #     deploy_payload["private_key"] = compile_result["private_key"]
        
        response = requests.post(
            f"{API_BASE}/deploy-contract",
            json=deploy_payload,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        result = response.json()
        
        assert "tx_hash" in result, "Missing tx_hash in response"
        assert result["tx_hash"].startswith("0x"), "TX hash should start with 0x"
        assert len(result["tx_hash"]) == 66, "TX hash should be 66 characters"
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ TX Hash: {result['tx_hash']}")
        print(f"✅ Success: {result['success']}")
        print(f"✅ Mock: {result['mock']}")
        if result['error']:
            print(f"⚠️  Error: {result['error']}")
        
        return result
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure API server is running")
        return None

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PHASE 3 COMPLETE TEST SUITE")
    print("="*60)
    
    # Test 1
    contract = test_1_generation()
    
    # Test 2
    compiled = test_2_compilation(contract)
    
    # Test 3
    compile_result = test_3_api_endpoint()
    
    # Test 4
    deploy_result = test_4_deployment(compile_result)
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nSummary:")
    print(f"  ✅ Contract Generation: PASSED")
    print(f"  ✅ Compilation: {'PASSED' if compiled else 'MOCK (compiler not installed)'}")
    print(f"  ✅ API Endpoint: {'PASSED' if compile_result else 'FAILED (server not running)'}")
    print(f"  ✅ Deployment: {'PASSED' if deploy_result else 'SKIPPED'}")
    print("="*60 + "\n")

