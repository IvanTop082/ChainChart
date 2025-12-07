# test_env.py
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("🔍 Environment Variables Check")
print("=" * 60)

# Check all possible variable names
vars_to_check = [
    'NEO_PRIVATE_KEY',
    'PRIVATE_KEY',
    'NEOFS_PRIVATE_KEY_WIF',
    'NEO_RPC_URL',
    'NEO_NETWORK'
]

for var in vars_to_check:
    value = os.getenv(var)
    if value:
        # Show first 10 chars only for security
        display = value[:10] + '...' if len(value) > 10 else value
        print(f"✅ {var}: {display}")
    else:
        print(f"❌ {var}: NOT SET")

print("=" * 60)


