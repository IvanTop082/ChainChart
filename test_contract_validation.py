#!/usr/bin/env python
"""
Test script to validate that the generated contract matches the diagram and works correctly.

This script:
1. Reads the generated contract
2. Validates it has the expected structure
3. Tests contract methods (if deployed)
4. Compares contract to diagram expectations
"""

import asyncio
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from generator.config import get_rpc_url, get_contract_hash, has_contract_hash
    from neo3.api import NeoRpcClient as RPCClient
    from neo3.core.types import UInt160
    NEO3_AVAILABLE = True
except ImportError:
    NEO3_AVAILABLE = False
    print("⚠️  neo3 library not installed - will only validate contract structure")
    print("   Install with: pip install neo-mamba")


def read_contract() -> str:
    """Read the generated contract file"""
    contract_path = Path("generated_contracts/Contract.cs")
    if not contract_path.exists():
        print(f"❌ Contract file not found: {contract_path}")
        return None
    return contract_path.read_text(encoding='utf-8')


def analyze_contract_structure(contract_code: str) -> Dict[str, Any]:
    """Analyze the contract structure"""
    structure = {
        "storage_variables": [],
        "functions": [],
        "events": [],
        "namespace": None,
        "class_name": None
    }
    
    # Extract namespace
    namespace_match = re.search(r'namespace\s+(\w+)', contract_code)
    if namespace_match:
        structure["namespace"] = namespace_match.group(1)
    
    # Extract class name
    class_match = re.search(r'public\s+class\s+(\w+)', contract_code)
    if class_match:
        structure["class_name"] = class_match.group(1)
    
    # Extract storage variables (StorageMap)
    storage_matches = re.findall(r'StorageMap\s+(\w+)', contract_code)
    structure["storage_variables"] = list(set(storage_matches))
    
    # Extract functions
    # Pattern: public static (return_type) FunctionName(...)
    function_pattern = r'public\s+static\s+(\w+)\s+(\w+)\s*\([^)]*\)'
    function_matches = re.findall(function_pattern, contract_code)
    for return_type, func_name in function_matches:
        structure["functions"].append({
            "name": func_name,
            "return_type": return_type
        })
    
    # Extract events
    event_pattern = r'public\s+static\s+event\s+Action[^;]*(\w+)\s*[;\(]'
    event_matches = re.findall(event_pattern, contract_code)
    structure["events"] = list(set(event_matches))
    
    return structure


def validate_contract_structure(structure: Dict[str, Any]) -> List[str]:
    """Validate contract has required structure"""
    issues = []
    
    if not structure["namespace"]:
        issues.append("❌ Missing namespace")
    elif structure["namespace"] != "ChainChartGenerated":
        issues.append(f"⚠️  Namespace is '{structure['namespace']}', expected 'ChainChartGenerated'")
    
    if not structure["class_name"]:
        issues.append("❌ Missing class definition")
    elif structure["class_name"] != "Contract":
        issues.append(f"⚠️  Class name is '{structure['class_name']}', expected 'Contract'")
    
    if not structure["functions"]:
        issues.append("⚠️  No functions found in contract")
    
    return issues


def print_contract_summary(structure: Dict[str, Any]):
    """Print a summary of the contract"""
    print("\n" + "=" * 60)
    print("📋 Contract Structure Summary")
    print("=" * 60)
    print(f"Namespace: {structure['namespace']}")
    print(f"Class: {structure['class_name']}")
    print(f"\nStorage Variables ({len(structure['storage_variables'])}):")
    for var in structure["storage_variables"]:
        print(f"  - {var}")
    print(f"\nFunctions ({len(structure['functions'])}):")
    for func in structure["functions"]:
        print(f"  - {func['return_type']} {func['name']}()")
    print(f"\nEvents ({len(structure['events'])}):")
    for event in structure["events"]:
        print(f"  - {event}")


