"""
Test deployment with a real compiled contract

This script shows how to test deployment once you have a real compiled contract.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from neo_rpc_deploy import deploy_contract, RPC_URL, PRIVATE_KEY_WIF

def main():
    """Test deployment with real contract"""
    print("=" * 60)
    print("Neo N3 Contract Deployment Test")
    print("=" * 60)
    print()
    
    # Check prerequisites
    if not PRIVATE_KEY_WIF:
        print("❌ ERROR: NEO_PRIVATE_KEY not set in .env file")
        print("\nPlease set NEO_PRIVATE_KEY in your .env file:")
        print("  NEO_PRIVATE_KEY=your_wif_private_key_here")
        return
    
    nef_path = Path("generated_contracts/contract.nef")
    manifest_path = Path("generated_contracts/contract.manifest.json")
    
    # Check if files exist
    if not nef_path.exists():
        print(f"❌ ERROR: NEF file not found: {nef_path}")
        print("\nPlease compile a contract first:")
        print("  1. Create a .cs contract file")
        print("  2. Compile it using: nccs Contract.cs")
        print("  3. Copy the .nef file to generated_contracts/contract.nef")
        return
    
    if not manifest_path.exists():
        print(f"❌ ERROR: Manifest file not found: {manifest_path}")
        return
    
    # Check NEF file size (mock files are only 24 bytes)
    nef_size = nef_path.stat().st_size
    if nef_size <= 24:
        print(f"⚠️  WARNING: NEF file is very small ({nef_size} bytes)")
        print("   This might be a mock file. Real contracts are usually > 100 bytes.")
        print("   Deployment may fail with 'Invalid transaction script' error.")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    print(f"✅ NEF file found: {nef_path} ({nef_size} bytes)")
    print(f"✅ Manifest file found: {manifest_path}")
    print(f"✅ RPC URL: {RPC_URL}")
    print()
    
    # Deploy
    try:
        print("Starting deployment...")
        print()
        result = deploy_contract()
        
        if result:
            print()
            print("=" * 60)
            print("✅ DEPLOYMENT SUCCESSFUL!")
            print("=" * 60)
            print(f"Transaction: {result}")
        else:
            print()
            print("=" * 60)
            print("❌ DEPLOYMENT FAILED")
            print("=" * 60)
            print("Check the error messages above for details.")
            
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ DEPLOYMENT ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

