#!/usr/bin/env python
"""
Verify environment variable setup for Next.js + Python backend
"""
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 60)
print("🔍 Environment Variable Setup Verification")
print("=" * 60)

print("\n📋 Current .env Configuration:")
print("-" * 60)

# Server-side variables (Python backend)
server_vars = {
    'NEO_PRIVATE_KEY': 'Server-side only (Python backend)',
    'NEO_RPC_URL': 'Server-side only (Python backend)',
    'NEO_NETWORK': 'Server-side only (Python backend)'
}

# Client-side variables (Next.js frontend)
client_vars = {
    'NEXT_PUBLIC_API_URL': 'Client-side (Next.js frontend) - API endpoint only',
    'NEXT_PUBLIC_NEO_PRIVATE_KEY': '❌ SHOULD NOT EXIST (security risk!)',
    'NEXT_PUBLIC_NEO_RPC_URL': 'Optional (if needed client-side)'
}

print("\n✅ Server-Side Variables (Python Backend):")
for var, description in server_vars.items():
    value = os.getenv(var)
    if value:
        display = value[:15] + '...' if len(value) > 15 else value
        print(f"  ✅ {var}: {display}")
        print(f"     {description}")
    else:
        print(f"  ❌ {var}: NOT SET")
        print(f"     {description}")

print("\n🌐 Client-Side Variables (Next.js Frontend):")
for var, description in client_vars.items():
    value = os.getenv(var)
    if value:
        if 'PRIVATE_KEY' in var:
            print(f"  ⚠️  {var}: SET (SECURITY RISK!)")
            print(f"     {description}")
        else:
            display = value[:30] + '...' if len(value) > 30 else value
            print(f"  ✅ {var}: {display}")
            print(f"     {description}")
    else:
        if 'PRIVATE_KEY' in var:
            print(f"  ✅ {var}: NOT SET (CORRECT - should not expose private key)")
        else:
            print(f"  ⚠️  {var}: NOT SET")
            print(f"     {description}")

print("\n" + "=" * 60)
print("📝 Recommendations:")
print("=" * 60)
print("""
✅ CORRECT Setup (Current):
   - NEO_PRIVATE_KEY: Server-side only (no prefix)
   - NEO_RPC_URL: Server-side only (no prefix)
   - NEXT_PUBLIC_API_URL: Client-side (API endpoint only)

❌ DO NOT USE:
   - NEXT_PUBLIC_NEO_PRIVATE_KEY: Would expose private key to client!
   - NEXT_PUBLIC_NEO_RPC_URL: Not needed (backend handles RPC)

🔒 Security:
   - Private key stays on server (Python backend)
   - Frontend calls backend API (no direct blockchain access)
   - Backend uses .env file (not exposed to client)
""")

print("=" * 60)



