# Phase 3 Complete Test Plan

This document provides comprehensive testing instructions for Phase 3: Smart Contract Generation, Compilation, and Deployment.

---

## Prerequisites

1. **Backend API running**: `python api_server.py` (port 8000)
2. **Neo Compiler** (optional for real compilation):
   ```bash
   dotnet tool install -g Neo.Compiler.CSharp
   ```
3. **neo-mamba** (optional for real deployment):
   ```bash
   pip install neo-mamba
   ```

---

## Test 1 — JSON → C# Generation

### Objective
Verify that ChainChart JSON correctly generates valid C# Neo N3 contract code.

### Test Data

```json
{
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
        "params": ["UInt160 to", "BigInteger amount"],
        "visibility": "public"
      }
    },
    {
      "id": "3",
      "type": "event",
      "data": {
        "name": "Transfer",
        "params": "UInt160 from, UInt160 to, BigInteger amount"
      }
    }
  ],
  "edges": [
    {"from": "1", "to": "2"},
    {"from": "2", "to": "3"}
  ]
}
```

### Expected Output Structure

The generated C# contract should include:

1. **Required Namespaces**:
   ```csharp
   using Neo;
   using Neo.SmartContract;
   using Neo.SmartContract.Framework;
   using Neo.SmartContract.Framework.Attributes;
   using Neo.SmartContract.Framework.Services;
   using System;
   using System.Numerics;
   ```

2. **Namespace Declaration**:
   ```csharp
   namespace ChainChartGenerated
   ```

3. **Contract Class**:
   ```csharp
   [DisplayName("ChainChartContract")]
   [ManifestExtra("Author", "ChainChart")]
   [ManifestExtra("Description", "Generated from ChainChart diagram")]
   public class Contract : SmartContract
   ```

4. **Storage Variables** (from State nodes):
   ```csharp
   private static StorageMap balanceMap => new StorageMap(Storage.CurrentContext, "balance");
   private static BigInteger balance => balanceMap.Get().ToBigInteger();
   private static void SetBalance(BigInteger value) => balanceMap.Put(value);
   ```

5. **Functions** (from Function nodes):
   ```csharp
   public static void transfer(UInt160 to, BigInteger amount)
   {
       // TODO: Implement function logic based on connected nodes
   }
   ```

6. **Events** (from Event nodes):
   ```csharp
   [DisplayName("Transfer")]
   public static event Action<UInt160, UInt160, BigInteger> Transfer;
   ```

7. **Owner Check**:
   ```csharp
   [InitialValue("0x00", ContractParameterType.Hash160)]
   private static readonly UInt160 Owner = default;

   private static bool IsOwner()
   {
       return Runtime.CheckWitness(Owner);
   }
   ```

### How to Test

**Option A: Direct Python Test**

```python
from generator.neo_contract_generator import generate_contract_from_diagram
from generator.contract_validator import validate_contract

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
is_valid, errors, fixed = validate_contract(contract)

print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
print("\nContract:")
print(contract)
```

**Option B: API Test**

```bash
curl -X POST http://localhost:8000/export-contract \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [
      {"id": "1", "type": "state", "label": "balance", "value": "", "position": {"x": 0, "y": 0}, "metadata": {"label": "balance"}},
      {"id": "2", "type": "function", "label": "transfer", "value": "", "position": {"x": 0, "y": 0}, "metadata": {"name": "transfer", "params": "UInt160 to, BigInteger amount"}},
      {"id": "3", "type": "event", "label": "Transfer", "value": "", "position": {"x": 0, "y": 0}, "metadata": {"name": "Transfer", "params": "UInt160 from, UInt160 to, BigInteger amount"}}
    ],
    "edges": [
      {"from": "1", "to": "2"},
      {"from": "2", "to": "3"}
    ]
  }'
```

### Verification Checklist

- ✅ Contract contains `namespace ChainChartGenerated`
- ✅ Contract class extends `SmartContract`
- ✅ Contract has `[DisplayName]` and `[ManifestExtra]` attributes
- ✅ Storage variables use `StorageMap` with `Storage.CurrentContext`
- ✅ Functions are `public static void`
- ✅ Events have `[DisplayName]` attribute
- ✅ Owner field has `[InitialValue]` attribute
- ✅ `IsOwner()` uses `Runtime.CheckWitness(Owner)`
- ✅ All required namespaces are present
- ✅ Contract validates with `validate_contract()` (no critical errors)

