#!/usr/bin/env python3
"""Recompile the current Contract.cs to update manifest and NEF"""

from pathlib import Path
from generator.neo_compiler import compile_contract
import shutil
import json

# Remove old compiled files
old_nef = Path("generated_contracts/contract.nef")
old_manifest = Path("generated_contracts/contract.manifest.json")

if old_nef.exists():
    old_nef.unlink()
    print(f"Removed old NEF: {old_nef}")

if old_manifest.exists():
    old_manifest.unlink()
    print(f"Removed old manifest: {old_manifest}")

# Compile the current Contract.cs
cs_file = Path("generated_contracts/Contract.cs")
print(f"\nCompiling: {cs_file}")
print(f"File exists: {cs_file.exists()}")

if not cs_file.exists():
    print("ERROR: Contract.cs not found!")
    exit(1)

nef_path, manifest_path, success, errors = compile_contract(str(cs_file))

print(f"\nCompilation success: {success}")
print(f"NEF path: {nef_path}")
print(f"Manifest path: {manifest_path}")

if errors:
    print(f"Errors: {errors}")

if success and nef_path and manifest_path:
    # Copy to the expected location
    target_nef = Path("generated_contracts/contract.nef")
    target_manifest = Path("generated_contracts/contract.manifest.json")
    
    if Path(nef_path).exists():
        shutil.copy2(nef_path, target_nef)
        print(f"\n✅ Copied NEF to {target_nef}")
        print(f"   Size: {target_nef.stat().st_size} bytes")
    
    if Path(manifest_path).exists():
        shutil.copy2(manifest_path, target_manifest)
        print(f"✅ Copied manifest to {target_manifest}")
        
        # Show manifest info
        manifest_data = json.loads(Path(manifest_path).read_text())
        print(f"\n📋 Manifest Info:")
        print(f"   Name: {manifest_data.get('name', 'N/A')}")
        methods = manifest_data.get('abi', {}).get('methods', [])
        print(f"   Methods: {[m['name'] for m in methods]}")
else:
    print("\n❌ Compilation failed or files not found")

