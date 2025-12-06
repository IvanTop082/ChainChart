/**
 * Verify WIF and show account address
 * Use this to check if your WIF matches the account with GAS
 * 
 * Usage: node verify_wif.js <WIF>
 */

const { wallet, rpc } = require('@cityofzion/neon-js');

async function verifyWIF() {
    const wif = process.argv[2];
    
    if (!wif) {
        console.error('Usage: node verify_wif.js <WIF>');
        console.error('Example: node verify_wif.js Kwj85Ds71XQSTh1ZLRsLQsTKGJRvZbxUz69arQcjEBfTXhwTsvu2');
        process.exit(1);
    }
    
    try {
        const account = new wallet.Account(wif);
        console.log('✅ WIF is valid!');
        console.log(`\nAccount Address: ${account.address}`);
        console.log(`Public Key: ${account.publicKey}`);
        
        // Check GAS balance
        try {
            const rpcClient = new rpc.RPCClient('http://seed3t5.neo.org:20332');
            const balances = await rpcClient.getNep17Balances(account.address);
            
            let gasBalance = 0;
            if (balances && balances.balance && Array.isArray(balances.balance)) {
                const gasAsset = balances.balance.find(b => 
                    b.asset_symbol === 'GAS' || 
                    b.asset_hash === '0xd2a4cff31913016155e38e474a2c06d08be276cf'
                );
                if (gasAsset) {
                    gasBalance = parseFloat(gasAsset.amount || 0);
                }
            }
            
            console.log(`\n💰 GAS Balance: ${gasBalance}`);
            console.log(`\n🔍 Verify on explorer:`);
            console.log(`   https://testnet.neotube.org/address/${account.address}`);
            
            if (gasBalance > 0) {
                console.log(`\n✅ This account has GAS! You can use this WIF in .env`);
            } else {
                console.log(`\n⚠️  This account has 0 GAS. Make sure this matches your NeoLine wallet.`);
            }
        } catch (balanceError) {
            console.log(`\n⚠️  Could not check balance: ${balanceError.message}`);
        }
        
    } catch (error) {
        console.error(`❌ Invalid WIF: ${error.message}`);
        process.exit(1);
    }
}

verifyWIF();

