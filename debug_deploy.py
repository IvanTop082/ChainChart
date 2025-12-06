"""
Debug script for testing deployment step by step
Run this to see detailed logs of what's happening during deployment
"""

import os
import sys
import logging
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env file from {env_path}")
    else:
        # Try loading from current directory
        load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Will try to use environment variables directly...")

# Setup logging to see all debug info
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Test deployment with detailed logging"""
    
    # Check for required files
    nef_path = Path("generated_contracts/contract.nef")
    manifest_path = Path("generated_contracts/contract.manifest.json")
    
    if not nef_path.exists():
        print(f"❌ NEF file not found: {nef_path}")
        print("   Please export a contract first from the UI")
        return
    
    if not manifest_path.exists():
        print(f"❌ Manifest file not found: {manifest_path}")
        print("   Please export a contract first from the UI")
        return
    
    # Check for private key (try multiple sources)
    private_key = os.getenv("NEO_PRIVATE_KEY")
    
    # If not found, try loading from deployment.config
    if not private_key:
        try:
            from deployment.config import NEO_PRIVATE_KEY
            private_key = NEO_PRIVATE_KEY
            print("✅ Loaded NEO_PRIVATE_KEY from deployment.config")
        except ImportError:
            pass
    
    if not private_key:
        print("❌ NEO_PRIVATE_KEY not found")
        print("   Options:")
        print("   1. Set it in .env file: NEO_PRIVATE_KEY=your_wif_key")
        print("   2. Set it in deployment/config.py: NEO_PRIVATE_KEY = 'your_wif_key'")
        print("   3. Export it: export NEO_PRIVATE_KEY=your_wif_key_here")
        return
    
    print("=" * 60)
    print("🚀 Starting deployment debug test...")
    print("=" * 60)
    print()
    
    # Import and call deployment function
    try:
        from generator.neonova_deploy import deploy_contract_neonova_style
        
        rpc_url = os.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")
        
        print(f"📁 NEF file: {nef_path}")
        print(f"📁 Manifest file: {manifest_path}")
        print(f"🌐 RPC URL: {rpc_url}")
        print(f"🔑 Private key: {'*' * (len(private_key) - 10)}{private_key[-10:]}")
        print()
        
        result = deploy_contract_neonova_style(
            str(nef_path),
            str(manifest_path),
            private_key,
            rpc_url
        )
        
        print()
        print("=" * 60)
        print("📊 Deployment Result:")
        print("=" * 60)
        print(f"Success: {result.get('success')}")
        print(f"TX Hash: {result.get('tx_hash')}")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        print("=" * 60)
        
        if result.get('success'):
            print()
            print("✅ Deployment successful!")
            if result.get('tx_hash'):
                print(f"   Transaction hash: {result.get('tx_hash')}")
                print(f"   View on explorer: https://testnet.neotube.org/transaction/{result.get('tx_hash')}")
        else:
            print()
            print("❌ Deployment failed!")
            if result.get('error'):
                print(f"   Error: {result.get('error')}")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Exception occurred:")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("=" * 60)

if __name__ == "__main__":
    main()

