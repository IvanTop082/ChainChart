# Witness Hash Mismatch - Analysis & Next Steps

## Current Status

The deployment script is correctly:
- ✅ Configuring Neo N3 TestNet settings (magic: 844378958)
- ✅ Building transactions with TxBuilder
- ✅ Creating signers and signing functions
- ✅ Connecting to RPC endpoint

However, we're getting a **witness hash mismatch** error:
```
witness hash mismatch: expected 1d0d967bed6f8069e177eba6c4a2a26d05b30ee0, got a0373ce0249ee3079efce84f540a6ffa5e3dcc62
```

## Root Cause Analysis

The witness hash mismatch indicates that:
1. The transaction is being built correctly
2. The signing is happening, but the witness hash doesn't match what the network expects
3. The network calculates the expected hash from the transaction data (excluding witnesses)
4. Our witness hash is calculated from the signed transaction data

## Possible Causes

1. **Network Magic Number Mismatch**
   - The witness hash includes the network magic number
   - If the RPC client is using a different magic number than our settings, the hash won't match
   - **Solution**: Ensure RPC client uses the same protocol settings

2. **Transaction Serialization Order**
   - Neo transactions must be serialized in a specific order
   - If the order is wrong, the hash calculation will be different
   - **Solution**: Verify TxBuilder is serializing correctly

3. **Signing Function Issue**
   - The `sign_with_account` function might not be creating the witness correctly
   - The witness needs to match the transaction hash calculation
   - **Solution**: Check if we need to manually create the witness

4. **RPC Client Protocol Settings**
   - The RPC client might need protocol settings passed explicitly
   - Currently, we're relying on module-level settings
   - **Solution**: Pass protocol settings to RPC client if possible

## Recommended Next Steps

1. **Verify RPC Client Settings**
   - Check if NeoRpcClient accepts protocol settings
   - Ensure RPC client uses the same network magic as our settings

2. **Try Alternative Signing Method**
   - Use `build_unsigned()` and manually create witness
   - Calculate witness hash manually to match network expectations

3. **Check neo-mamba Version Compatibility**
   - Verify we're using a compatible version
   - Check if there are known issues with witness hash calculation

4. **Use Neo GUI or neo-cli as Reference**
   - Compare how they sign transactions
   - See if there's a different approach we should use

## Current Workaround

For now, the deployment script will fail with the witness hash mismatch. The transaction is being built correctly, but the signing mechanism needs adjustment.

## Files to Check

- `generator/neo_deploy.py` - Main deployment logic
- `deployment/deploy.py` - Deployment script wrapper
- Check neo-mamba documentation for correct signing approach