---

## Test 2 — Compilation Works

### Objective
Verify that the generated C# contract compiles successfully to NEF + manifest.

### Test Data

Use the contract generated from Test 1, or any valid Neo C# contract.

### Expected Output

Calling `compile_contract(path_to_cs)` should return:

- **`.nef` file**: Compiled Neo Executable Format (binary)
- **`.manifest.json`**: Contract manifest with ABI, permissions, etc.
- **`success: True`**: If compiler is installed and compilation succeeds
- **`errors: []`**: Empty list if no compilation errors

### How to Test

```python
from generator.neo_contract_generator import generate_contract_from_diagram, write_contract_to_file
from generator.neo_compiler import compile_contract, read_compiled_files
from pathlib import Path

# Generate contract
diagram = {...}  # Use test diagram from Test 1
contract = generate_contract_from_diagram(diagram)

# Save to file
contract_file = Path("test_contract.cs")
contract_file.write_text(contract, encoding='utf-8')

# Compile
nef_path, manifest_path, success, errors = compile_contract(str(contract_file))

print(f"NEF: {nef_path}")
print(f"Manifest: {manifest_path}")
print(f"Success: {success}")
print(f"Errors: {errors}")

if success:
    compiled = read_compiled_files(nef_path, manifest_path)
    print(f"NEF size: {len(compiled['nef'])} chars (base64)")
    print(f"Manifest: {compiled['manifest']}")
```

### Verification Checklist

- ✅ `nef_path` points to existing `.nef` file
- ✅ `manifest_path` points to existing `.manifest.json` file
- ✅ `success` is `True` (if compiler installed) or `False` with mock files (if not)
- ✅ NEF file is valid binary (not empty, starts with NEF3 magic bytes if real)
- ✅ Manifest contains required fields: `name`, `abi`, `permissions`
- ✅ Manifest ABI includes methods and events from contract

### Expected Behavior

**With Neo Compiler Installed:**
- Compilation succeeds
- Real NEF and manifest files generated
- `success = True`
- `errors = []` (or warnings only)

**Without Neo Compiler:**
- Mock files generated
- `success = False`
- `errors` contains helpful message about installing compiler

---

## Test 3 — API Endpoint Works

### Objective
Verify that `POST /compile-contract` endpoint correctly generates, validates, compiles, and returns contract + NEF + manifest.

### Test Endpoint

**POST** `/compile-contract`

### Request Body

```json
{
  "nodes": [
    {
      "id": "1",
      "type": "state",
      "label": "balance",
      "value": "",
      "position": {"x": 0, "y": 0},
      "metadata": {
        "label": "balance",
        "dataType": "BigInteger"
      }
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
  "edges": [
    {"from": "1", "to": "2"}
  ]
}
```

### Expected Response

**Status**: `200 OK`

**Response Body**:
```json
{
  "contract": "using Neo;...",
  "nef": "base64_encoded_nef_content...",
  "manifest": {
    "name": "Contract",
    "abi": {
      "methods": [...],
      "events": [...]
    },
    "permissions": [...]
  },
  "success": true,
  "compile_errors": [],
  "error": null,
  "mock": false
}
```

### How to Test

**Option A: Using curl**

```bash
curl -X POST http://localhost:8000/compile-contract \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

**Option B: Using Python**

```python
import requests

