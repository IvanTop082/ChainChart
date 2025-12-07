from pathlib import Path

print("=" * 60)
print("📋 Deployment Files Check")
print("=" * 60)

nef = Path('generated_contracts/contract.nef')
manifest = Path('generated_contracts/contract.manifest.json')

print(f"\n1. contract.nef:")
print(f"   Exists: {nef.exists()}")
if nef.exists():
    print(f"   Size: {nef.stat().st_size} bytes")
    print(f"   Magic: {nef.read_bytes()[:4]}")
    print(f"   Location: {nef.absolute()}")

print(f"\n2. contract.manifest.json:")
print(f"   Exists: {manifest.exists()}")
if manifest.exists():
    print(f"   Size: {manifest.stat().st_size} bytes")
    print(f"   Location: {manifest.absolute()}")

print(f"\n{'✅ Files ready for deployment!' if (nef.exists() and manifest.exists()) else '⚠️  Files missing - need to export contract first'}")
print("=" * 60)