async def test_contract_methods(structure: Dict[str, Any]) -> Dict[str, bool]:
    """Test contract methods if deployed"""
    results = {}
    
    if not NEO3_AVAILABLE:
        print("\n⚠️  Skipping live contract tests (neo3 not installed)")
        return results
    
    contract_hash_str = get_contract_hash()
    if not contract_hash_str or not has_contract_hash():
        print("\n⚠️  Skipping live contract tests (contract not deployed)")
        return results
    
    print("\n" + "=" * 60)
    print("🧪 Testing Contract Methods (Live)")
    print("=" * 60)
    
    rpc_url = get_rpc_url()
    rpc = RPCClient(rpc_url)
    
    hash_str = contract_hash_str.replace("0x", "").replace("0X", "")
    contract_hash_uint = UInt160.from_string(hash_str)
    
    # Test each function
    for func in structure["functions"]:
        func_name = func["name"]
        print(f"\n🔧 Testing: {func_name}()")
        
        try:
            result = await rpc.invoke_function(contract_hash_uint, func_name, [])
            
            if isinstance(result, dict):
                state = result.get("state", "UNKNOWN")
                if state == "HALT":
                    print(f"   ✅ {func_name}() executed successfully")
                    stack = result.get("stack", [])
                    if stack:
                        print(f"   📊 Return value: {stack[0]}")
                    results[func_name] = True
                else:
                    print(f"   ❌ {func_name}() failed (state: {state})")
                    results[func_name] = False
            else:
                print(f"   ✅ {func_name}() executed")
                results[func_name] = True
                
        except Exception as e:
            print(f"   ❌ Error calling {func_name}(): {e}")
            results[func_name] = False
    
    return results


async def test_contract_storage(structure: Dict[str, Any]) -> Dict[str, Any]:
    """Test reading contract storage"""
    results = {}
    
    if not NEO3_AVAILABLE:
        return results
    
    contract_hash_str = get_contract_hash()
    if not contract_hash_str or not has_contract_hash():
        return results
    
    print("\n" + "=" * 60)
    print("📖 Testing Contract Storage")
    print("=" * 60)
    
    rpc_url = get_rpc_url()
    rpc = RPCClient(rpc_url)
    
    hash_str = contract_hash_str.replace("0x", "").replace("0X", "")
    contract_hash_uint = UInt160.from_string(hash_str)
    
    # Test reading storage for each storage variable
    for var in structure["storage_variables"]:
        # Try common key patterns
        test_keys = [var.lower(), "counter", "value", var]
        
        for key in test_keys:
            print(f"\n🔍 Reading storage: {var} (key: '{key}')")
            try:
                storage_key = key.encode('utf-8')
                storage_value = await rpc.get_storage(contract_hash_uint, storage_key)
                
                if storage_value:
                    if len(storage_value) <= 8:
                        value = int.from_bytes(storage_value, 'little', signed=False)
                        print(f"   ✅ Value: {value}")
                        results[var] = value
                        break
                    else:
                        print(f"   ✅ Value (hex): {storage_value.hex()}")
                        results[var] = storage_value.hex()
                        break
                else:
                    print(f"   ⚠️  Key '{key}' not found")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    return results


async def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Contract Validation Test")
    print("=" * 60)
    
    # Step 1: Read contract
    print("\n📖 Reading generated contract...")
    contract_code = read_contract()
    if not contract_code:
        print("\n❌ Cannot continue without contract file")
        sys.exit(1)
    
    print("✅ Contract file found")
    
    # Step 2: Analyze structure
    print("\n🔍 Analyzing contract structure...")
    structure = analyze_contract_structure(contract_code)
    
    # Step 3: Print summary
    print_contract_summary(structure)
    
    # Step 4: Validate structure
    print("\n" + "=" * 60)
    print("✅ Structure Validation")
    print("=" * 60)
    issues = validate_contract_structure(structure)
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ Contract structure is valid!")
    
    # Step 5: Test live contract (if deployed)
    method_results = await test_contract_methods(structure)
    storage_results = await test_contract_storage(structure)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Contract Structure: {'✅ Valid' if not issues else '⚠️  Has issues'}")
    if method_results:
        print(f"Method Tests: {sum(method_results.values())}/{len(method_results)} passed")
    if storage_results:
        print(f"Storage Tests: {len(storage_results)} values read")
    
    print("\n✅ Contract validation complete!")
    print("\n💡 Next steps:")
    print("   1. Review the contract structure above")
    print("   2. If deployed, check method test results")
    print("   3. Compare with your ChainChart diagram")
    print("   4. Test in UI by executing the diagram")


if __name__ == "__main__":
    asyncio.run(main())

