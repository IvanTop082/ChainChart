#!/usr/bin/env python
"""
Compile C# Neo Smart Contract to NEF + Manifest

This script compiles a C# contract file to Neo N3 executable format (.nef) and manifest.

Usage:
    python deployment/compile.py [contract_path]

If contract_path is not provided, defaults to generated/Contract.cs

Requirements:
    - Neo.Compiler.CSharp (neon command) OR
    - Neo N3 compiler (neoc command) OR
    - Neo Express (neoxp command)

Installation:
    # Option 1: Install Neo.Compiler.CSharp (Recommended)
    dotnet tool install -g Neo.Compiler.CSharp
    
    # Option 2: Install Neo N3 compiler
    # Download from: https://github.com/neo-project/neo-compiler
    
    # Option 3: Install Neo Express
    dotnet tool install -g Neo.Express
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.neo_compiler import compile_contract


def main():
    """Main compilation function"""
    # Determine contract path
    if len(sys.argv) > 1:
        contract_path = Path(sys.argv[1])
    else:
        # Default to generated/Contract.cs
        contract_path = Path(__file__).parent.parent / "generated" / "Contract.cs"
    
    if not contract_path.exists():
        print(f"❌ ERROR: Contract file not found: {contract_path}")
        print(f"\nPlease ensure the contract file exists, or provide a path:")
        print(f"  python deployment/compile.py <path_to_contract.cs>")
        sys.exit(1)
    
    print(f"Compiling contract: {contract_path}")
    print("=" * 60)
    
    # Compile contract
    nef_path, manifest_path, success, errors = compile_contract(str(contract_path))
    
    if success and nef_path and manifest_path:
        print(f"\n✅ Compilation successful!")
        print(f"   NEF file: {nef_path}")
        print(f"   Manifest: {manifest_path}")
        
        # Verify files exist
        if Path(nef_path).exists() and Path(manifest_path).exists():
            nef_size = Path(nef_path).stat().st_size
            print(f"   NEF size: {nef_size} bytes")
            
            # Show manifest summary
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    print(f"   Contract name: {manifest.get('name', 'N/A')}")
                    print(f"   Methods: {len(manifest.get('abi', {}).get('methods', []))}")
            except:
                pass
            
            print(f"\n✅ Ready for deployment!")
            print(f"   Run: python deployment/deploy.py")
            return 0
        else:
            print(f"❌ ERROR: Compiled files not found at expected locations")
            return 1
    else:
        print(f"\n❌ Compilation failed!")
        if errors:
            print(f"\nErrors/Warnings:")
            for error in errors:
                if error.strip():
                    print(f"  - {error}")
        
        print(f"\n📖 Installation Instructions:")
        print(f"=" * 60)
        print(f"\nTo install Neo compiler, choose one of the following:")
        print(f"\n1. Neo.Compiler.CSharp (Recommended):")
        print(f"   dotnet tool install -g Neo.Compiler.CSharp")
        print(f"   # Then use: neon <contract.cs>")
        print(f"\n2. Neo N3 Compiler:")
        print(f"   # Download from: https://github.com/neo-project/neo-compiler")
        print(f"   # Or use: neoc compile <contract.cs>")
        print(f"\n3. Neo Express:")
        print(f"   dotnet tool install -g Neo.Express")
        print(f"   # Then use: neoxp contract compile <contract.cs>")
        print(f"\nAfter installation, run this script again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