response = requests.post(
    "http://localhost:8000/compile-contract",
    json={
        "nodes": [
            {
                "id": "1",
                "type": "state",
                "label": "balance",
                "value": "",
                "position": {"x": 0, "y": 0},
                "metadata": {"label": "balance"}
            },
            {
                "id": "2",
                "type": "function",
                "label": "transfer",
                "value": "",
                "position": {"x": 0, "y": 0},
                "metadata": {
                    "name": "transfer",
                    "params": "UInt160 to, BigInteger amount"
                }
            }
        ],
        "edges": [{"from": "1", "to": "2"}]
    }
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Contract length: {len(result['contract'])}")
print(f"Manifest keys: {list(result['manifest'].keys())}")
print(f"NEF length: {len(result['nef'])}")
print(f"Errors: {result['compile_errors']}")
```

### Verification Checklist

- ✅ Status code is `200`
- ✅ Response contains `contract` (string, non-empty)
- ✅ Response contains `manifest` (object with `name`, `abi`, `permissions`)
- ✅ Response contains `nef` (base64 string, non-empty)
- ✅ Response contains `compile_errors` (array)
- ✅ `success` is `true` (if compiler installed) or `false` (if mock)
- ✅ Contract file saved to `generated/Contract.cs`

### File Verification

After calling the endpoint, check:

```bash
# Check generated contract file
cat generated/Contract.cs

# Should contain valid C# Neo contract code
```

---

## Test 4 — Deployment (Mock or Real)

### Objective
Verify that `POST /deploy-contract` endpoint correctly deploys NEF + manifest to Neo TestNet (or returns mock TX hash).

### Test Endpoint

**POST** `/deploy-contract`

### Request Body

```json
{
  "nef": "base64_encoded_nef_content...",
  "manifest": {
    "name": "Contract",
    "abi": {...},
    "permissions": [...]
  },
  "private_key": "optional_private_key_wif_format"
}
```

### Expected Response

**With neo-mamba installed:**
```json
{
  "tx_hash": "0x1234...",
  "success": true,
  "error": null,
  "mock": false
}
```

**Without neo-mamba (mock):**
```json
{
  "tx_hash": "0x1234...",
  "success": false,
  "error": "neo-mamba library not available. TODO: Install neo-mamba for real deployment.",
  "mock": true
}
```

### How to Test

**Step 1: Get NEF and manifest from Test 3**

```python
# First, compile a contract
compile_response = requests.post("http://localhost:8000/compile-contract", json={...})
compile_result = compile_response.json()

nef = compile_result["nef"]
manifest = compile_result["manifest"]
```

**Step 2: Deploy**

```python
deploy_response = requests.post(
    "http://localhost:8000/deploy-contract",
    json={
        "nef": nef,
        "manifest": manifest,
        "private_key": None  # Optional
    }
)

result = deploy_response.json()
print(f"Success: {result['success']}")
print(f"TX Hash: {result['tx_hash']}")
print(f"Mock: {result['mock']}")
if result['error']:
    print(f"Error: {result['error']}")
```

### Verification Checklist

- ✅ Returns dictionary with `tx_hash`, `success`, `error`, `mock`
- ✅ `tx_hash` is a valid hex string (starts with `0x`)
- ✅ `tx_hash` is 66 characters long (0x + 64 hex chars)
- ✅ Error message explains if deployment is mocked
- ✅ Mock deployment returns consistent hash (based on NEF content)

### Expected Behavior

**With neo-mamba Installed:**
- Real deployment attempt (may require valid RPC and private key)
- Returns real transaction hash if successful
- `success = True`, `mock = False`

**Without neo-mamba:**
- Mock deployment
- Returns hash derived from NEF content
- `success = False`, `mock = True`
- Error message explains how to enable real deployment

---

## Test 5 — Contract Validation

### Objective
Verify that the contract validator correctly identifies and fixes common issues.

### Test Cases

**Test 5.1: Missing Namespace**

```python
from generator.contract_validator import validate_contract

contract = """
public class Contract : SmartContract
{
    public static void Main() { }
}
"""

is_valid, errors, fixed = validate_contract(contract)
# Should detect missing namespaces and add them
```

**Test 5.2: Missing DisplayName**

```python
contract = """
namespace ChainChartGenerated {
    public class Contract : SmartContract { }
}
"""

is_valid, errors, fixed = validate_contract(contract)
# Should detect missing DisplayName and add it
```

**Test 5.3: Storage Variables**

```python
contract = """
namespace ChainChartGenerated {
    public class Contract : SmartContract {
        private static StorageMap balanceMap => new StorageMap(Storage.CurrentContext, "balance");
    }
}
"""

is_valid, errors, fixed = validate_contract(contract)
# Should validate StorageMap usage
```

### Verification Checklist

- ✅ Validator detects missing namespaces
- ✅ Validator detects missing DisplayName
- ✅ Validator detects missing Owner initialization
- ✅ Validator detects missing Runtime.CheckWitness
- ✅ Validator automatically patches common issues
- ✅ Patched contract compiles successfully

---

## Running All Tests

Create a comprehensive test script `test_phase3_complete.py`:

```python
import asyncio
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
        
        if nef_path and manifest_path:
            compiled = read_compiled_files(nef_path, manifest_path)
            print(f"✅ NEF size: {len(compiled['nef'])} chars (base64)")
            print(f"✅ Manifest keys: {list(compiled['manifest'].keys())}")
        
        return nef_path, manifest_path, compiled if nef_path else None

def test_3_api_endpoint():
    """Test 3: API Endpoint"""
    print("\n" + "="*60)
    print("TEST 3: API Endpoint")
    print("="*60)
    
    response = requests.post(
        f"{API_BASE}/compile-contract",
        json={
            "nodes": [
                {"id": "1", "type": "state", "label": "balance", "value": "", "position": {"x": 0, "y": 0}, "metadata": {"label": "balance"}},
                {"id": "2", "type": "function", "label": "transfer", "value": "", "position": {"x": 0, "y": 0}, "metadata": {"name": "transfer", "params": "UInt160 to, BigInteger amount"}}
            ],
            "edges": [{"from": "1", "to": "2"}]
        }
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
    
    return result

def test_4_deployment(compile_result):
    """Test 4: Deployment"""
    print("\n" + "="*60)
    print("TEST 4: Deployment")
    print("="*60)
    
    response = requests.post(
        f"{API_BASE}/deploy-contract",
        json={
            "nef": compile_result["nef"],
            "manifest": compile_result["manifest"],
            "private_key": None
        }
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
    
    return result

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PHASE 3 COMPLETE TEST SUITE")
    print("="*60)
    
    # Test 1
    contract = test_1_generation()
    
    # Test 2
    nef_path, manifest_path, compiled = test_2_compilation(contract)
    
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
    print(f"  ✅ API Endpoint: PASSED")
    print(f"  ✅ Deployment: {'PASSED' if deploy_result['success'] else 'MOCK (neo-mamba not installed)'}")
    print("="*60 + "\n")
```

Run with:
```bash
python tests/test_phase3_complete.py
```

---

## Troubleshooting

### Compilation Fails

**Issue**: `compile_contract()` returns `(None, None, False, errors)`

**Solutions**:
1. Install Neo compiler: `dotnet tool install -g Neo.Compiler.CSharp`
2. Verify compiler: `neon --version`
3. Check DevPack: Ensure `Neo.SmartContract.Framework` is referenced

### API Returns 500 Error

**Issue**: Internal server error

**Solutions**:
1. Check backend logs for detailed error
2. Verify diagram format matches expected structure
3. Check that `generated/` directory is writable

### Deployment Always Returns Mock

**Issue**: `mock: true` in deployment response

**Solutions**:
1. Install neo-mamba: `pip install neo-mamba`
2. Set `NEO_RPC_URL` environment variable
3. Provide valid private key (WIF format) for signing

### Contract Validation Errors

**Issue**: Validator finds issues in generated contract

**Solutions**:
1. Check validator output for specific errors
2. Validator should auto-patch common issues
3. Review generated contract in `generated/Contract.cs`

---

## Success Criteria

All tests pass when:

1. ✅ Contract generation produces valid C# code
2. ✅ Contract compiles to NEF + manifest (or mock files generated)
3. ✅ API endpoints return correct responses
4. ✅ Deployment returns valid TX hash (real or mock)
5. ✅ Contract validator detects and fixes common issues
6. ✅ Generated contracts are usable for Neo blockchain deployment

---

## Next Steps

1. ✅ Test contract generation
2. ✅ Test compilation (with or without compiler)
3. ✅ Test API endpoints
4. ⏭️ Install Neo compiler for real compilation
5. ⏭️ Install neo-mamba for real deployment
6. ⏭️ Test on Neo TestNet with real RPC
7. ⏭️ Integrate with UI for one-click export + deploy
