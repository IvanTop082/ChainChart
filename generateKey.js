const { wallet } = require('@cityofzion/neon-js');

const acct = new wallet.Account();   // automatically generates a new keypair

console.log("Address:", acct.address);
console.log("Public Key:", acct.publicKey);
console.log("Private Key (HEX):", acct.privateKey);   // This is what you put in NEO_PRIVATE_KEY
console.log("Private Key (WIF):", acct.WIF);



