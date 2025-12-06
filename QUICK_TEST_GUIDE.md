# 🚀 Quick Test: UI → Backend → Neo TestNet

## ✅ Prerequisites Check

Your `.env` is already configured:
- ✅ `NEO_RPC_URL=http://seed3t5.neo.org:20332`
- ✅ `NEO_CONTRACT_HASH=0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab`

## Step 1: Start Backend Server

```bash
python api_server.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

## Step 2: Start Frontend UI

**Open a NEW terminal:**
```bash
cd "ChainChart_new ui"
npm run dev
```

**Expected output:**
```
  ▲ Next.js ...
  - Local:        http://localhost:3000
```

## Step 3: Create a Test Diagram

1. Open `http://localhost:3000/builder` in your browser

2. Create a simple diagram with ONE function node:

   **Node 1: Function Node**
   - **Label**: "Read Counter"
   - **Type**: Function
   - **Tool**: `read_neo_state`
   - **Parameters**: 
     - `key`: `"value"`

   **OR**

   **Node 1: Function Node**
   - **Label**: "Get Counter"
   - **Type**: Function
   - **Tool**: `call_neo_contract`
   - **Parameters**:
     - `method`: `"get"`
     - `args`: `[]`

3. Click "Execute" or "Run" button

## Step 4: Watch the Magic! ✨

### In Backend Console, you should see:
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

### In UI, you should see:
- Execution completed successfully
- Result showing the value from blockchain (likely `0`)
- No "mock" indicators

## What This Proves

✅ **Backend connects to Neo TestNet**  
✅ **Contract exists and is accessible**  
✅ **Real RPC calls are being made**  
✅ **No mocks or fallbacks**  
✅ **Complete UI → Backend → Blockchain flow works!**

## Troubleshooting

### "NEO_CONTRACT_HASH not set"
- Check `.env` file exists
- Restart backend server after changing `.env`

### "neo3 library not installed"
```bash
pip install neo-mamba
```

### Backend not starting
- Check if port 8000 is free
- Install dependencies: `pip install fastapi uvicorn`

### Frontend can't connect
- Check CORS in `api_server.py` allows your frontend port
- Verify backend is running on port 8000

### Still seeing mocks
- Check backend console for errors
- Verify contract hash is correct
- Make sure `generator/config.py` is being imported correctly

## Next Steps

Once this works, try:
1. **Read different storage keys**
2. **Call different contract methods**
3. **Create more complex workflows** with multiple nodes
4. **Chain operations** together (read → process → display)

