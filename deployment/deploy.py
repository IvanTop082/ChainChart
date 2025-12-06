#!/usr/bin/env python
"""
Deploy Neo N3 Smart Contract to TestNet

This script deploys a compiled Neo contract (.nef + manifest.json) to Neo N3 TestNet.

Uses pure RPC deployment (no neo-mamba, no CLI, no GUI).

Requirements:
    pip install ecdsa base58 requests

Environment Variables:
    NEO_PRIVATE_KEY - Private key for signing the deployment transaction (WIF format)
    NEO_RPC_URL - Neo RPC endpoint (default: http://seed3t5.neo.org:20332)

Usage:
    python deployment/deploy.py [nef_path] [manifest_path]

If paths are not provided, defaults to:
    - generated_contracts/contract.nef
    - generated_contracts/contract.manifest.json
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Try neo-mamba (provides neo3 module)
    # Only import what we actually use
    from neo3.api import NeoRpcClient
    from neo3.core.types import UInt160, UInt256
    from neo3.wallet.account import Account
    # Create aliases for compatibility with existing code
    RPCClient = NeoRpcClient
    NEO3_AVAILABLE = True
except ImportError as e:
    NEO3_AVAILABLE = False
    print("❌ ERROR: neo3 (neo-mamba) is not installed")
    print(f"   Import error: {e}")
    print("\nInstall it with:")
    print("  pip install neo-mamba")
    print("\nOr if using pip3:")
    print("  pip3 install neo-mamba")
    print("\nNote: neo-mamba provides the neo3 module used for deployment")
    sys.exit(1)

from deployment.config import (
    NEO_RPC_URL, 
    NEO_PRIVATE_KEY, 
    save_contract_info,
    CONTRACT_INFO_PATH
)

# Print neo3-python version at runtime
try:
    import neo3
    # Try multiple ways to get version
    neo3_version = getattr(neo3, '__version__', None)
    if not neo3_version:
        try:
            import neo_mamba
            neo3_version = getattr(neo_mamba, '__version__', None)
        except:
            pass
    if not neo3_version:
        try:
            import pkg_resources
            neo3_version = pkg_resources.get_distribution('neo-mamba').version
        except:
            pass
    if not neo3_version:
        neo3_version = 'unknown'
    print(f"📦 neo3-python version: {neo3_version}")
except ImportError:
    print("⚠️  Warning: Could not detect neo3-python version")


def load_nef_and_manifest(nef_path: Optional[str] = None, manifest_path: Optional[str] = None) -> tuple:
    """Load NEF and manifest files"""
    if not nef_path:
        nef_path = Path(__file__).parent.parent / "generated" / "compiled" / "Contract.nef"
    else:
        nef_path = Path(nef_path)
    
    if not manifest_path:
        manifest_path = Path(__file__).parent.parent / "generated" / "compiled" / "Contract.manifest.json"
    else:
        manifest_path = Path(manifest_path)
    
    # Validate files exist
    if not nef_path.exists():
        raise FileNotFoundError(f"NEF file not found: {nef_path}")
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    # Read files
    nef_data = nef_path.read_bytes()
    manifest_data = manifest_path.read_text(encoding='utf-8')
    
    return nef_data, manifest_data, manifest_path


async def deploy_contract(nef_data: bytes, manifest_data: str, private_key: str, rpc_url: str) -> dict:
    """
    Deploy contract to Neo N3 TestNet
    
    Args:
        nef_data: Compiled NEF file bytes
        manifest_data: Manifest JSON string
        private_key: Private key for signing (WIF format)
        rpc_url: Neo RPC endpoint URL
        
    Returns:
        Dictionary with tx_hash and contract_hash
    """
    import json
    
    # Parse manifest
    manifest = json.loads(manifest_data)
    
    # Connect to RPC
    print(f"🔗 Connecting to Neo RPC: {rpc_url}")
    rpc = RPCClient(rpc_url)
    
    # Create wallet from private key
    print("🔐 Loading wallet from private key...")
    try:
        # neo-mamba uses Account.from_wif for WIF format private keys
        account = Account.from_wif(private_key)
    except Exception as e:
        raise ValueError(f"Invalid private key format: {e}")
    
    print(f"   Address: {account.address}")
    
    # Check GAS balance (async)
    print("💰 Checking GAS balance...")
    try:
        import asyncio
        async def check_balance():
            balances = await rpc.get_nep17_balances(account.address)
            gas_balance = 0
            for balance in balances:
                if balance.get("asset_symbol") == "GAS":
                    gas_balance = float(balance.get("amount", 0))
                    break
            return gas_balance
        
        gas_balance = asyncio.run(check_balance())
        print(f"   GAS balance: {gas_balance}")
        
        if gas_balance < 10:  # Minimum GAS for deployment
            raise ValueError(f"Insufficient GAS. Need at least 10 GAS, have {gas_balance}")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not check GAS balance: {e}")
        print(f"   Continuing anyway...")
    
    # Deploy contract using the existing deployment function
    print("\n📤 Deploying contract to TestNet...")
    
    # Configure Neo N3 TestNet settings for neo-mamba
    try:
        # Transaction class imports 'from neo3 import settings' which gets the Settings instance
        from neo3 import settings
        
        # Network settings for Neo N3 TestNet
        settings.network.magic = 844378958  # Neo N3 TestNet magic number
        
        # Set fee settings if they exist
        if hasattr(settings.network, 'fee_per_byte'):
            settings.network.fee_per_byte = 1000
        if hasattr(settings.network, 'execution_fee_factor'):
            settings.network.execution_fee_factor = 30
        if hasattr(settings, 'standalone'):
            settings.standalone = False
        
        # Protocol settings (only if protocol attribute exists)
        if hasattr(settings, 'protocol'):
            if hasattr(settings.protocol, 'max_valid_until_block_increment'):
                settings.protocol.max_valid_until_block_increment = 2102400  # ~1 month
            if hasattr(settings.protocol, 'max_transactions_per_block'):
                settings.protocol.max_transactions_per_block = 512
            if hasattr(settings.protocol, 'memory_pool_max_transactions'):
                settings.protocol.memory_pool_max_transactions = 50000
        
        print("   ✅ Deployment environment configured.")
    except ImportError:
        print("   ⚠️  Warning: Could not import neo3.settings, using defaults")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not configure settings: {e}")
    
    try:
        # Use the existing deployment function from generator/neo_deploy.py
        # which has more complete implementation
        from generator.neo_deploy import deploy_to_testnet
        
        # Save NEF and manifest to temp files for deployment function
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_nef = Path(temp_dir) / "contract.nef"
            temp_manifest = Path(temp_dir) / "contract.manifest.json"
            
            temp_nef.write_bytes(nef_data)
            temp_manifest.write_text(manifest_data, encoding='utf-8')
            
            # Call deployment function (synchronous)
            result = deploy_to_testnet(
                str(temp_nef),
                str(temp_manifest),
                private_key
            )
            
            if result.get("success"):
                tx_hash = result.get("tx_hash")
                
                # Calculate contract hash from NEF and account
                # Contract hash = Hash160(script_hash + nef_checksum + manifest_hash)
                from neo3.contracts import Contract, NEF
                from neo3.core.types import UInt160
                import hashlib
                
                # Parse NEF to get checksum
                try:
                    nef_obj = NEF.deserialize_from_bytes(nef_data)
                    nef_checksum = nef_obj.checksum
                except:
                    # Fallback: use hash of NEF
                    nef_checksum = hashlib.sha256(nef_data).digest()[:4]
                
                # Calculate manifest hash
                manifest_hash = hashlib.sha256(manifest_data.encode()).digest()
                
                # Contract hash calculation (simplified)
                # In reality, it's: Hash160(script_hash || nef_checksum || manifest_hash)
                script_hash = account.script_hash()
                contract_hash_bytes = hashlib.sha256(
                    script_hash.to_array() + nef_checksum + manifest_hash
                ).digest()[:20]
                contract_hash = UInt160(contract_hash_bytes)
                
                return {
                    "tx_hash": tx_hash,
                    "contract_hash": f"0x{contract_hash.to_str()}",
                    "success": True
                }
            else:
                raise Exception(result.get("error", "Deployment failed"))
        
    except Exception as e:
        # If RPC deploy fails, try alternative method
        print(f"   ⚠️  Standard deploy failed: {e}")
        print(f"   Trying alternative deployment method...")
        
        # Alternative: Use invokecontract RPC with deploy script
        # This requires constructing the deployment script manually
        raise NotImplementedError(
            f"Deployment failed: {e}\n\n"
            "Please ensure:\n"
            "1. neo3-python is correctly installed\n"
            "2. RPC endpoint is accessible\n"
            "3. Private key has sufficient GAS\n"
            "4. Contract is valid\n\n"
            "For manual deployment, use Neo GUI or neo-cli."
        )


def main():
    """Main deployment function - uses pure RPC deployment"""
    print("=" * 60)
    print("Neo N3 TestNet Contract Deployment (Pure RPC)")
    print("=" * 60)
    
    # Check for private key
    if not NEO_PRIVATE_KEY:
        print("\n❌ ERROR: NEO_PRIVATE_KEY environment variable not set")
        print("\nSet it with:")
        print("  export NEO_PRIVATE_KEY=your_private_key_here")
        print("\nOr on Windows:")
        print("  $env:NEO_PRIVATE_KEY='your_private_key_here'")
        print("\nOr create a .env file with:")
        print("  NEO_PRIVATE_KEY=your_private_key_here")
        sys.exit(1)
    
    # Get file paths from command line or use defaults
    nef_path = sys.argv[1] if len(sys.argv) > 1 else None
    manifest_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Use new RPC deployment script
    try:
        # Import the new RPC deployment module
        from neo_rpc_deploy import deploy_contract
        
        # Temporarily set paths if provided
        if nef_path or manifest_path:
            import neo_rpc_deploy
            if nef_path:
                neo_rpc_deploy.NEF_PATH = nef_path
            if manifest_path:
                neo_rpc_deploy.MANIFEST_PATH = manifest_path
        
        # Deploy using pure RPC
        result = deploy_contract()
        
        print(f"\n✅ Deployment successful!")
        print(f"   Transaction: {result}")
        
        return 0
        
    except ImportError as e:
        print(f"\n❌ ERROR: Missing required library: {e}")
        print(f"\nInstall required packages:")
        print(f"  pip install ecdsa base58 requests")
        return 1
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\nPlease ensure the contract is compiled first:")
        print(f"  python deployment/compile.py")
        print(f"\nOr export from the UI using 'Export Contract' button")
        return 1
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import json
    sys.exit(main())

