# How to Interact with Your Counter Smart Contract

## Your Contract Overview

Your counter contract has one main method:
- **`increment()`** - Increases the counter by 1 and saves it to blockchain storage

The counter value is stored in blockchain storage with the key `"counter"`.

## Understanding the Contract
g
**Contract Hash:** `CounterContract_1765089445730_6228` (use the actual deployed contract hash)

**Storage:**
- Key: `"counter"`
- Value: `BigInteger` (starts at 0)

**Method:**
- `increment()` - No parameters, returns `Void`

## How to Interact with the Counter

### 1. Call `increment()` to Increase the Counter

When you call `increment()`, the contract will:
1. Read the current value from storage (or 0 if first time)
2. Add 1 to it
3. Save the new value back to storage

**Important:** Each call to `increment()` requires a blockchain transaction, which means:
- You need a wallet to sign the transaction
- You'll pay gas fees
- The transaction needs to be confirmed on the blockchain

### 2. Read the Counter Value

Since your contract doesn't have a `get()` method, you have two options:

**Option A: Read directly from storage (Recommended)**
```typescript
import { rpc, sc, u } from '@cityofzion/neon-js';

const client = new rpc.RPCClient('https://testnet.onegate.space');
const contractHash = 'YOUR_CONTRACT_HASH';

// Read storage directly
const storageKey = Buffer.from('counter', 'utf-8');
const result = await client.getStorage(contractHash, u.HexString.fromHex(storageKey.toString('hex')));

if (result && result.value) {
  const counterValue = parseInt(result.value, 16); // Convert from hex
  console.log('Counter value:', counterValue);
} else {
  console.log('Counter value: 0 (not set yet)');
}
```

**Option B: Add a get() method to your contract**
You would need to recompile and redeploy with a `get()` method added.

### 3. Frontend Integration Example

```typescript
import { rpc, sc, u, wallet } from '@cityofzion/neon-js';

const RPC_URL = 'https://testnet.onegate.space';
const CONTRACT_HASH = 'YOUR_DEPLOYED_CONTRACT_HASH';

// Function to increment the counter
async function incrementCounter(account: wallet.Account) {
  const client = new rpc.RPCClient(RPC_URL);
  
  // Create the script to call increment()
  const script = sc.createScript({
    scriptHash: CONTRACT_HASH,
    operation: 'increment',
    args: [] // No arguments needed
  });
  
  // Create and sign transaction
  const tx = new sc.Transaction({
    signers: [{
      account: account.scriptHash,
      scopes: sc.WitnessScope.CalledByEntry
    }],
    script: script
  });
  
  // Sign with your wallet
  await tx.sign(account);
  
  // Send transaction to blockchain
  const result = await client.sendRawTransaction(u.HexString.fromHex(tx.serialize()));
  
  console.log('Transaction sent:', result);
  return result;
}

// Function to read counter value from storage
async function getCounterValue() {
  const client = new rpc.RPCClient(RPC_URL);
  
  // Convert "counter" string to hex for storage key
  const storageKey = Buffer.from('counter', 'utf-8');
  const keyHex = u.HexString.fromHex(storageKey.toString('hex'));
  
  try {
    const result = await client.getStorage(CONTRACT_HASH, keyHex);
    
    if (result && result.value) {
      // Convert hex string to number
      const value = parseInt(result.value, 16);
      return value;
    }
    return 0; // Default to 0 if not set
  } catch (error) {
    console.error('Error reading counter:', error);
    return 0;
  }
}
```

### 4. React Component Example

```tsx
import React, { useState, useEffect } from 'react';
import { wallet } from '@cityofzion/neon-js';

function CounterApp() {
  const [counter, setCounter] = useState<number>(0);
  const [account, setAccount] = useState<wallet.Account | null>(null);
  const [loading, setLoading] = useState(false);

  // Load counter value on mount and periodically
  useEffect(() => {
    loadCounter();
    const interval = setInterval(loadCounter, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadCounter = async () => {
    try {
      const value = await getCounterValue();
      setCounter(value);
    } catch (error) {
      console.error('Failed to load counter:', error);
    }
  };

  const handleIncrement = async () => {
    if (!account) {
      alert('Please connect your wallet first');
      return;
    }

    setLoading(true);
    try {
      await incrementCounter(account);
      // Wait a moment for transaction to be confirmed
      setTimeout(() => {
        loadCounter();
        setLoading(false);
      }, 3000);
    } catch (error) {
      console.error('Failed to increment:', error);
      setLoading(false);
      alert('Failed to increment counter. Check console for details.');
    }
  };

  return (
    <div>
      <h1>Counter dApp</h1>
      <div>
        <p>Current Counter: {counter}</p>
        <button 
          onClick={handleIncrement} 
          disabled={!account || loading}
        >
          {loading ? 'Processing...' : 'Increment Counter'}
        </button>
        <button onClick={loadCounter}>
          Refresh
        </button>
      </div>
    </div>
  );
}
```

## Step-by-Step Guide

### Step 1: Deploy Your Contract
1. Compile your contract: `nccs CounterContract_1765089445730_6228.cs`
2. Deploy to Neo TestNet
3. Save the contract hash

### Step 2: Connect Wallet
```typescript
// Example: Connect using neon-js
import { wallet } from '@cityofzion/neon-js';

const wif = 'YOUR_WIF_KEY'; // Never expose this in production!
const account = new wallet.Account(wif);
```

### Step 3: Call increment()
```typescript
// Use the incrementCounter function above
await incrementCounter(account);
```

### Step 4: Read Counter Value
```typescript
// Use the getCounterValue function above
const value = await getCounterValue();
console.log('Counter is now:', value);
```

## Important Notes

1. **Storage Key:** The contract uses `"counter"` as the storage key. Make sure to use this exact string when reading.

2. **First Call:** The first time you call `increment()`, the counter will be 0, then become 1.

3. **Transaction Confirmation:** After calling `increment()`, wait a few seconds for the transaction to be confirmed before reading the new value.

4. **Gas Fees:** Each `increment()` call costs gas. Make sure your wallet has enough GAS tokens.

5. **No Get Method:** Since there's no `get()` method, you must read from storage directly using `getStorage()`.

## Testing Your Contract

1. **Test Increment:**
   ```bash
   # Call increment() via RPC
   # Check storage after transaction confirms
   ```

2. **Verify Storage:**
   ```typescript
   const value = await getCounterValue();
   console.log('Counter value:', value);
   ```

3. **Multiple Increments:**
   - Call `increment()` multiple times
   - Each call should increase the counter by 1
   - Verify the value increases: 0 → 1 → 2 → 3...

## Troubleshooting

**Problem:** Counter always shows 0
- **Solution:** Make sure you're reading from the correct contract hash and storage key

**Problem:** increment() doesn't work
- **Solution:** Check that your wallet has GAS tokens and the transaction is being signed correctly

**Problem:** Can't read storage
- **Solution:** Verify the contract hash is correct and the contract is deployed

## Next Steps

1. Deploy your contract to Neo TestNet
2. Get the contract hash
3. Use the code examples above to interact with it
4. Build your frontend UI
5. Test incrementing and reading the counter

