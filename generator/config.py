"""
Neo Blockchain Configuration

This module provides centralized configuration for Neo RPC URL and contract hash.
All blockchain-related tools should import from this module.

Environment Variables:
    NEO_RPC_URL - Neo RPC endpoint URL (default: http://seed3t5.neo.org:20332)
    NEO_CONTRACT_HASH - Deployed contract hash (default: local dev hash)
"""

import os

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables directly

# RPC Configuration
NEO_RPC_URL = os.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")

# Contract Hash Configuration
NEO_CONTRACT_HASH = os.getenv(
    "NEO_CONTRACT_HASH",
    "0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab"  # default for local dev
)

def get_rpc_url() -> str:
    """Get the Neo RPC URL"""
    return NEO_RPC_URL

def get_contract_hash() -> str:
    """Get the deployed contract hash"""
    return NEO_CONTRACT_HASH

def has_contract_hash() -> bool:
    """Check if contract hash is available and valid"""
    if not NEO_CONTRACT_HASH:
        return False
    # Basic validation: should be hex string (with or without 0x prefix)
    hash_str = NEO_CONTRACT_HASH.replace("0x", "").replace("0X", "")
    return len(hash_str) == 40 and all(c in '0123456789abcdefABCDEF' for c in hash_str)



