# ============================================
# Neo N3 RPC Smart Contract Deployment Script
# No CLI, No GUI, No Node, No neo-mamba
# Pure RPC signing + broadcast
# ============================================

import base64
import hashlib
import json
import os
import requests
from typing import Tuple
from pathlib import Path

try:
    from ecdsa import SigningKey, NIST256p
    from ecdsa.util import sigencode_string
    ECDSA_AVAILABLE = True
except ImportError:
    ECDSA_AVAILABLE = False
    print("⚠️  Warning: ecdsa library not found. Install with: pip install ecdsa")

try:
    import base58
    BASE58_AVAILABLE = True
except ImportError:
    BASE58_AVAILABLE = False
    print("⚠️  Warning: base58 library not found. Install with: pip install base58")

from neo3_contract_builder import ScriptBuilder
from neo3_tx_serializer import Neo3TransactionSerializer

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------

# Get RPC URL from config or environment
try:
    from deployment.config import NEO_RPC_URL, NEO_PRIVATE_KEY
    RPC_URL = NEO_RPC_URL
    PRIVATE_KEY_WIF = NEO_PRIVATE_KEY
except ImportError:
    RPC_URL = os.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")
    PRIVATE_KEY_WIF = os.getenv("NEO_PRIVATE_KEY")

NEF_PATH = "generated_contracts/contract.nef"
MANIFEST_PATH = "generated_contracts/contract.manifest.json"

# -------------------------------------------------------
# WIF → Private Key (32 bytes)
# -------------------------------------------------------

def wif_to_private_key(wif: str) -> bytes:
    """Convert WIF format private key to raw 32-byte private key"""
    if not BASE58_AVAILABLE:
        raise ImportError("base58 library required. Install with: pip install base58")
    
    decoded = base58.b58decode(wif)
    # WIF format: version byte (0x80) + 32 bytes private key + [compression flag] + checksum (4 bytes)
    # Standard WIF: 37 bytes (no compression flag)
    # Compressed WIF: 38 bytes (with compression flag 0x01)
    
    if len(decoded) == 37:
        # Standard WIF (no compression flag)
        payload = decoded[:-4]
        checksum = decoded[-4:]
        private_key = decoded[1:33]  # Skip version byte, get 32 bytes
    elif len(decoded) == 38:
        # Compressed WIF (with compression flag)
        payload = decoded[:-4]
        checksum = decoded[-4:]
        private_key = decoded[1:33]  # Skip version byte, get 32 bytes (compression flag is at index 33)
    else:
        raise ValueError(f"Invalid WIF length: {len(decoded)} (expected 37 or 38)")
    
    # Verify checksum
    hash_result = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if hash_result != checksum:
        raise ValueError("Invalid WIF checksum")
    
    return private_key

# -------------------------------------------------------
# RPC helper
# -------------------------------------------------------

