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
        const result = await experimental.deployContract(
            nefFile,
            contractManifest,
            {
                networkMagic: networkMagic,
                rpcAddress: rpcUrl,
                account: account
            }
        );

        // Get transaction hash
        const txHash = result.txid || result.txId || result.hash;
        
        if (txHash) {
            console.log(JSON.stringify({
                success: true,
                tx_hash: txHash,
                error: null
            }));
        } else {
            console.log(JSON.stringify({
                success: false,
                tx_hash: null,
                error: 'Deployment completed but no transaction hash returned'
            }));
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

