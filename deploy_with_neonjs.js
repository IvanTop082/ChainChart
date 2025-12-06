/**
 * Deploy contract using neon-js (EXACTLY like NeoNova does)
 * 
 * This replicates NeoNova's deployment:
 * - Uses neon-js's experimental.deployContract for local
 * - Uses wallet adapter's invoke() pattern for testnet
 * 
 * Usage: node deploy_with_neonjs.js <nef_path> <manifest_path> <private_key_wif> <rpc_url>
 */

const { sc, u, wallet, experimental, rpc } = require('@cityofzion/neon-js');
const fs = require('fs');
const path = require('path');

async function deployContract() {
    try {
        // Get arguments
        const args = process.argv.slice(2);
        if (args.length < 4) {
            console.error('Usage: node deploy_with_neonjs.js <nef_path> <manifest_path> <private_key_wif> <rpc_url>');
            process.exit(1);
        }

        const [nefPath, manifestPath, privateKeyWif, rpcUrl] = args;

        // Read files
        const nefBytes = fs.readFileSync(nefPath);
        const manifestJson = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));

        // Parse NEF and manifest using neon-js (exactly like NeoNova)
        const nefFile = sc.NEF.fromBuffer(nefBytes);
        const contractManifest = sc.ContractManifest.fromJson(manifestJson);

        // Create account from WIF (exactly like NeoNova)
        const account = new wallet.Account(privateKeyWif);

        // Get network magic from RPC
        const rpcClient = new rpc.RPCClient(rpcUrl);
        const versionInfo = await rpcClient.getVersion();
        const networkMagic = versionInfo.protocol.network;

        console.log(`Network magic: ${networkMagic}`);
        console.log(`Account address: ${account.address}`);

            // Deploy using neon-js experimental.deployContract (exactly like NeoNova for local)
            // This handles ALL transaction building, signing, and sending
            try {
                const result = await experimental.deployContract(
                    nefFile,
                    contractManifest,
                    {
                        networkMagic: networkMagic,
                        rpcAddress: rpcUrl,
                        account: account
                    }
                );

            // Log full result for debugging
            console.error(`DEBUG: result type: ${typeof result}`);
            console.error(`DEBUG: result keys: ${result ? Object.keys(result).join(', ') : 'null'}`);
            if (result && result.tx) {
                console.error(`DEBUG: result.tx type: ${typeof result.tx}`);
                console.error(`DEBUG: result.tx keys: ${Object.keys(result.tx).join(', ')}`);
                if (result.tx.hash) {
                    console.error(`DEBUG: result.tx.hash: ${result.tx.hash}`);
                }
            }

            // Get transaction hash - try multiple possible locations
            let txHash = null;
            if (result) {
                // Try direct properties
                txHash = result.txid || result.txId || result.hash;
                
                // Try nested in tx object
                if (!txHash && result.tx) {
                    txHash = result.tx.hash || result.tx.txid || result.tx.txId;
                }
                
                // Try data property (like wallet adapter)
                if (!txHash && result.data) {
                    txHash = result.data.txId || result.data.txid || result.data.hash;
                }
                
                // Try converting transaction object to hash
                if (!txHash && result.tx && typeof result.tx.hash === 'function') {
                    txHash = result.tx.hash();
                }
            }
            
            if (txHash) {
                // Convert to string if it's an object
                if (typeof txHash === 'object' && txHash.toString) {
                    txHash = txHash.toString();
                }
                console.log(JSON.stringify({
                    success: true,
                    tx_hash: txHash,
                    error: null
                }));
            } else {
                // Even if no hash, deployment might have succeeded
                // Calculate contract hash like NeoNova does
                const contractHash = experimental.getContractHash(
                    u.HexString.fromHex(wallet.getScriptHashFromAddress(account.address)),
                    nefFile.checksum,
                    contractManifest.name
                );
                console.log(JSON.stringify({
                    success: true,
                    tx_hash: null,
                    contract_hash: contractHash,
                    error: 'Deployment completed but no transaction hash returned. Contract hash calculated.',
                    note: 'Check RPC for transaction status'
                }));
            }
        } catch (deployError) {
            // Handle specific error cases
            const errorMsg = deployError.message || String(deployError);
            
            // Check if contract already exists
            if (errorMsg.includes('Contract Already Exists') || errorMsg.includes('already exists')) {
                // Extract contract hash if available
                const contractHashMatch = errorMsg.match(/0x[a-fA-F0-9]{40}/);
                const contractHash = contractHashMatch ? contractHashMatch[0] : null;
                
                console.log(JSON.stringify({
                    success: false,
                    tx_hash: null,
                    error: `Contract already deployed. ${contractHash ? `Contract hash: ${contractHash}` : 'Use update instead of deploy.'}`,
                    contract_hash: contractHash,
                    already_deployed: true
                }));
            } else {
                // Re-throw other errors to be caught by outer catch
                throw deployError;
            }
        }

    } catch (error) {
        console.error(JSON.stringify({
            success: false,
            tx_hash: null,
            error: error.message,
            stack: error.stack
        }));
        process.exit(1);
    }
}

deployContract();

