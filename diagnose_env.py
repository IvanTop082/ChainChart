#!/usr/bin/env python
"""
Quick Fix Checklist - Environment Variable Diagnostics
Run this script to diagnose .env file issues
"""
from pathlib import Path
import os
import sys

print("=" * 60)
print("🔍 Quick Fix Checklist - Environment Variable Diagnostics")
print("=" * 60)

# 1. Check if .env exists
print("\n1️⃣  Check if .env exists:")
print("-" * 60)
env_file = Path('.env')
if env_file.exists():
    print(f"   ✅ .env file found: {env_file.absolute()}")
    print(f"   Size: {env_file.stat().st_size} bytes")
    print(f"   Readable: {os.access(env_file, os.R_OK)}")
else:
    print(f"   ❌ .env file NOT FOUND at: {env_file.absolute()}")
    print("   💡 Create it in the project root directory")
    sys.exit(1)

# 2. Check .env content (be careful not to expose keys!)
print("\n2️⃣  Check .env content (first 20 chars only for security):")
print("-" * 60)
try:
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        neo_vars = [line for line in lines if 'NEO' in line.upper() and not line.strip().startswith('#')]
        
        if neo_vars:
            print("   Found NEO-related variables:")
            for line in neo_vars:
                # Show variable name and first 20 chars of value
                if '=' in line:
                    var_name, var_value = line.split('=', 1)
                    var_name = var_name.strip()
                    var_value = var_value.strip()
                    if var_value:
                        display = var_value[:20] + '...' if len(var_value) > 20 else var_value
                        print(f"   ✅ {var_name}: {display}")
                    else:
                        print(f"   ⚠️  {var_name}: (empty value)")
        else:
            print("   ❌ No NEO-related variables found in .env")
except Exception as e:
    print(f"   ❌ Error reading .env file: {e}")

# 3. Test loading in Python
print("\n3️⃣  Test loading in Python:")
print("-" * 60)
try:
    from dotenv import load_dotenv
    print("   ✅ python-dotenv is installed")
    
    load_dotenv()
    private_key = os.getenv('NEO_PRIVATE_KEY')
    
    if private_key:
        print(f"   ✅ NEO_PRIVATE_KEY loaded: {private_key[:10]}...")
        print(f"   Length: {len(private_key)} characters")
        print(f"   Format: {'WIF (starts with K/L)' if private_key[0] in 'KL' else 'Other'}")
    else:
        print("   ❌ NEO_PRIVATE_KEY NOT SET in environment")
        print("   💡 Add to .env file: NEO_PRIVATE_KEY=your_wif_key_here")
    
    # Check other variables
    rpc_url = os.getenv('NEO_RPC_URL')
    network = os.getenv('NEO_NETWORK')
    
    print(f"\n   Other variables:")
    print(f"   NEO_RPC_URL: {rpc_url if rpc_url else 'NOT SET'}")
    print(f"   NEO_NETWORK: {network if network else 'NOT SET'}")
    
except ImportError:
    print("   ❌ python-dotenv is NOT installed")
    print("   💡 Install with: pip install python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Error loading .env: {e}")

# 4. Check python-dotenv installation
print("\n4️⃣  Check python-dotenv installation:")
print("-" * 60)
try:
    import dotenv
    print(f"   ✅ python-dotenv installed")
    print(f"   Version: {dotenv.__version__ if hasattr(dotenv, '__version__') else 'unknown'}")
except ImportError:
    print("   ❌ python-dotenv is NOT installed")
    print("   💡 Install with: pip install python-dotenv")
    print("   Or: python -m pip install python-dotenv")

# 5. Verify project structure
print("\n5️⃣  Verify project structure:")
print("-" * 60)
root = Path('.')
api_server = root / 'api_server.py'
generated_contracts = root / 'generated_contracts'

print(f"   Project root: {root.absolute()}")
print(f"   api_server.py: {'✅ Found' if api_server.exists() else '❌ Not found'}")
print(f"   generated_contracts/: {'✅ Found' if generated_contracts.exists() else '❌ Not found'}")
print(f"   .env: {'✅ Found' if env_file.exists() else '❌ Not found'}")
print(f"   Same directory: {'✅ Yes' if env_file.parent == api_server.parent else '❌ No'}")

print("\n" + "=" * 60)
print("✅ Diagnostic Complete!")
print("=" * 60)
print("\n💡 If issues found:")
print("   1. Create .env file in project root if missing")
print("   2. Install python-dotenv: pip install python-dotenv")
print("   3. Verify NEO_PRIVATE_KEY is set in .env")
print("   4. Restart backend server after changing .env")
print("=" * 60)



