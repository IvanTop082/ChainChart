# Neo N3 TestNet Deployment Guide

This directory contains scripts for compiling and deploying Neo N3 smart contracts to TestNet.

## Prerequisites

1. **Neo Compiler** (choose one):
   ```bash
   # Option 1: Neo.Compiler.CSharp (Recommended)
   dotnet tool install -g Neo.Compiler.CSharp
   
   # Option 2: Neo N3 Compiler
   # Download from: https://github.com/neo-project/neo-compiler
   
   # Option 3: Neo Express
   dotnet tool install -g Neo.Express
   ```

2. **Python Dependencies**:
   ```bash
   pip install neo3-python
   ```

3. **Environment Variables**:
   Create a `.env` file in the project root:
   ```env
   NEO_PRIVATE_KEY=your_private_key_here
   NEO_RPC_URL=https://testnet1.neo.org:443
   ```

## Step-by-Step Deployment

### Step 1: Compile Contract

Compile your C# contract to NEF + manifest:

```bash
python deployment/compile.py
```

Or specify a custom contract path:

```bash
python deployment/compile.py generated/Contract.cs
```

**Expected Output:**
- `generated/compiled/Contract.nef`
- `generated/compiled/Contract.manifest.json`

### Step 2: Deploy Contract

Deploy the compiled contract to Neo N3 TestNet:

```bash
python deployment/deploy.py
```

Or specify custom paths:

```bash
python deployment/deploy.py generated/compiled/Contract.nef generated/compiled/Contract.manifest.json
```

**Requirements:**
- `NEO_PRIVATE_KEY` environment variable must be set
- Account must have sufficient GAS (at least 10 GAS for deployment)

**Expected Output:**
- Transaction hash
- Contract hash
- Contract info saved to `deployment/contract_info.json`

### Step 3: Test Deployment

Test the deployed contract by calling a method:

```bash
python test_deployment.py
```

Or call a specific method:

```bash
python test_deployment.py getBalance
python test_deployment.py transfer "from" "to" 100
```

## File Structure

```
deployment/
├── compile.py          # Compile C# to NEF + manifest
├── deploy.py           # Deploy to Neo N3 TestNet
├── config.py           # Contract hash management
├── contract_info.json  # Deployed contract info (auto-generated)
└── README.md          # This file
```

## Contract Hash Usage

Once deployed, the contract hash is automatically saved to `deployment/contract_info.json` and loaded by the agent tools.

The agent will automatically use real RPC calls when a contract hash is available:

- `ReadNeoStateTool` - Reads from blockchain storage
- `CallNeoContractTool` - Calls contract methods

## Troubleshooting

### Compiler Not Found

**Error:** `Neo compiler not found`

**Solution:**
```bash
dotnet tool install -g Neo.Compiler.CSharp
```

### Private Key Not Set

**Error:** `NEO_PRIVATE_KEY environment variable not set`

**Solution:**
```bash
export NEO_PRIVATE_KEY=your_private_key_here
# Or on Windows:
$env:NEO_PRIVATE_KEY='your_private_key_here'
```

### Insufficient GAS

**Error:** `Insufficient GAS`

**Solution:**
- Get TestNet GAS from a faucet
- Ensure your account has at least 10 GAS

### RPC Connection Failed

**Error:** `RPC connection failed`

**Solution:**
- Check `NEO_RPC_URL` is correct
- Verify network connectivity
- Try alternative RPC endpoints:
  - `https://testnet1.neo.org:443`
  - `https://testnet2.neo.org:443`
  - `https://testnet3.neo.org:443`

### Contract Not Found

**Error:** `Contract not found` (in test script)

**Solution:**
- Wait for transaction confirmation (may take a few blocks)
- Verify contract hash in `deployment/contract_info.json`
- Check transaction on Neo blockchain explorer

## Testing Instructions

1. **Compile contract:**
   ```bash
   python deployment/compile.py
   ```

2. **Deploy contract:**
   ```bash
   python deployment/deploy.py
   ```

3. **Confirm output:**
   ```
   ✅ Deployment successful!
   Contract hash: 0x....
   Transaction hash: 0x....
   ```

4. **Run test call:**
   ```bash
   python test_deployment.py
   ```

5. **Verify agent uses real RPC:**
   - The agent tools will automatically detect the contract hash
   - Real RPC calls will be used instead of mocks
   - Check logs for RPC activity

## Notes

- All mocked blockchain logic is removed once a contract hash exists
- The agent automatically switches to real RPC calls
- Contract hash is persisted in `deployment/contract_info.json`
- RPC URL can be configured via `NEO_RPC_URL` environment variable