def rpc_call(method: str, params: list):
    """Make an RPC call to Neo node"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    res = requests.post(RPC_URL, json=payload, timeout=30)
    res.raise_for_status()
    result = res.json()
    
    if "error" in result:
        raise Exception(f"RPC error: {result['error']}")
    
    # Return the result, or the full response if result is None
    return result.get("result", result)

# -------------------------------------------------------
# Deploy Script Builder (NeoVM)
# -------------------------------------------------------

def build_deploy_script(nef_bytes: bytes, manifest_str: str) -> bytes:
    """
    Creates the NeoVM script for deployment.
    
    Neo N3 ContractManagement.deploy expects: (nef: ByteString, manifest: ByteString)
    Script format: PUSH nef PUSH manifest CALLT ContractManagement.deploy
    """
    sb = ScriptBuilder()
    
    # Push NEF as bytes first (ContractManagement.deploy expects nef, then manifest)
    sb.emit_push(nef_bytes)
    
    # Push manifest as bytes (UTF-8 encoded JSON string)
    manifest_bytes = manifest_str.encode('utf-8') if isinstance(manifest_str, str) else manifest_str
    sb.emit_push(manifest_bytes)
    
    # Call ContractManagement.deploy using CALLT
    # ContractManagement hash: 0xfffdc93764dbaddd97c48f252a53ea4643faa3fd
    contract_hash_hex = "fffdc93764dbaddd97c48f252a53ea4643faa3fd"
    contract_hash_bytes = bytes.fromhex(contract_hash_hex)
    # Neo N3 UInt160 is stored in little-endian format
    contract_hash_bytes = contract_hash_bytes[::-1]
    
    # Use CALLT to call contract method
    sb.emit_contract_call(contract_hash_bytes, "deploy")
    
    return sb.to_array()

# -------------------------------------------------------
# Convert WIF → script hash (address)
# -------------------------------------------------------

def get_script_hash_from_wif(wif: str) -> str:
    """Convert WIF to script hash (UInt160)"""
    pk = wif_to_private_key(wif)
    sk = SigningKey.from_string(pk, curve=NIST256p)
    vk = sk.get_verifying_key()
    
    # Compressed public key
    pub = b'\x03' + vk.to_string()[:32]
    
    # SHA256 then RIPEMD160
    sha = hashlib.sha256(pub).digest()
    rip = hashlib.new("ripemd160", sha).digest()
    
    # Return as hex string (little-endian for Neo)
    return rip.hex()

# -------------------------------------------------------
# Transaction builder
# -------------------------------------------------------

def build_transaction(script: bytes, signer_hash: str) -> dict:
    """Build a Neo N3 transaction"""
    import random
    
    # Get current block height for validUntilBlock
    try:
        block_count_result = rpc_call("getblockcount", [])
        # Handle both direct result and wrapped result
        if isinstance(block_count_result, dict) and "result" in block_count_result:
            block_count = block_count_result["result"]
        elif isinstance(block_count_result, int):
            block_count = block_count_result
        else:
            block_count = 0
        valid_until_block = block_count + 2102400  # ~1 month
    except:
        valid_until_block = 0  # Will be set by network
    
    # Generate random nonce (uint32) - Neo N3 requires a non-zero nonce
    nonce = random.randint(1, 0xFFFFFFFF)
    
    # Convert script hash to proper format (little-endian hex)
    # signer_hash is already hex string from get_script_hash_from_wif
    # Neo N3 expects UInt160 format (20 bytes, little-endian)
    
    return {
        "version": 0,
        "nonce": nonce,
        "systemFee": "0",
        "networkFee": "0",
        "validUntilBlock": valid_until_block,
        "signers": [
            {
                "account": signer_hash,
                "scopes": "CalledByEntry"
            }
        ],
        "attributes": [],
        "script": base64.b64encode(script).decode(),
        "witnesses": []
    }

# -------------------------------------------------------
# Sign transaction
# -------------------------------------------------------

def sign_transaction(tx: dict, private_key: bytes) -> dict:
    """
    Signs the transaction and adds witness using proper Neo N3 serialization
    """
    if not ECDSA_AVAILABLE:
        raise ImportError("ecdsa library required. Install with: pip install ecdsa")
    
    # Serialize transaction WITHOUT witnesses for signing
    # Neo N3 signs the serialized transaction (without witnesses) + network magic
    tx_serialized = Neo3TransactionSerializer.serialize_for_signing(tx)
    
    # Add network magic to the hash (Neo N3 includes magic in signature)
    magic_bytes = Neo3TransactionSerializer.serialize_uint32(Neo3TransactionSerializer.NETWORK_MAGIC)
    data_to_hash = tx_serialized + magic_bytes
    
    # Hash the serialized transaction + magic
    digest = hashlib.sha256(data_to_hash).digest()
    
    # Sign with ECDSA
    sk = SigningKey.from_string(private_key, curve=NIST256p)
    sig = sk.sign_digest(digest, sigencode=sigencode_string)
    
    # Get public key for verification script
    vk = sk.get_verifying_key()
    pub_key_bytes = b'\x03' + vk.to_string()[:32]  # Compressed public key (33 bytes)
    
    # Build invocation script: PUSHBYTES64 <64-byte signature>
    sig_len = len(sig)
    if sig_len <= 0x4B:  # PUSHBYTES
        invocation_script = bytes([0x0C, sig_len]) + sig  # 0x0C = PUSHBYTES
    elif sig_len <= 0xFF:  # PUSHDATA1
        invocation_script = bytes([0x0D, sig_len]) + sig  # 0x0D = PUSHDATA1
    else:
        invocation_script = bytes([0x0E]) + sig_len.to_bytes(2, 'little') + sig  # 0x0E = PUSHDATA2
    
    # Build verification script for ECDSA
    # Neo N3 standard verification for single signature uses CHECKMULTISIG:
    # PUSH 1 (0x51) PUSH 1 (0x51) PUSHDATA1 (0x0D) <33-byte pubkey> CHECKMULTISIG (0x41)
    # This means: require 1 signature from 1 public key
    verification_script = bytes([0x51, 0x51, 0x0D, 33]) + pub_key_bytes + bytes([0x41])
    
    # Add witness
    tx["witnesses"] = [{
        "invocation": base64.b64encode(invocation_script).decode(),
        "verification": base64.b64encode(verification_script).decode()
    }]
    
    return tx

# -------------------------------------------------------
# MAIN DEPLOY FUNCTION
# -------------------------------------------------------

def deploy_contract():
    """Deploy contract to Neo N3 TestNet using pure RPC"""
    if not ECDSA_AVAILABLE:
        raise ImportError("ecdsa library required. Install with: pip install ecdsa")
    if not BASE58_AVAILABLE:
        raise ImportError("base58 library required. Install with: pip install base58")
    
    if PRIVATE_KEY_WIF is None or PRIVATE_KEY_WIF == "":
        raise Exception("NEO_PRIVATE_KEY missing. Set it in .env file or environment variable.")

    # Check files exist
    nef_path = Path(NEF_PATH)
    manifest_path = Path(MANIFEST_PATH)
    
    if not nef_path.exists():
        raise FileNotFoundError(f"NEF file not found: {NEF_PATH}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {MANIFEST_PATH}")
    
    # Check if NEF is a mock/empty file (24 bytes = just header, no contract code)
    nef_size = nef_path.stat().st_size
    if nef_size <= 24:
        raise ValueError(
            f"NEF file is too small ({nef_size} bytes) - this is just the NEF header with no contract code. "
            "Please export your contract from the UI first. The contract must be compiled properly "
            "before deployment. Even a minimal contract should be at least 50-100 bytes."
        )
    elif nef_size < 50:
        # Very small but might be valid - warn but allow
        print(f"⚠️  Warning: NEF file is very small ({nef_size} bytes). Make sure the contract compiled correctly.")

    print("=" * 60)
    print("Neo N3 RPC Contract Deployment")
    print("=" * 60)
    print(f"🔗 RPC URL: {RPC_URL}")
    print(f"📂 NEF: {NEF_PATH}")
    print(f"📂 Manifest: {MANIFEST_PATH}")
    print()

    # Load NEF & manifest
    print("📖 Loading contract files...")
    with open(nef_path, "rb") as f:
        nef_bytes = f.read()
    with open(manifest_path, "r", encoding='utf-8') as f:
        manifest_json = json.load(f)  # Parse JSON
        manifest_str = json.dumps(manifest_json, separators=(',', ':'))  # Compact JSON (no spaces/newlines)
    
    print(f"   NEF size: {len(nef_bytes)} bytes")
    print(f"   Manifest size: {len(manifest_str)} bytes")
    print()

    # Get signer script hash
    print("🔐 Preparing signer...")
    signer_hash = get_script_hash_from_wif(PRIVATE_KEY_WIF)
    print(f"   Signer: {signer_hash}")
    print()

    # Build deploy script
    print("🔨 Building deployment script...")
    script = build_deploy_script(nef_bytes, manifest_str)
    print(f"   Script size: {len(script)} bytes")
    print()

    # Build transaction with signers
    print("📝 Building transaction...")
    tx = build_transaction(script, signer_hash)
    
    # Try to get fee estimates from RPC using invokescript
    print("   Getting fee estimates from RPC...")
    try:
        script_b64 = base64.b64encode(script).decode()
        invoke_result = rpc_call("invokescript", [script_b64])
        
        if invoke_result and "tx" in invoke_result:
            tx_from_rpc = invoke_result["tx"]
            # Use RPC-provided fees and validUntilBlock
            if "systemFee" in tx_from_rpc:
                tx["systemFee"] = str(tx_from_rpc["systemFee"])
            if "networkFee" in tx_from_rpc:
                tx["networkFee"] = str(tx_from_rpc["networkFee"])
            if "validUntilBlock" in tx_from_rpc:
                tx["validUntilBlock"] = tx_from_rpc["validUntilBlock"]
            if "nonce" in tx_from_rpc:
                tx["nonce"] = tx_from_rpc["nonce"]
            print("   ✅ Got fee estimates from RPC")
        else:
            print("   ⚠️  Could not get fee estimates, using defaults")
    except Exception as e:
        print(f"   ⚠️  Could not get fee estimates: {e}, using defaults")
    
    print("   Transaction structure created")
    print()

    # Sign transaction
    print("✍️  Signing transaction...")
    priv = wif_to_private_key(PRIVATE_KEY_WIF)
    signed_tx = sign_transaction(tx, priv)
    print("   Transaction signed")
    print()

    # Broadcast to Neo RPC
    print("📡 Broadcasting transaction...")
    try:
        # Try sendtransaction first (some RPC implementations accept JSON)
        print("   🔄 Trying sendtransaction (JSON format)...")
        try:
            response = rpc_call("sendtransaction", [signed_tx])
        except Exception as json_error:
            print(f"   ⚠️  sendtransaction failed: {json_error}")
            print("   🔄 Trying sendrawtransaction (hex format)...")
            # Serialize to binary, then encode as Base64
            # Neo N3 sendrawtransaction expects Base64-encoded transaction!
            tx_binary = Neo3TransactionSerializer.serialize_transaction(signed_tx)
            tx_base64 = base64.b64encode(tx_binary).decode('utf-8')
            print(f"   ✅ Transaction serialized: {len(tx_binary)} bytes")
            print(f"   📦 Base64 encoded: {len(tx_base64)} characters")
            
            # Neo N3 sendrawtransaction expects Base64-encoded string
            response = rpc_call("sendrawtransaction", [tx_base64])
        
        print()
        print("=" * 60)
        print("✅ DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        
        # Extract transaction hash from response
        tx_hash = None
        if isinstance(response, dict):
            if "result" in response:
                tx_hash = response["result"]
            elif "txid" in response:
                tx_hash = response["txid"]
            elif "hash" in response:
                tx_hash = response["hash"]
        elif isinstance(response, str):
            tx_hash = response
        
        if tx_hash:
            print(f"Transaction Hash: {tx_hash}")
        else:
            print(f"Transaction Response: {response}")
        
        print()
        print("📝 Full Response:")
        print(json.dumps(response, indent=2))
        print("=" * 60)
        
        # Return structured result for API
        return {
            "tx_hash": tx_hash or str(response),
            "success": True,
            "response": response
        }
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ DEPLOYMENT FAILED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Please check:")
        print("  1. RPC endpoint is accessible")
        print("  2. Private key is correct")
        print("  3. Wallet has sufficient GAS")
        print("  4. Contract files are valid")
        print("=" * 60)
        raise

if __name__ == "__main__":
    deploy_contract()

