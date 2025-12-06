# 🚀 End-to-End Test: UI → Backend → Neo TestNet

## Quick Start Guide

### Step 1: Start Backend Server

**Terminal 1:**
```bash
cd C:\Users\vanys\ChainChart
python api_server.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

### Step 2: Start Frontend UI

**Terminal 2 (NEW terminal):**
```bash
cd "C:\Users\vanys\ChainChart\ChainChart_new ui"
npm run dev
```

**Expected output:**
```
  ▲ Next.js ...
  - Local:        http://localhost:3000
```

### Step 3: Open Builder in Browser

1. Open: `http://localhost:3000/builder`
2. You should see the ChainChart builder interface

### Step 4: Create a Simple Test Diagram

**Create this flow:**

1. **Add a Function Node:**
   - Click "Add Node" or drag a Function node
   - **Label**: "Read Counter"
   - **Tool**: `read_neo_state`
   - **Parameters**: 
     - Key: `key`
     - Value: `"value"`

   **OR**

2. **Add a Function Node:**
   - **Label**: "Get Counter"
   - **Tool**: `call_neo_contract`
   - **Parameters**:
     - Key: `method`
     - Value: `"get"`
     - Key: `args`
     - Value: `[]`

3. **Add an Event Node:**
   - **Label**: "Display Result"
   - Connect it from the Function node

### Step 5: Execute the Diagram

1. Click "Execute" or "Run" button
2. Watch the backend console (Terminal 1)

### Step 6: Verify Real Blockchain Calls

**In Backend Console (Terminal 1), you should see:**
```
🔗 Using RPC: http://seed3t5.neo.org:20332
📝 Using Contract Hash: 0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab
🔍 Reading storage key: value
✅ Storage value: 0
```

**OR for method call:**
```
🔗 Using RPC: http://seed3t5.neo.org:20332
📝 Using Contract Hash: 0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab
🔧 Calling method: get
📚 Using library: neo-mamba
✅ Method call successful
   ⛽ Gas consumed: 72376
```

**In UI, you should see:**
- Execution completed successfully
- Result showing the value from blockchain (0)
- No "mock" indicators

## What This Proves

✅ **UI → Backend connection works**  
✅ **Backend → Neo TestNet connection works**  
✅ **Real blockchain calls (no mocks)**  
✅ **Complete end-to-end flow works!**

## Troubleshooting

### Backend not starting
- Check if port 8000 is already in use
- Install dependencies: `pip install fastapi uvicorn`

### Frontend can't connect
- Check CORS settings in `api_server.py`
- Verify backend is running on port 8000

### Still seeing mocks
- Check backend console for error messages
- Verify contract hash is correct in `.env`
- Make sure `generator/config.py` is being imported

### No debug messages in backend
- Check that the tools are being called
- Verify the diagram has the correct node types

## Success Indicators

✅ **Backend Console Shows:**
- `🔗 Using RPC: ...`
- `📝 Using Contract Hash: ...`
- `✅ Storage value: ...` or `✅ Method call successful`

✅ **UI Shows:**
- Real execution results
- No "mock" indicators
- Actual values from blockchain

✅ **No Errors:**
- No "fallback to mock" messages
- No "RPC call failed" errors
- No "contract hash not set" errors

