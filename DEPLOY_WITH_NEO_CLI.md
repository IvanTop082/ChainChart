# Deploy Using Neo-CLI (Alternative Method)

If you have Neo-CLI installed, you can deploy directly without the Python script:

## Steps

1. **Copy contract files to Neo-CLI directory:**
   ```bash
   # Copy from your project
   cp generated_contracts/contract.nef /path/to/neo-cli/
   cp generated_contracts/contract.manifest.json /path/to/neo-cli/
   ```

2. **Start Neo-CLI and connect to TestNet:**
   ```bash
   cd /path/to/neo-cli
   ./neo-cli
   ```

3. **Deploy the contract:**
   ```
   deploy contract.nef contract.manifest.json
   ```

4. **Confirm the transaction when prompted**

5. **Save the contract hash** from the output to your `.env`:
   ```
   NEO_CONTRACT_HASH=0x...
   ```

## If Neo-CLI is not installed

You can download it from:
- https://github.com/neo-project/neo-node/releases

Or continue fixing the Python deployment script.

