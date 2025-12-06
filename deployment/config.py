"""
Deployment Configuration - Contract Hash Management

This module manages the deployed contract hash and RPC configuration.
"""

import os
import json
from pathlib import Path
from typing import Optional

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables directly

# Path to contract info file
CONTRACT_INFO_PATH = Path(__file__).parent / "contract_info.json"

# RPC Configuration
NEO_RPC_URL = os.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")
NEO_PRIVATE_KEY = os.getenv("NEO_PRIVATE_KEY", "")

# Contract hash (loaded from contract_info.json)
CONTRACT_HASH: Optional[str] = None


def load_contract_info() -> dict:
    """Load contract information from contract_info.json"""
    if CONTRACT_INFO_PATH.exists():
        try:
            with open(CONTRACT_INFO_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load contract_info.json: {e}")
    return {}


def save_contract_info(contract_hash: str, tx_hash: str):
    """Save contract information to contract_info.json"""
    info = {
        "contract_hash": contract_hash,
        "tx_hash": tx_hash,
        "rpc_url": NEO_RPC_URL,
        "network": "testnet"
    }
    
    with open(CONTRACT_INFO_PATH, 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"✅ Contract info saved to {CONTRACT_INFO_PATH}")


def get_contract_hash() -> Optional[str]:
    """Get the deployed contract hash"""
    global CONTRACT_HASH
    
    if CONTRACT_HASH:
        return CONTRACT_HASH
    
    info = load_contract_info()
    CONTRACT_HASH = info.get("contract_hash")
    return CONTRACT_HASH


def has_contract_hash() -> bool:
    """Check if contract hash is available"""
    return get_contract_hash() is not None


# Load contract hash on import
CONTRACT_HASH = get_contract_hash()

