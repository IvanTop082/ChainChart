#!/usr/bin/env python
"""Quick deployment test script"""
import requests
import json
import os

nef_path = 'generated_contracts/contract.nef'
manifest_path = 'generated_contracts/contract.manifest.json'

print("🚀 Testing Deployment via API...")
print(f"   NEF exists: {os.path.exists(nef_path)}")
print(f"   Manifest exists: {os.path.exists(manifest_path)}")
print()

try:
    # Send empty body - API will read from disk
    response = requests.post('http://localhost:8000/deploy-contract', json={}, timeout=30)
    print(f"✅ Status: {response.status_code}")
    print()
    print("📋 Response:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        result = response.json()
        if result.get('tx_hash'):
            print()
            print("=" * 60)
            print("✅ DEPLOYMENT SUCCESSFUL!")
            print("=" * 60)
            print(f"Transaction Hash: {result['tx_hash']}")
            print()
            print("🔍 View on TestNet Explorer:")
            print(f"   https://dora.coz.io/neotracker/testnet/tx/{result['tx_hash']}")
            if result.get('contract_hash'):
                print(f"   Contract Hash: {result['contract_hash']}")
                print(f"   https://dora.coz.io/neotracker/testnet/contract/{result['contract_hash']}")
        else:
            print("⚠️  Deployment may have failed - no tx_hash in response")
except requests.exceptions.ConnectionError:
    print("❌ Error: Cannot connect to API server")
    print("   Make sure the API server is running:")
    print("   python api_server.py")
except Exception as e:
    print(f"❌ Error: {e}")

