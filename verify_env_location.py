#!/usr/bin/env python
"""
Verify .env file location and accessibility
"""
from pathlib import Path
from dotenv import load_dotenv
import os

print("=" * 60)
print("🔍 .env File Location Verification")
print("=" * 60)

# Get project root (where this script is located)
project_root = Path(__file__).parent.absolute()
env_file = project_root / '.env'
api_server = project_root / 'api_server.py'

print(f"\n📂 Project Structure:")
print(f"  Project root: {project_root}")
print(f"  .env file:    {env_file}")
print(f"  api_server.py: {api_server}")

print(f"\n✅ File Checks:")
print(f"  .env exists: {env_file.exists()}")
print(f"  .env is file: {env_file.is_file() if env_file.exists() else False}")
print(f"  api_server.py exists: {api_server.exists()}")
print(f"  Same directory: {env_file.parent == api_server.parent}")

if env_file.exists():
    print(f"  .env size: {env_file.stat().st_size} bytes")
    print(f"  .env readable: {os.access(env_file, os.R_OK)}")
    
    # Test loading
    print(f"\n🔑 Environment Variable Loading Test:")
    load_dotenv(env_file)  # Explicitly load from this location
    
    vars_to_check = [
        'NEO_PRIVATE_KEY',
        'NEO_RPC_URL',
        'NEO_NETWORK'
    ]
    
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            display = value[:10] + '...' if len(value) > 10 else value
            print(f"  ✅ {var}: {display}")
        else:
            print(f"  ❌ {var}: NOT SET")
    
    print(f"\n✅ .env file is in the correct location!")
    print(f"   Backend can load it from: {env_file}")
else:
    print(f"\n❌ .env file NOT FOUND at: {env_file}")
    print(f"   Please create it in the project root directory.")

print("=" * 60)

