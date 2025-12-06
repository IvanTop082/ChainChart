#!/usr/bin/env python
"""
Direct deployment script for SimpleCounter contract
Bypasses UI and exports - deploys directly to TestNet
"""

import sys
from pathlib import Path
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def deploy_simplecounter():
    """Deploy the SimpleCounter contract directly"""
    
    print("=" * 60)
    print("🚀 Direct Deployment: SimpleCounter Contract")
    print("=" * 60)
    print()
    
    # Step 1: Find the compiled contract
    nef_source = Path("bin/sc/SimpleCounter.nef")
    manifest_source = Path("bin/sc/SimpleCounter.manifest.json")
    
    if not nef_source.exists():
        print("❌ ERROR: SimpleCounter.nef not found!")
        print(f"   Expected: {nef_source.absolute()}")
        print()
        print("   Please compile it first:")
        print("   nccs simplecounter.cs")
        return False
    
    if not manifest_source.exists():
        print("❌ ERROR: SimpleCounter.manifest.json not found!")
        print(f"   Expected: {manifest_source.absolute()}")
        return False
    
    nef_size = nef_source.stat().st_size
    print(f"✅ Found compiled contract:")
    print(f"   NEF: {nef_size} bytes")
    print(f"   Manifest: {manifest_source.stat().st_size} bytes")
    print()
    
    if nef_size <= 24:
        print("❌ ERROR: NEF is too small (mock/empty contract)")
        print("   Please compile the contract properly first")
        return False
    
    # Step 2: Copy to generated_contracts/ for deployment
    generated_contracts_dir = Path("generated_contracts")
    generated_contracts_dir.mkdir(exist_ok=True)
    
    target_nef = generated_contracts_dir / "contract.nef"
    target_manifest = generated_contracts_dir / "contract.manifest.json"
    
    print("📋 Copying files to generated_contracts/...")
    shutil.copy2(nef_source, target_nef)
    shutil.copy2(manifest_source, target_manifest)
    print(f"   ✅ Copied to: {target_nef}")
    print(f"   ✅ Copied to: {target_manifest}")
    print()
    
    # Step 3: Deploy using pure RPC
    print("🚀 Deploying to Neo TestNet...")
    print()
    
    try:
        from neo_rpc_deploy import deploy_contract
        
        result = deploy_contract()
        
        if isinstance(result, dict):
            if result.get("tx_hash"):
                print()
                print("=" * 60)
                print("✅ DEPLOYMENT SUCCESSFUL!")
                print("=" * 60)
                print(f"Transaction Hash: {result['tx_hash']}")
                print()
                print("🔍 View on TestNet:")
                print(f"   https://dora.coz.io/neotracker/testnet/tx/{result['tx_hash']}")
                return True
            else:
                print("❌ Deployment failed - no transaction hash")
                print(f"   Result: {result}")
                return False
        elif isinstance(result, str):
            print()
            print("=" * 60)
            print("✅ DEPLOYMENT SUCCESSFUL!")
            print("=" * 60)
            print(f"Transaction Hash: {result}")
            print()
            print("🔍 View on TestNet:")
            print(f"   https://dora.coz.io/neotracker/testnet/tx/{result}")
            return True
        else:
            print("❌ Unexpected result format")
            print(f"   Result: {result}")
            return False
            
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ DEPLOYMENT FAILED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        
        # Provide helpful error messages
        error_str = str(e).lower()
        if "nef file is too small" in error_str or "24 bytes" in error_str:
            print("💡 Solution: The contract needs to be compiled properly")
            print("   Run: nccs simplecounter.cs")
        elif "ecdsa" in error_str or "base58" in error_str:
            print("💡 Solution: Install missing dependencies")
            print("   Run: pip install ecdsa base58")
        elif "private key" in error_str or "NEO_PRIVATE_KEY" in error_str:
            print("💡 Solution: Set your private key in .env file")
            print("   Add: NEO_PRIVATE_KEY=your_wif_key_here")
        elif "not found" in error_str:
            print("💡 Solution: Make sure the contract files exist")
            print("   Check: bin/sc/SimpleCounter.nef")
        
        return False


if __name__ == "__main__":
    success = deploy_simplecounter()
    sys.exit(0 if success else 1)

