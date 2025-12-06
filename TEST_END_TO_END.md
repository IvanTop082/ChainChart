# End-to-End Test: UI → Backend → Neo TestNet

## Prerequisites

1. ✅ **Backend API Server Running**
   ```bash
   python api_server.py
   ```
   Server should start on `http://localhost:8000`

2. ✅ **Frontend UI Running**
   ```bash
   cd "ChainChart_new ui"
   npm run dev
   ```
   UI should be available at `http://localhost:3000` (or similar)

3. ✅ **Environment Variables Set**
   - `NEO_RPC_URL` - Already set in `.env`
   - `NEO_CONTRACT_HASH` - Must be set to your deployed contract hash

## Step-by-Step Test

### Step 1: Set Contract Hash

Make sure your `.env` file has:
```bash
NEO_RPC_URL=http://seed3t5.neo.org:20332
NEO_CONTRACT_HASH=0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab
```

### Step 2: Start Backend Server

```bash
python api_server.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Start Frontend UI

In a new terminal:
```bash
cd "ChainChart_new ui"
npm run dev
```

### Step 4: Create a ChainChart in UI

1. Open `http://localhost:3000/builder` (or your frontend URL)
2. Create a simple diagram that uses Neo tools:

**Example Flow:**
```
[State Node: "Read Counter"]
    ↓
[Function Node: "read_neo_state" with key="value"]
    ↓
[Operation Node: "add" with the result]
    ↓
[Event Node: "Display Result"]
```

**Or simpler:**
```
[Function Node: "call_neo_contract" with method="get"]
    ↓
[Event Node: "Show Result"]
```

### Step 5: Execute the ChainChart

1. Click "Execute" or "Run" button in the UI
2. Watch the backend console for debug messages:
   ```
   🔗 Using RPC: http://seed3t5.neo.org:20332
   📝 Using Contract Hash: 0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab
   🔍 Reading storage key: value
   ✅ Storage value: 0
   ```

3. Check the UI for execution results

### Step 6: Verify Real Blockchain Calls

**In Backend Console, you should see:**
- ✅ `🔗 Using RPC: ...` messages
- ✅ `📝 Using Contract Hash: ...` messages
- ✅ `✅ Storage value: ...` or `✅ Method call successful`
- ❌ NO mock values or fallback messages

**In UI, you should see:**
- Execution results showing real values from blockchain
- No "mocked" indicators

## Test Scenarios

### Scenario 1: Read Storage
- **Node Type**: Function
- **Tool**: `read_neo_state`
- **Parameter**: `key="value"`
- **Expected**: Returns `0` (or current counter value)

### Scenario 2: Call Contract Method
- **Node Type**: Function
- **Tool**: `call_neo_contract`
- **Parameters**: 
  - `method="get"`
  - `args=[]`
- **Expected**: Returns `{"status": "success", "result": [0], ...}`

### Scenario 3: Increment Counter (if you have write access)
- **Node Type**: Function
- **Tool**: `call_neo_contract`
- **Parameters**:
  - `method="Increment"`
  - `args=[]`
- **Expected**: Transaction executed (if you have signing capability)

## Troubleshooting

### Backend Not Starting
- Check if port 8000 is already in use
- Verify Python dependencies: `pip install fastapi uvicorn`

### Frontend Not Connecting
- Check CORS settings in `api_server.py`
- Verify backend URL in frontend config

### "NEO_CONTRACT_HASH not set"
- Add `NEO_CONTRACT_HASH=0x...` to `.env` file
- Restart backend server

### "neo3 library not installed"
- Install: `pip install neo-mamba`
- Restart backend server

### Still Getting Mock Values
- Check backend console for error messages
- Verify contract hash is correct
- Check RPC URL is accessible

## Success Indicators

✅ **Backend Console Shows:**
```
🔗 Using RPC: http://seed3t5.neo.org:20332
📝 Using Contract Hash: 0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab
🔍 Reading storage key: value
✅ Storage value: 0
```

✅ **UI Shows:**
- Real execution results
- No "mock" indicators
- Actual values from blockchain

✅ **No Errors:**
- No "fallback to mock" messages
- No "RPC call failed" errors
- No "contract hash not set" errors

## Quick Test Command

You can also test the backend directly:
```bash
python test_live_chain.py
```

This verifies connectivity before testing the full UI flow.

