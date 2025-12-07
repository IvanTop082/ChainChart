# Safe Testing Guide for Generated Contract

## ✅ Safety First
- **TestNet Only**: All testing happens on Neo TestNet (no real funds at risk)
- **Test GAS**: You have 29.89 GAS in your testnet wallet (more than enough)
- **No Mainnet Risk**: This contract will NOT deploy to mainnet

## 📋 Step-by-Step Testing Process

### Step 1: Compile the Contract (Verify it works)

**Option A: Via UI (Recommended)**
1. Open your ChainChart UI
2. Click **"Export Contract"** button
3. The backend will:
   - Validate the contract code
   - Compile it to NEF + manifest
   - Save files to `generated_contracts/`
4. Check for any compilation errors in the response

**Option B: Manual Compilation**
```bash
# If you have Neo compiler installed
neoc Contract.cs
```

**Expected Result:**
- ✅ `contract.nef` file created
- ✅ `contract.manifest.json` file created
- ✅ No compilation errors

---

### Step 2: Deploy to TestNet

**Via UI:**
1. Click **"Deploy to TestNet"** button
2. The system will:
   - Load NEF and manifest from `generated_contracts/`
   - Use your WIF from `.env` (`Kwn83NJDk1dwKuvCQBJWSxkEudL7GeRwrqoZBRvgRWThGGP38Agw`)
   - Deploy using `neon-js` (same as NeoNova)
   - Return transaction hash

**What to Expect:**
- ✅ Transaction hash (e.g., `0x1234...`)
- ✅ Contract deployed to TestNet
- ✅ ~10 GAS fee deducted (you have 29.89 GAS, so safe)

**If Deployment Fails:**
- Check GAS balance (should be > 10 GAS)
- Verify RPC connection (TestNet: `http://seed3t5.neo.org:20332`)
- Check private key format (should be WIF)

---

### Step 3: Test the Deployed Contract

After deployment, you'll get a **contract hash** (script hash). Use it to test:

#### A. Test `StoreData` Method

**Using Neo Explorer:**
1. Go to https://testnet.neotube.org
2. Enter your contract hash
3. Click "Invoke" tab
4. Select method: `StoreData`
5. Enter parameters:
   - `key`: `"test_key"`
   - `value`: `"test_value"`
6. Click "Invoke" (read-only test, no fee)

**Using RPC (Command Line):**
```bash
# Replace <CONTRACT_HASH> with your deployed contract hash
curl -X POST http://seed3t5.neo.org:20332 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "invokefunction",
    "params": [
      "<CONTRACT_HASH>",
      "StoreData",
      [
        {"type": "String", "value": "test_key"},
        {"type": "String", "value": "test_value"}
      ]
    ],
    "id": 1
  }'
```

#### B. Test `GetData` Method (Read-Only)

**Using Neo Explorer:**
1. Go to your contract on https://testnet.neotube.org
2. Click "Invoke" tab
3. Select method: `GetData`
4. Enter parameter:
   - `key`: `"test_key"`
5. Click "Invoke" (read-only, free)
6. Should return: `"test_value"`

**Using RPC:**
```bash
curl -X POST http://seed3t5.neo.org:20332 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "invokefunction",
    "params": [
      "<CONTRACT_HASH>",
      "GetData",
      [{"type": "String", "value": "test_key"}]
    ],
    "id": 1
  }'
```

---

### Step 4: Verify Contract on Explorer

1. Go to https://testnet.neotube.org
2. Search for your transaction hash (from deployment)
3. Click on the transaction
4. You'll see:
   - Contract hash (save this!)
   - Deployment details
   - Contract methods

---

## 🔍 Testing Checklist

- [ ] Contract compiles without errors
- [ ] Contract deploys successfully (get transaction hash)
- [ ] Contract hash is visible on Neo Explorer
- [ ] `StoreData` method can be invoked (test with test data)
- [ ] `GetData` method returns stored data correctly
- [ ] Events are emitted (check transaction logs)

---

## 🛠️ Troubleshooting

### "Compilation failed"
- Check contract syntax (should be valid C#)
- Ensure all using statements are present
- Check for spaces in variable names (should be fixed automatically)

### "Deployment failed: Insufficient GAS"
- You have 29.89 GAS, so this shouldn't happen
- If it does, get more testnet GAS: https://neotube.org/faucet

### "Contract Already Exists"
- This means the contract was already deployed
- Change the contract name in the manifest to deploy a new version
- Or use a different contract code

### "Transaction signing failed"
- Check your `.env` file has correct `NEO_PRIVATE_KEY` (WIF format)
- Verify the private key matches your wallet with GAS

---

## 📝 Contract Methods Reference

### `StoreData(string key, string value)`
- **Purpose**: Store key-value data in contract storage
- **Parameters**: 
  - `key` (string): Storage key
  - `value` (string): Value to store
- **Event**: Emits `OnDataStored(key)` event
- **Cost**: ~0.01 GAS (network fee)

### `GetData(string key)`
- **Purpose**: Retrieve stored data
- **Parameters**: 
  - `key` (string): Storage key to retrieve
- **Returns**: Stored value (string) or null if not found
- **Cost**: Free (read-only, no transaction)

---

## 🎯 Next Steps After Testing

Once you've verified the contract works:
1. ✅ Test with different data types
2. ✅ Test edge cases (empty strings, long strings)
3. ✅ Check transaction logs for events
4. ✅ Verify storage persistence across transactions
5. ✅ Test with your actual ChainChart-generated contracts

---

## 🔗 Useful Links

- **Neo TestNet Explorer**: https://testnet.neotube.org
- **TestNet Faucet**: https://neotube.org/faucet
- **Neo Documentation**: https://docs.neo.org
- **Your Contract Location**: `generated_contracts/Contract.cs`

---

**Remember**: This is TestNet - experiment freely! No real funds are at risk.



