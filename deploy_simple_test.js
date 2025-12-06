/**
 * Quick deployment script for testing SimpleCounter contract
 * 
 * Usage: node deploy_simple_test.js <private_key_wif_or_hex> [rpc_url]
 * 
 * Example:
 *   node deploy_simple_test.js KxDgvEKzgSBPPfuVfw67oPQBSjidEiqTHURKSDL1R7yGaGYAeYnr
 *   node deploy_simple_test.js KxDgvEKzgSBPPfuVfw67oPQBSjidEiqTHURKSDL1R7yGaGYAeYnr http://seed3t5.neo.org:20332
 */

const { sc, u, wallet, experimental, rpc } = require('@cityofzion/neon-js');
const fs = require('fs');
const path = require('path');

async function deploySimpleCounter() {
    try {
        // Get arguments
        const args = process.argv.slice(2);
        if (args.length < 1) {
            console.error('Usage: node deploy_simple_test.js <private_key_wif_or_hex> [rpc_url]');
            console.error('\nExample:');
            console.error('  node deploy_simple_test.js KxDgvEKzgSBPPfuVfw67oPQBSjidEiqTHURKSDL1R7yGaGYAeYnr');
            process.exit(1);
        }

        const [privateKey, rpcUrl = 'http://seed3t5.neo.org:20332'] = args;

        // Paths to contract files - using TestDeploy contract to avoid "already exists" error
        // This contract has methods: setValue, getValue, hello
        const nefPath = path.join(__dirname, 'bin', 'sc', 'TestDeploy.nef');
        const manifestPath = path.join(__dirname, 'bin', 'sc', 'TestDeploy.manifest.json');
        
        // Alternative: Use SimpleCounter (if you want to try with a different account)
        // const nefPath = path.join(__dirname, 'bin', 'sc', 'SimpleCounter.nef');
        // const manifestPath = path.join(__dirname, 'bin', 'sc', 'SimpleCounter.manifest.json');

        // Check if files exist
        if (!fs.existsSync(nefPath)) {
            console.error(`❌ ERROR: NEF file not found: ${nefPath}`);
            console.error('   Make sure SimpleCounter contract is compiled.');
            process.exit(1);
        }

        if (!fs.existsSync(manifestPath)) {
            console.error(`❌ ERROR: Manifest file not found: ${manifestPath}`);
            process.exit(1);
        }

        console.log('📦 Loading contract...');
        console.log(`   NEF: ${nefPath}`);
        console.log(`   Manifest: ${manifestPath}`);

        // Read files
        const nefBytes = fs.readFileSync(nefPath);
        const manifestJson = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));

        // Parse NEF and manifest using neon-js
        const nefFile = sc.NEF.fromBuffer(nefBytes);
        const contractManifest = sc.ContractManifest.fromJson(manifestJson);

        // Create account from private key
        let account;
        try {
            account = new wallet.Account(privateKey);
        } catch (error) {
            const hexKey = privateKey.startsWith('0x') ? privateKey.slice(2) : privateKey;
            account = new wallet.Account(hexKey);
        }

        console.log(`\n🔐 Account: ${account.address}`);

        // Get network magic from RPC
        const rpcClient = new rpc.RPCClient(rpcUrl);
        const versionInfo = await rpcClient.getVersion();
        const networkMagic = versionInfo.protocol.network;

        console.log(`🌐 Network: ${rpcUrl}`);
        console.log(`   Magic: ${networkMagic}`);

        // Check GAS balance
        try {
            const balances = await rpcClient.getNep17Balances(account.address);
            let gasBalance = 0;
            
            if (balances && balances.balance && Array.isArray(balances.balance)) {
                const gasAsset = balances.balance.find(b => 
                    (b.asset_symbol === 'GAS' || b.symbol === 'GAS') || 
                    (b.asset_hash === '0xd2a4cff31913016155e38e474a2c06d08be276cf' || 
                     b.assethash === '0xd2a4cff31913016155e38e474a2c06d08be276cf') ||
                    (b.asset && b.asset.symbol === 'GAS')
                );
                if (gasAsset) {
                    const amountStr = gasAsset.amount || gasAsset.value || '0';
                    const amountInt = parseInt(amountStr, 10);
                    gasBalance = amountInt / Math.pow(10, parseInt(gasAsset.decimals || '8', 10));
                }
            }
            
            console.log(`💰 GAS Balance: ${gasBalance}`);
            
            if (gasBalance < 1) {
                console.log(`\n⚠️  Warning: Low GAS balance. You may need GAS to deploy.`);
                console.log(`   Get testnet GAS from: https://neotube.org/faucet`);
            }
        } catch (balanceError) {
            console.log(`⚠️  Warning: Could not check GAS balance: ${balanceError.message}`);
        }

        // Deploy contract
        console.log(`\n📤 Deploying contract...`);
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
        let txHash = null;
        if (result) {
            txHash = result.txid || result.txId || result.hash;
            if (!txHash && result.tx) {
                txHash = result.tx.hash || result.tx.txid || result.tx.txId;
            }
            if (!txHash && result.data) {
                txHash = result.data.txId || result.data.txid || result.data.hash;
            }
        }

        // Calculate contract hash
        const contractHash = experimental.getContractHash(
            u.HexString.fromHex(wallet.getScriptHashFromAddress(account.address)),
            nefFile.checksum,
            contractManifest.name
        );

        console.log(`\n✅ Deployment successful!`);
        console.log(`   Contract Hash: 0x${contractHash}`);
        if (txHash) {
            console.log(`   Transaction: ${txHash}`);
        }
        console.log(`\n🔍 View on explorer:`);
        console.log(`   https://testnet.neotube.org/contract/0x${contractHash}`);
        console.log(`   https://dora.coz.io/neotracker/testnet/contract/0x${contractHash}`);

        console.log(JSON.stringify({
            success: true,
            contract_hash: `0x${contractHash}`,
            tx_hash: txHash,
            error: null
        }));

    } catch (error) {
        const errorMsg = error.message || String(error);
        console.error(`\n❌ Deployment failed: ${errorMsg}`);
        
        if (errorMsg.includes('Insufficient GAS') || errorMsg.includes('insufficient')) {
            console.error(`\n💡 You need GAS to deploy. Get testnet GAS from:`);
            console.error(`   https://neotube.org/faucet`);
        }
        
        console.error(JSON.stringify({
            success: false,
            tx_hash: null,
            error: errorMsg,
            stack: error.stack
        }));
        process.exit(1);
    }
}

deploySimpleCounter();

