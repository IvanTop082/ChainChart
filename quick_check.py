from dotenv import load_dotenv
import os

load_dotenv()

print("\n🔍 All NEO Environment Variables:")
print("=" * 60)
vars_to_check = ['NEO_PRIVATE_KEY', 'NEO_RPC_URL', 'NEO_NETWORK']
for var in vars_to_check:
    value = os.getenv(var)
    if value:
        display = value[:20] + '...' if len(value) > 20 else value
        print(f'✅ {var}: {display}')
    else:
        print(f'❌ {var}: NOT SET')
print("=" * 60)

