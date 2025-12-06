# How to Test Neo N3 Deployment

## Quick Test (Infrastructure Only)

Test all deployment components without deploying:

```bash
python test_deployment_infrastructure.py
```

This will test:
- ✅ WIF to private key conversion
- ✅ Script building
- ✅ Transaction building
- ✅ Transaction signing
- ✅ Transaction serialization
- ✅ RPC connection
- ✅ Script validation

## Full Deployment Test (Requires Real Contract)

### Step 1: Compile a Real Contract

You need a properly compiled Neo N3 contract. Options:

**Option A: Use Neo.Compiler.CSharp**
```bash
# Install compiler
dotnet tool install -g Neo.Compiler.CSharp

# Compile your contract
nccs Contract.cs

# This creates Contract.nef and Contract.manifest.json
```

**Option B: Use the built-in compiler**
The `generator/neo_compiler.py` will automatically compile contracts if a compiler is installed.

### Step 2: Place Files in generated_contracts/

```bash
# Copy compiled files
cp Contract.nef generated_contracts/contract.nef
cp Contract.manifest.json generated_contracts/contract.manifest.json
```

### Step 3: Test Deployment

```bash
# Test with the test script
python test_with_real_contract.py

# Or deploy directly
python deployment/deploy.py
```

## What to Expect

### ✅ Success Indicators:
- Transaction serialized successfully
- Transaction signed successfully
- RPC accepts the transaction
- Returns transaction hash

### ⚠️ Common Issues:

**Error: -506 "Invalid transaction script"**
- **Cause**: NEF file is mock or invalid
- **Solution**: Compile a real contract

**Error: -508 "Invalid signature"**
- **Cause**: Private key mismatch or signing issue
- **Solution**: Check NEO_PRIVATE_KEY in .env

**Error: -511 "Insufficient funds"**
- **Cause**: Account doesn't have enough GAS
- **Solution**: Get TestNet GAS from faucet

## Test Scripts Available

1. **test_deployment_infrastructure.py**
   - Tests all components
   - Works with mock data
   - No real deployment

2. **test_with_real_contract.py**
   - Full deployment test
   - Requires real compiled contract
   - Actually deploys to TestNet

3. **test_deploy_script.py**
   - Tests script format only
   - Uses invokescript (dry run)
   - Good for debugging script issues

## Environment Setup

Make sure your `.env` file has:
```
NEO_PRIVATE_KEY=your_wif_private_key_here
NEO_RPC_URL=http://seed3t5.neo.org:20332
```

## Getting TestNet GAS

If you need TestNet GAS for deployment:
1. Visit Neo TestNet faucet
2. Enter your address (derived from private key)
3. Request GAS

## Troubleshooting

**All tests pass but deployment fails:**
- Check NEF file size (should be > 24 bytes for real contracts)
- Verify contract compiled successfully
- Check RPC endpoint is accessible

**Script validation fails:**
- Verify NEF file format is correct
- Check manifest JSON is valid
- Ensure contract hash in script is correct

