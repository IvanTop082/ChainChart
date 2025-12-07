/**
 * Deploy contract using neon-js (EXACTLY like NeoNova does)
 * 
 * This replicates NeoNova's deployment:
 * - Uses neon-js's experimental.deployContract for local
 * - Uses wallet adapter's invoke() pattern for testnet
 * 
 * Usage: node deploy_with_neonjs.js <nef_path> <manifest_path> <private_key_hex_or_wif> <rpc_url>
 */

const { sc, u, wallet, experimental, rpc } = require('@cityofzion/neon-js');
const fs = require('fs');
const path = require('path');

async function deployContract() {
    try {
        // Get arguments
        const args = process.argv.slice(2);
        if (args.length < 4) {
            console.error('Usage: node deploy_with_neonjs.js <nef_path> <manifest_path> <private_key_hex_or_wif> <rpc_url>');
            process.exit(1);
        }

        const [nefPath, manifestPath, privateKey, rpcUrl] = args;

        // Read files
        const nefBytes = fs.readFileSync(nefPath);
        const manifestJson = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));

        // Parse NEF and manifest using neon-js (exactly like NeoNova)
        const nefFile = sc.NEF.fromBuffer(nefBytes);
        const contractManifest = sc.ContractManifest.fromJson(manifestJson);

        // Create account from private key (supports both HEX and WIF format)
        // wallet.Account auto-detects format: WIF (starts with K/L/c) or HEX (with/without 0x prefix)
        let account; 
        try {
            // Try to create account - neon-js auto-detects WIF vs HEX
            account = new wallet.Account(privateKey);
        } catch (error) {
            // If it fails, try treating as HEX (remove 0x prefix if present)
            const hexKey = privateKey.startsWith('0x') ? privateKey.slice(2) : privateKey;
            account = new wallet.Account(hexKey);
        }

        // Get network magic from RPC
        const rpcClient = new rpc.RPCClient(rpcUrl);
        const versionInfo = await rpcClient.getVersion();
        const networkMagic = versionInfo.protocol.network;

        console.log(`Network magic: ${networkMagic}`);
        console.log(`Account address: ${account.address}`);

        // Check GAS balance before deployment (informational only)
        // Note: We don't block deployment here - let experimental.deployContract handle the actual check
        // as it may use a different method or have more accurate balance information
        try {
            const balances = await rpcClient.getNep17Balances(account.address);
            let gasBalance = 0;
            let balanceDetails = "Unable to parse";
            
            if (balances && balances.balance && Array.isArray(balances.balance)) {
                // Try multiple field names (RPC response format can vary)
                const gasAsset = balances.balance.find(b => 
                    (b.asset_symbol === 'GAS' || b.symbol === 'GAS') || 
                    (b.asset_hash === '0xd2a4cff31913016155e38e474a2c06d08be276cf' || 
                     b.assethash === '0xd2a4cff31913016155e38e474a2c06d08be276cf') ||
                    (b.asset && b.asset.symbol === 'GAS')
                );
                if (gasAsset) {
                    // Amount is in smallest unit (8 decimals for GAS)
                    // e.g., "2989090036" = 29.89090036 GAS
                    const amountStr = gasAsset.amount || gasAsset.value || '0';
                    const amountInt = parseInt(amountStr, 10);
                    gasBalance = amountInt / Math.pow(10, parseInt(gasAsset.decimals || '8', 10));
                    balanceDetails = `Found GAS: ${gasBalance} (raw: ${amountStr})`;
                } else {
                    balanceDetails = `No GAS entry in balance array (${balances.balance.length} assets found)`;
                }
            } else {
                balanceDetails = `Balance structure: ${JSON.stringify(balances)}`;
            }
            
            console.log(`💰 GAS Balance Check: ${balanceDetails}`);
            console.log(`   Account: ${account.address}`);
            console.log(`   Detected GAS: ${gasBalance}`);
            
            if (gasBalance > 0) {
                console.log(`   ✅ Account has GAS! Ready for deployment.`);
            } else {
                console.log(`   ⚠️  Note: This is a preliminary check. experimental.deployContract will verify balance before deployment.`);
            }
            
            // Don't block deployment - let experimental.deployContract handle it
            // It may have more accurate balance information or use a different RPC method
        } catch (balanceError) {
            console.log(`⚠️  Warning: Could not check GAS balance: ${balanceError.message}`);
            console.log(`   Continuing with deployment - experimental.deployContract will verify balance`);
        }
        
        // Log explorer URL for manual verification
        console.log(`\n🔍 Verify GAS balance manually:`);
        console.log(`   TestNet Explorer: https://testnet.neotube.org/address/${account.address}`);
        console.log(`   Dora Explorer: https://dora.coz.io/neotracker/testnet/address/${account.address}`);

        // Deploy using neon-js experimental.deployContract (exactly like NeoNova for local)
        // This handles ALL transaction building, signing, and sending
        // If this doesn't throw an exception, deployment succeeded (even if we can't parse the result)
        let deploymentSucceeded = false;
        let result = null;
        
        try {
            result = await experimental.deployContract(
                nefFile,
                contractManifest,
                {
                    networkMagic: networkMagic,
                    rpcAddress: rpcUrl,
                    account: account
                }
            );
            
            // If we got here without exception, deployment succeeded
            deploymentSucceeded = true;
        } catch (deployError) {
            // Handle deployment errors
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
                process.exit(0); // Exit with success code since this is expected
            } else {
                // Re-throw other deployment errors
                throw deployError;
            }
        }
        
        // If deployment succeeded, try to extract transaction hash
        if (deploymentSucceeded) {
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
            
            // Log debug info only if we couldn't extract txHash (for troubleshooting)
            if (!txHash && result) {
                console.error(`DEBUG: result type: ${typeof result}`);
                if (typeof result === 'object') {
                    console.error(`DEBUG: result keys: ${Object.keys(result).join(', ')}`);
                    console.error(`DEBUG: full result: ${JSON.stringify(result, null, 2)}`);
                }
            }
            
            // Always calculate contract hash (needed for frontend connection)
            const contractHash = experimental.getContractHash(
                u.HexString.fromHex(wallet.getScriptHashFromAddress(account.address)),
                nefFile.checksum,
                contractManifest.name
            );
            
            if (txHash) {
                // Convert to string if it's an object
                if (typeof txHash === 'object' && txHash.toString) {
                    txHash = txHash.toString();
                }
                // Return both tx_hash and contract_hash
                console.log(JSON.stringify({
                    success: true,
                    tx_hash: txHash,
                    contract_hash: `0x${contractHash}`,
                    error: null
                }));
            } else {
                // No tx_hash but deployment succeeded - return contract_hash
                console.log(JSON.stringify({
                    success: true,
                    tx_hash: null,
                    contract_hash: `0x${contractHash}`,
                    error: null,
                    note: 'Deployment succeeded but transaction hash not found in response. Contract hash calculated.'
                }));
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

