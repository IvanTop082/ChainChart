# End-to-End Test Frontend Guide

## Overview

Create a simple standalone HTML/JavaScript frontend that lets you:
1. Paste the contract hash from ChainChart deployment
2. Test `increment()` method
3. Read `counter` property
4. Verify the counter increases

## What ChainChart Will Give You

After deploying, ChainChart will provide:
- **Contract Hash**: `0x1234...` (the deployed contract address)
- **Transaction Hash**: `0xabcd...` (deployment transaction)
- **Network**: TestNet URL (e.g., `https://testnet.onegate.space`)

## Frontend Structure

### Option 1: Simple HTML + JavaScript (Easiest)

**File: `test-counter.html`**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Counter Contract Tester</title>
    <script src="https://cdn.jsdelivr.net/npm/@cityofzion/neon-js@5.8.0/dist/index.js"></script>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
        .input-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 10px; font-size: 14px; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; }
        .result { margin: 20px 0; padding: 15px; border-radius: 5px; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <h1>🔢 Counter Contract Tester</h1>
    
    <div class="input-group">
        <label>Contract Hash (from ChainChart):</label>
        <input type="text" id="contractHash" placeholder="0x1234...">
    </div>
    
    <div class="input-group">
        <label>RPC URL:</label>
        <input type="text" id="rpcUrl" value="https://testnet.onegate.space">
    </div>
    
    <div class="input-group">
        <label>Private Key (WIF) - for signing transactions:</label>
        <input type="password" id="privateKey" placeholder="Kwn83...">
        <small>⚠️ Only use testnet keys! Never use mainnet keys here.</small>
    </div>
    
    <div>
        <button onclick="readCounter()">📖 Read Counter</button>
        <button onclick="incrementCounter()">➕ Increment Counter</button>
        <button onclick="testMultipleIncrements()">🔄 Test Multiple (3x)</button>
    </div>
    
    <div id="result"></div>
    
    <script>
        const { rpc, sc, u, wallet } = window.neon;
        
        function getContractHash() {
            return document.getElementById('contractHash').value.trim();
        }
        
        function getRpcUrl() {
            return document.getElementById('rpcUrl').value.trim();
        }
        
        function getPrivateKey() {
            return document.getElementById('privateKey').value.trim();
        }
        
        function showResult(message, type = 'info') {
            const resultDiv = document.getElementById('result');
            resultDiv.className = `result ${type}`;
            resultDiv.innerHTML = message;
        }
        
        // Read counter value (read-only, no transaction needed)
        async function readCounter() {
            const contractHash = getContractHash();
            const rpcUrl = getRpcUrl();
            
            if (!contractHash) {
                showResult('❌ Please enter contract hash', 'error');
                return;
            }
            
            try {
                showResult('⏳ Reading counter...', 'info');
                
                const client = new rpc.RPCClient(rpcUrl);
                
                // Option 1: Call the counter property (if it's a method)
                const script = sc.createScript({
                    scriptHash: contractHash,
                    operation: 'counter',
                    args: []
                });
                
                const result = await client.invokeScript(u.HexString.fromHex(script));
                
                if (result.state === 'FAULT') {
                    // Try reading from storage directly
                    return await readCounterFromStorage(contractHash, rpcUrl);
                }
                
                const counterValue = result.stack[0]?.value || 0;
                showResult(`✅ Counter Value: <strong>${counterValue}</strong>`, 'success');
                
            } catch (error) {
                // Fallback: read from storage
                await readCounterFromStorage(contractHash, rpcUrl);
            }
        }
        
        // Read counter from storage directly
        async function readCounterFromStorage(contractHash, rpcUrl) {
            try {
                const client = new rpc.RPCClient(rpcUrl);
                
                // Storage key is "counter" (prefix) + "" (empty) = "counter"
                const storageKey = Buffer.from('counter', 'utf-8');
                const keyHex = u.HexString.fromHex(storageKey.toString('hex'));
                
                const result = await client.getStorage(contractHash, keyHex);
                
                if (result && result.value) {
                    // Convert hex to number
                    const value = parseInt(result.value, 16);
                    showResult(`✅ Counter Value (from storage): <strong>${value}</strong>`, 'success');
                } else {
                    showResult('✅ Counter Value: <strong>0</strong> (not set yet)', 'info');
                }
            } catch (error) {
                showResult(`❌ Error reading counter: ${error.message}`, 'error');
            }
        }
        
        // Increment counter (requires transaction)
        async function incrementCounter() {
            const contractHash = getContractHash();
            const rpcUrl = getRpcUrl();
            const privateKey = getPrivateKey();
            
            if (!contractHash) {
                showResult('❌ Please enter contract hash', 'error');
                return;
            }
            
            if (!privateKey) {
                showResult('❌ Please enter private key to sign transaction', 'error');
                return;
            }
            
            try {
                showResult('⏳ Incrementing counter...', 'info');
                
                const client = new rpc.RPCClient(rpcUrl);
                const account = new wallet.Account(privateKey);
                
                // Create script to call increment()
                const script = sc.createScript({
                    scriptHash: contractHash,
                    operation: 'increment',
                    args: []
                });
                
                // Build transaction
                const tx = new sc.Transaction({
                    signers: [{
                        account: account.scriptHash,
                        scopes: sc.WitnessScope.CalledByEntry
                    }],
                    script: script
                });
                
                // Sign transaction
                await tx.sign(account);
                
                // Send transaction
                const result = await client.sendRawTransaction(u.HexString.fromHex(tx.serialize()));
                
                showResult(`
                    ✅ Counter Incremented!<br>
                    <strong>Transaction Hash:</strong> ${result}<br>
                    <small>Wait a few seconds, then click "Read Counter" to see the new value.</small>
                `, 'success');
                
                // Auto-read after 3 seconds
                setTimeout(() => {
                    readCounter();
                }, 3000);
                
            } catch (error) {
                showResult(`❌ Error incrementing: ${error.message}`, 'error');
                console.error('Full error:', error);
            }
        }
        
        // Test multiple increments
        async function testMultipleIncrements() {
            showResult('⏳ Testing 3 increments...', 'info');
            
            for (let i = 1; i <= 3; i++) {
                showResult(`⏳ Incrementing ${i}/3...`, 'info');
                await incrementCounter();
                
                // Wait for transaction to confirm
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                // Read counter
                await readCounter();
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
            
            showResult('✅ Test complete! Check counter value above.', 'success');
        }
    </script>
</body>
</html>
```

### Option 2: React/Next.js (More Professional)

**File: `test-counter-app.tsx`**

```tsx
'use client';

import { useState } from 'react';
import { rpc, sc, u, wallet } from '@cityofzion/neon-js';

export default function CounterTester() {
  const [contractHash, setContractHash] = useState('');
  const [rpcUrl, setRpcUrl] = useState('https://testnet.onegate.space');
  const [privateKey, setPrivateKey] = useState('');
  const [counter, setCounter] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const readCounter = async () => {
    if (!contractHash) {
      setError('Please enter contract hash');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const client = new rpc.RPCClient(rpcUrl);
      
      // Try calling counter property
      const script = sc.createScript({
        scriptHash: contractHash,
        operation: 'counter',
        args: []
      });

      const result = await client.invokeScript(u.HexString.fromHex(script));
      
      if (result.state === 'FAULT') {
        // Fallback: read from storage
        const storageKey = Buffer.from('counter', 'utf-8');
        const keyHex = u.HexString.fromHex(storageKey.toString('hex'));
        const storageResult = await client.getStorage(contractHash, keyHex);
        
        if (storageResult && storageResult.value) {
          setCounter(parseInt(storageResult.value, 16));
        } else {
          setCounter(0);
        }
      } else {
        setCounter(result.stack[0]?.value || 0);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const incrementCounter = async () => {
    if (!contractHash || !privateKey) {
      setError('Please enter contract hash and private key');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const client = new rpc.RPCClient(rpcUrl);
      const account = new wallet.Account(privateKey);

      const script = sc.createScript({
        scriptHash: contractHash,
        operation: 'increment',
        args: []
      });

      const tx = new sc.Transaction({
        signers: [{
          account: account.scriptHash,
          scopes: sc.WitnessScope.CalledByEntry
        }],
        script: script
      });

      await tx.sign(account);
      const result = await client.sendRawTransaction(u.HexString.fromHex(tx.serialize()));

      // Wait and refresh counter
      setTimeout(() => {
        readCounter();
      }, 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '50px auto', padding: '20px' }}>
      <h1>🔢 Counter Contract Tester</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <label>Contract Hash:</label>
        <input
          type="text"
          value={contractHash}
          onChange={(e) => setContractHash(e.target.value)}
          placeholder="0x1234..."
          style={{ width: '100%', padding: '10px' }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label>RPC URL:</label>
        <input
          type="text"
          value={rpcUrl}
          onChange={(e) => setRpcUrl(e.target.value)}
          style={{ width: '100%', padding: '10px' }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label>Private Key (WIF):</label>
        <input
          type="password"
          value={privateKey}
          onChange={(e) => setPrivateKey(e.target.value)}
          placeholder="Kwn83..."
          style={{ width: '100%', padding: '10px' }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <button onClick={readCounter} disabled={loading}>
          📖 Read Counter
        </button>
        <button onClick={incrementCounter} disabled={loading}>
          ➕ Increment
        </button>
      </div>

      {counter !== null && (
        <div style={{ padding: '15px', background: '#d4edda', borderRadius: '5px' }}>
          <strong>Counter Value: {counter}</strong>
        </div>
      )}

      {error && (
        <div style={{ padding: '15px', background: '#f8d7da', borderRadius: '5px' }}>
          ❌ {error}
        </div>
      )}
    </div>
  );
}
```

## Setup Instructions

### For HTML Version:

1. **Create the file:**
   ```bash
   # Create test-counter.html in a new folder
   mkdir counter-test
   cd counter-test
   # Copy the HTML code above into test-counter.html
   ```

2. **Open in browser:**
   - Just double-click `test-counter.html`
   - Or serve with: `python -m http.server 8000`

3. **No build step needed** - works directly in browser

### For React/Next.js Version:

1. **Create Next.js app:**
   ```bash
   npx create-next-app@latest counter-test
   cd counter-test
   npm install @cityofzion/neon-js
   ```

2. **Add the component:**
   - Create `app/test/page.tsx` with the React code above

3. **Run:**
   ```bash
   npm run dev
   ```

## How to Use

1. **Deploy contract in ChainChart:**
   - Generate and deploy your counter contract
   - Copy the **Contract Hash** (e.g., `0x1234abcd...`)

2. **Open test frontend:**
   - Paste contract hash into the input field
   - Enter RPC URL (default: `https://testnet.onegate.space`)
   - Enter your private key (WIF format)

3. **Test:**
   - Click **"Read Counter"** → Should show `0` (first time)
   - Click **"Increment Counter"** → Wait for transaction
   - Click **"Read Counter"** again → Should show `1`
   - Repeat → Should show `2`, `3`, `4`...

## What to Verify

✅ **First Read**: Counter = 0  
✅ **After 1st Increment**: Counter = 1  
✅ **After 2nd Increment**: Counter = 2  
✅ **After 3rd Increment**: Counter = 3  

If the counter increases correctly, your contract works! 🎉

## Troubleshooting

**Problem: "Contract not found"**
- Check contract hash is correct (starts with `0x`)
- Verify contract is deployed to TestNet

**Problem: "Insufficient GAS"**
- Make sure your wallet has GAS tokens
- Get testnet GAS from faucet

**Problem: "Counter always 0"**
- Check you're using the correct storage key
- Verify contract hash is correct
- Make sure increment transactions are confirming

## Security Notes

⚠️ **NEVER use mainnet private keys in this test frontend!**  
⚠️ **Only use testnet keys for testing**  
⚠️ **Don't commit private keys to git**

## What ChainChart Provides

After deployment, ChainChart shows:
- Contract Hash: `0x...` (paste this)
- Transaction Hash: `0x...` (for verification)
- Network: TestNet

You only need the **Contract Hash** to test!

