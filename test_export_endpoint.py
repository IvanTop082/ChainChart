"""
Test script for POST /export-contract API endpoint
"""

import requests
import json

API_BASE = "http://localhost:8000"

# Test diagram - State -> Function -> Event
TEST_DIAGRAM = {
    "nodes": [
        {
            "id": "1",
            "type": "state",
            "label": "balance",
            "value": "",
            "position": {"x": 0, "y": 0},
            "metadata": {
                "label": "balance",
                "dataType": "BigInteger",
                "visibility": "public"
            }
        },
        {
            "id": "2",
            "type": "function",
            "label": "transfer",
            "value": "",
            "position": {"x": 0, "y": 0},
            "metadata": {
                "name": "transfer",
                "params": "UInt160 to, BigInteger amount",
                "visibility": "public",
                "payable": False
            }
        },
        {
            "id": "3",
            "type": "event",
            "label": "Transfer",
            "value": "",
            "position": {"x": 0, "y": 0},
            "metadata": {
                "name": "Transfer",
                "params": "UInt160 from, UInt160 to, BigInteger amount"
            }
        }
    ],
    "edges": [
        {"from": "1", "to": "2"},
        {"from": "2", "to": "3"}
    ]
}


def test_export_endpoint():
    """Test the /export-contract endpoint"""
    print("\n" + "="*60)
    print("TESTING POST /export-contract")
    print("="*60)
    
    url = f"{API_BASE}/export-contract"
    
    try:
        print("\n📤 Sending request...")
        response = requests.post(url, json=TEST_DIAGRAM, timeout=30)
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Success: {result.get('success')}")
            
            # Check contract
            contract = result.get("contract", "")
            if contract:
                print(f"✅ Contract generated: {len(contract)} chars")
                print(f"   Preview: {contract[:200]}...")
            else:
                print("❌ No contract in response")
            
            # Check manifest
            manifest = result.get("manifest", {})
            if manifest:
                print(f"✅ Manifest generated")
                print(f"   Name: {manifest.get('name', 'N/A')}")
                print(f"   Methods: {len(manifest.get('abi', {}).get('methods', []))}")
                print(f"   Events: {len(manifest.get('abi', {}).get('events', []))}")
            else:
                print("❌ No manifest in response")
            
            # Check NEF
            nef = result.get("nef", "")
            if nef:
                print(f"✅ NEF generated: {len(nef)} chars (base64)")
            else:
                print("❌ No NEF in response")
            
            # Check for errors
            if result.get("error"):
                print(f"\n⚠️  Warning: {result['error']}")
            
            # Save to files for inspection
            if contract:
                with open("generated_contract.cs", "w", encoding="utf-8") as f:
                    f.write(contract)
                print(f"\n💾 Contract saved to: generated_contract.cs")
            
            if manifest:
                with open("generated_manifest.json", "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)
                print(f"💾 Manifest saved to: generated_manifest.json")
            
            if nef:
                import base64
                nef_bytes = base64.b64decode(nef)
                with open("generated_contract.nef", "wb") as f:
                    f.write(nef_bytes)
                print(f"💾 NEF saved to: generated_contract.nef")
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Details: {error_data}")
            except:
                print(f"   Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed!")
        print("   Make sure the API server is running:")
        print("   python api_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_export_endpoint()
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

