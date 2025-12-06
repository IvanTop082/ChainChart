# Complete Deployment Guide: UI → SpoonOS → Neo TestNet

## ✅ Full Pipeline Overview

Your system now supports the complete flow:

1. **Create Graph in UI** → Draw ChainChart diagram
2. **SpoonOS Agent Processes** → Executes workflow logic
3. **Generate Smart Contract** → Converts diagram to C# Neo contract
4. **Compile Contract** → Creates NEF + manifest
5. **Deploy to TestNet** → Sends to Neo N3 TestNet
6. **View on TestNet** → See deployed contract

## 🎯 Step-by-Step Usage

### 1. Start Backend Server

```bash
# In project root
python api_server.py
```

Server runs on `http://localhost:8000`

### 2. Start Frontend UI

```bash
# In ChainChart_new ui directory
npm run dev
```

UI runs on `http://localhost:3000`

### 3. Create Your ChainChart Diagram

1. Open the UI in browser
2. Add nodes (State, Function, Operation, Event, Condition)
3. Connect nodes with edges
4. Configure node properties (values, names, etc.)

### 4. Test Execution (Optional)

Click "Execute" to test the workflow with SpoonOS agent.

### 5. Export Contract

Click **"Export Contract"** button:
- Generates C# contract from diagram
- Compiles to NEF + manifest
- Saves to `generated_contracts/contract.nef` and `contract.manifest.json`

### 6. Deploy to TestNet

Click **"Deploy to TestNet"** button:
- Exports contract (if not already exported)
- Deploys to Neo N3 TestNet using pure RPC
- Returns transaction hash
- Shows link to view on TestNet

### 7. View on TestNet

After deployment:
- Transaction hash is displayed
- Click **"View on TestNet"** button
- Opens NeoTube explorer showing your deployed contract

## 🔧 Prerequisites

### Environment Setup

Make sure `.env` file has:
```
NEO_PRIVATE_KEY=your_wif_private_key_here
NEO_RPC_URL=http://seed3t5.neo.org:20332
```

### Neo Compiler (Optional but Recommended)

For real contracts (not mock):
```bash
dotnet tool install -g Neo.Compiler.CSharp
```

## 📊 What Happens Behind the Scenes

### When You Click "Export Contract":

1. **UI sends diagram** → `POST /export-contract`
2. **Backend transforms** → UI format → Backend format
3. **SpoonOS processes** → `generate_contract_from_diagram()`
4. **Contract generated** → Deterministic C# code
5. **Contract validated** → Auto-patches issues
6. **Contract compiled** → NEF + manifest created
7. **Files saved** → `generated_contracts/contract.nef` + `.manifest.json`
8. **Response sent** → Contract code, NEF, manifest returned

### When You Click "Deploy to TestNet":

1. **Export first** → Gets NEF + manifest
2. **Backend receives** → `POST /deploy-contract`
3. **Files prepared** → NEF + manifest saved
4. **RPC deployment** → `neo_rpc_deploy.py` handles:
   - Transaction building
   - ECDSA signing
   - Base64 serialization
   - RPC broadcast
5. **Transaction hash** → Returned to UI
6. **TestNet link** → NeoTube explorer URL

## 🌐 Viewing Contracts on TestNet

### NeoTube Explorer

After deployment, you can view your contract at:
```
https://testnet.neotube.org/transaction/{tx_hash}
```

### NeoScan (Alternative)

```
https://testnet.neoscan.io/transaction/{tx_hash}
```

## ⚠️ Important Notes

1. **Mock Contracts**: If compiler isn't installed, you'll get a mock NEF (24 bytes). Deployment will fail with "Invalid transaction script". Install the compiler for real contracts.

2. **TestNet GAS**: You need TestNet GAS to deploy. Get it from:
   - Neo TestNet Faucet
   - Or use a TestNet wallet

3. **Private Key**: Must be in WIF format in `.env` file.

4. **RPC Endpoint**: Currently using `http://seed3t5.neo.org:20332`

## 🐛 Troubleshooting

### "Invalid transaction script" Error
- **Cause**: Mock NEF file (24 bytes, no contract code)
- **Solution**: Install Neo compiler and compile a real contract

### "Insufficient funds" Error
- **Cause**: Not enough TestNet GAS
- **Solution**: Get GAS from TestNet faucet

### "Private key missing" Error
- **Cause**: NEO_PRIVATE_KEY not set in .env
- **Solution**: Add your WIF private key to .env

### Deployment succeeds but no transaction hash
- **Cause**: RPC response format might be different
- **Solution**: Check backend logs for actual transaction hash

## 🎉 Success Indicators

✅ **Export Success:**
- Files saved to `generated_contracts/`
- NEF file > 24 bytes (real contract)
- No compilation errors

✅ **Deployment Success:**
- Transaction hash returned
- "View on TestNet" button appears
- Link opens NeoTube showing your contract

## 📝 Example Workflow

1. Create diagram with:
   - State node: "PlayerHP" = 100
   - Function node: "DamagePlayer"
   - Operation node: "-" with value 10
   - Event node: "PlayerDamaged"

2. Connect: State → Function → Operation → Event

3. Click "Export Contract" → Contract generated

4. Click "Deploy to TestNet" → Contract deployed

5. Click "View on TestNet" → See your contract on blockchain!

## 🚀 You're Ready!

The complete pipeline is now functional:
- ✅ UI diagram creation
- ✅ SpoonOS agent execution
- ✅ Contract generation
- ✅ Contract compilation
- ✅ TestNet deployment
- ✅ TestNet viewing

Just create your diagram and deploy!

