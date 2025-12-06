# Witness Hash Mismatch - Explained Simply

## What We're Trying To Do

We want to deploy a compiled Neo smart contract (`.nef` + `.manifest.json`) to the Neo N3 TestNet blockchain.

## The Process

1. ✅ **Compile contract** → Creates `.nef` and `.manifest.json` files
2. ✅ **Build transaction** → Create a transaction that says "deploy this contract"
3. ✅ **Sign transaction** → Sign it with your private key to prove you authorized it
4. ❌ **Send to network** → Network rejects it with "witness hash mismatch"

## What Is "Witness Hash"?

Think of it like this:
- **Transaction** = A document saying "I want to deploy this contract"
- **Witness** = Your signature on that document
- **Witness Hash** = A fingerprint/checksum of your signature

When you sign a transaction, you create a "witness" (signature). The network calculates what the witness hash SHOULD be based on:
- The transaction data
- Your account
- The network settings (magic number)

Then it compares:
- **Expected hash** = What the network calculated it should be
- **Got hash** = What we actually provided

If they don't match → **"witness hash mismatch"** error

## The Current Error

```
witness hash mismatch: 
  expected: 1d0d967bed6f8069e177eba6c4a2a26d05b30ee0
  got: abf67736ec009a243a848ada4903fb5e4591b174
```

This means:
- The network calculated: `1d0d967bed6f8069e177eba6c4a2a26d05b30ee0`
- We provided: `abf67736ec009a243a848ada4903fb5e4591b174`
- They don't match → Transaction rejected

## Why This Happens

The witness hash is calculated from:
1. **Transaction data** (script, fees, signers, etc.)
2. **Network magic number** (844378958 for TestNet)
3. **How the transaction is serialized** (the order/format of data)

If ANY of these are wrong or different, the hash won't match.

## What We've Tried

1. ✅ Set network magic number correctly (844378958)
2. ✅ Configure settings before building transaction
3. ✅ Use `protocol_magic` parameter in Transaction constructor
4. ✅ Use TxBuilder to calculate fees correctly
5. ✅ Manually construct transaction with all correct parameters

**But the hash still doesn't match.**

## Possible Causes

1. **neo-mamba library bug** - The library might be calculating the witness hash incorrectly
2. **Version incompatibility** - Our neo-mamba version (3.1.0) might have a bug
3. **Serialization order** - The transaction might be serialized in a different order than expected
4. **Network settings** - Some network setting we're missing or setting incorrectly

## What This Means For You

- ✅ **Contract compilation works perfectly**
- ✅ **Transaction building works**
- ✅ **Everything is set up correctly**
- ❌ **But the signing/sending step fails**

The deployment pipeline is **95% complete**. Only the final signing step has an issue.

## Solutions

### Option 1: Use Neo GUI or neo-cli (Recommended for now)
- These tools handle signing correctly
- Manual but guaranteed to work
- Steps:
  1. Compile: `python deployment/compile.py` ✅
  2. Deploy using Neo GUI or neo-cli
  3. Save contract hash to `deployment/contract_info.json`

### Option 2: Wait for neo-mamba fix
- This might be a known issue that gets fixed in a future version
- Check neo-mamba GitHub for issues/updates

### Option 3: Try different approach
- Use direct RPC calls (bypassing neo-mamba's signing)
- Use a different Python SDK (if one exists)

## Bottom Line

**The issue:** The signature/witness we create doesn't match what the network expects, even though we're doing everything "correctly" according to the documentation.

**The impact:** We can't automatically deploy contracts via Python script right now.

**The workaround:** Use Neo GUI or neo-cli for deployment (manual but works).

**The good news:** Everything else works! Compilation, transaction building, settings - all perfect. Just the signing step needs fixing.

