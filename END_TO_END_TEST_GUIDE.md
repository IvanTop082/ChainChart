# End-to-End Test Guide: ChainChart → Deploy → Frontend Connection

This guide will walk you through testing the complete flow from creating a contract in ChainChart to connecting to it from a separate frontend.

## Step 1: Create a Simple Contract in ChainChart

1. **Open ChainChart UI** (http://localhost:3000 or your dev server)
2. **Create a simple counter contract:**
   - Add a **Storage** node (for storing the counter value)
   - Add an **Operation** node (for the increment logic)
   - Connect them with an edge
   - Or just use the existing counter example if you have one

3. **Click "Generate Smart Contract"**
   - Wait for SpoonOS to generate the contract
   - You should see a success message
   - The contract is now saved to filesystem and Supabase

## Step 2: Deploy the Contract

1. **Click "Deploy to TestNet"** button
2. **Wait for deployment** (may take 30-60 seconds)
3. **When deployment succeeds:**
   - A modal will pop up showing:
     - ✅ Contract Hash (e.g., `0xa34b5e45ab9f62f03ac244c04059388867360080`)
     - ✅ Transaction Hash (if available)
     - ✅ Connection instructions
   - **COPY THE CONTRACT HASH** - you'll need this!

## Step 3: Create a Simple Frontend

### Option A: Simple HTML + JavaScript (Easiest)

Create a new folder for your test frontend:

```bash
mkdir test-frontend
cd test-frontend
```

Create `index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChainChart Contract Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #1a1a1a;
            color: #fff;
        }
        .container {
            background: #2a2a2a;
            padding: 30px;
            border-radius: 10px;
        }
        input, button {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid #444;
        }
        input {
            width: 100%;
            background: #1a1a1a;
            color: #fff;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background: #45a049;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background: #1a1a1a;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }
        .error {
            border-left-color: #f44336;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 ChainChart Contract Test</h1>
        
        <div>
            <label>Contract Hash:</label>
            <input type="text" id="contractHash" placeholder="0x..." />
        </div>
        
        <div>
            <label>Method Name:</label>
            <input type="text" id="methodName" placeholder="counter" value="counter" />
        </div>
        
        <button onclick="callContract()">Call Contract Method</button>
        <button onclick="incrementCounter()">Increment Counter</button>
        
        <div id="result"></div>
    </div>

    <!-- Load neon-js from CDN -->
    <script src="https://cdn.jsdelivr.net/npm/@cityofzion/neon-js@latest/lib/browser/index.js"></script>
    <script>
        const RPC_URL = "http://seed3t5.neo.org:20332";
        
        async function callContract() {
            const contractHash = document.getElementById('contractHash').value.trim();
            const methodName = document.getElementById('methodName').value.trim();
            const resultDiv = document.getElementById('result');
            
            if (!contractHash) {
                resultDiv.innerHTML = '<div class="result error">Please enter a contract hash</div>';
                return;
            }
            
            if (!methodName) {
                resultDiv.innerHTML = '<div class="result error">Please enter a method name</div>';
                return;
            }
            
            resultDiv.innerHTML = '<div class="result">Calling contract... ⏳</div>';
            
            try {
                const { rpc, sc, u } = window.neon;
                const client = new rpc.RPCClient(RPC_URL);
                
                const script = sc.createScript({
                    scriptHash: contractHash,
                    operation: methodName,
                    args: []
                });
                
                const result = await client.invokeScript(u.HexString.fromHex(script));
                
                if (result.state === 'FAULT') {
                    resultDiv.innerHTML = `<div class="result error">❌ Execution failed: ${result.exception || 'Unknown error'}</div>`;
                    return;
                }
                
                let value = null;
                if (result.stack && result.stack.length > 0) {
                    const stackItem = result.stack[0];
                    value = stackItem.value !== undefined ? stackItem.value : stackItem;
                }
                
                resultDiv.innerHTML = `
                    <div class="result">
                        <h3>✅ Success!</h3>
                        <p><strong>Method:</strong> ${methodName}</p>
                        <p><strong>Result:</strong> ${JSON.stringify(value, null, 2)}</p>
                        <p><strong>Gas Consumed:</strong> ${result.gasconsumed || 'N/A'}</p>
                    </div>
                `;
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error">❌ Error: ${error.message}</div>`;
                console.error('Error:', error);
            }
        }
        
        async function incrementCounter() {
            const contractHash = document.getElementById('contractHash').value.trim();
            const resultDiv = document.getElementById('result');
            
            if (!contractHash) {
                resultDiv.innerHTML = '<div class="result error">Please enter a contract hash</div>';
                return;
            }
            
            resultDiv.innerHTML = '<div class="result">Incrementing counter... ⏳</div>';
            
            try {
                const { rpc, sc, u } = window.neon;
                const client = new rpc.RPCClient(RPC_URL);
                
                const script = sc.createScript({
                    scriptHash: contractHash,
                    operation: "increment",
                    args: []
                });
                
                const result = await client.invokeScript(u.HexString.fromHex(script));
                
                if (result.state === 'FAULT') {
                    resultDiv.innerHTML = `<div class="result error">❌ Execution failed: ${result.exception || 'Unknown error'}</div>`;
                    return;
                }
                
                resultDiv.innerHTML = `
                    <div class="result">
                        <h3>✅ Counter Incremented!</h3>
                        <p><strong>Gas Consumed:</strong> ${result.gasconsumed || 'N/A'}</p>
                        <p><em>Note: This is a test invoke. To actually write to the blockchain, you need to sign and broadcast the transaction.</em></p>
                    </div>
                `;
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error">❌ Error: ${error.message}</div>`;
                console.error('Error:', error);
            }
        }
    </script>
</body>
</html>
```

### Option B: React/Next.js Frontend (More Professional)

If you prefer a React setup:

```bash
npx create-next-app@latest test-frontend
cd test-frontend
npm install @cityofzion/neon-js
```

Then create a simple component to call your contract.

## Step 4: Test the Connection

1. **Open your frontend** (HTML file in browser, or run your React app)
2. **Paste the contract hash** from the deployment modal
3. **Click "Call Contract Method"** with method name `counter`
4. **You should see the counter value!**

## Step 5: Verify It Works

✅ **Success indicators:**
- Frontend can read from your contract
- Counter value is returned correctly
- No errors in browser console
- Gas consumption is shown

## Troubleshooting

### "Contract hash not found"
- Make sure you copied the full hash (starts with `0x`, 42 characters total)
- Check the hash in the TestNet explorer

### "Method not found"
- Check the manifest.json to see available methods
- Method names are case-sensitive
- Make sure you're using the exact method name from the contract

### "RPC connection failed"
- Check your internet connection
- Try a different RPC URL: `http://seed1t5.neo.org:20332` or `http://seed2t5.neo.org:20332`

### "Execution failed"
- Check the contract method signature
- Make sure you're passing the correct parameters
- Check the contract code to see what the method expects

## Next Steps

Once this works, you can:
1. Add more methods to your contract
2. Create a more sophisticated frontend
3. Add wallet connection for write operations
4. Deploy to MainNet (when ready)

## Quick Reference

- **Contract Hash**: From deployment modal (starts with `0x`)
- **RPC URL**: `http://seed3t5.neo.org:20332` (TestNet)
- **Library**: `@cityofzion/neon-js`
- **TestNet Explorer**: https://dora.coz.io/neotracker/testnet/

Good luck! 🚀

