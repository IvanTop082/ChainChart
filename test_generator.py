"""
Quick test script for Phase 3 deterministic contract generator
"""

from generator.neo_contract_generator import generate_contract_from_diagram
from generator.neo_compiler import compile_contract, read_compiled_files
import tempfile
from pathlib import Path

def test_generation():
    """Test 1: JSON → C# Generation"""
    print("\n" + "="*60)
    print("TEST 1: JSON → C# Generation")
    print("="*60)
    
    test_diagram = {
        "nodes": [
            {"id": "1", "type": "state", "data": {"label": "balance"}},
            {"id": "2", "type": "function", "data": {
                "name": "transfer",
                "params": ["UInt160 to", "BigInteger amount"],
                "visibility": "public"
            }},
            {"id": "3", "type": "event", "data": {
                "name": "Transfer",
                "params": "UInt160 from, UInt160 to, BigInteger amount"
            }}
        ],
        "edges": [
            {"from": "1", "to": "2"},
            {"from": "2", "to": "3"}
        ]
    }
    
    contract = generate_contract_from_diagram(test_diagram)
    
    print(f"✅ Contract generated ({len(contract)} chars)")
    
    # Verify components
    assert "StorageMap balanceMap" in contract, "Missing storage variable"
    assert "public static void transfer" in contract, "Missing function"
    assert "public static event Action" in contract, "Missing event"
    
    print("✅ StorageMap balanceMap found")
    print("✅ Function transfer found")
    print("✅ Event Transfer found")
    
    # Test 2: Compile
    print("\n" + "="*60)
    print("TEST 2: Compile Contract")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        contract_file = Path(temp_dir) / "Contract.cs"
        contract_file.write_text(contract, encoding='utf-8')
        
        nef_path, manifest_path, success = compile_contract(str(contract_file))
        
        print(f"✅ Compilation attempted")
        print(f"   NEF: {nef_path}")
        print(f"   Manifest: {manifest_path}")
        print(f"   Success: {success}")
        
        if nef_path and manifest_path:
            compiled = read_compiled_files(nef_path, manifest_path)
            print(f"✅ NEF size: {len(compiled['nef'])} chars (base64)")
            print(f"✅ Manifest keys: {list(compiled['manifest'].keys())}")
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_generation()

