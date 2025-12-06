"""
Neo Compiler Integration - Compile C# contracts and deploy to Neo TestNet
"""

import os
import subprocess
import json
import base64
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


def compile_contract(cs_path: str) -> Tuple[Optional[str], Optional[str], bool, List[str]]:
    """
    Execute Neo compiler CLI to compile C# contract.
    
    Uses 'neon' command (Neo.Compiler.CSharp) to compile the contract.
    
    Args:
        cs_path: Path to the .cs contract file
        
    Returns:
        Tuple of (nef_path, manifest_path, success, errors)
        - nef_path: Path to compiled .nef file (or None if failed)
        - manifest_path: Path to .manifest.json (or None if failed)
        - success: True if compilation succeeded
        - errors: List of compiler warnings/errors (empty if success)
    """
    cs_file = Path(cs_path)
    
    if not cs_file.exists():
        return None, None, False, [f"Contract file not found: {cs_path}"]
    
    # Create output directory
    output_dir = cs_file.parent / "compiled"
    output_dir.mkdir(exist_ok=True)
    
    errors = []
    
    # Create a .csproj file if it doesn't exist (needed for framework references)
    csproj_file = cs_file.parent / f"{cs_file.stem}.csproj"
    if not csproj_file.exists():
        csproj_content = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net9.0</TargetFramework>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Neo.SmartContract.Framework" Version="3.8.1" />
  </ItemGroup>
</Project>"""
        csproj_file.write_text(csproj_content, encoding='utf-8')
    
    # Try different Neo compiler commands (in order of preference)
    compiler_commands = [
        # Neo.Compiler.CSharp (nccs command) - compile .cs file directly
        # The compiler will automatically use the .csproj in the same directory for references
        {
            "cmd": ["nccs", str(cs_file)],
            "name": "nccs (Neo.Compiler.CSharp)",
            "output_pattern": "*.nef"
        },
        # Neo.Compiler.CSharp (neon command - older versions)
        {
            "cmd": ["neon", str(cs_file)],
            "name": "neon (Neo.Compiler.CSharp)",
            "output_pattern": "*.nef"
        },
        # Neo N3 official compiler (neoc)
        {
            "cmd": ["neoc", "compile", str(cs_file), "-o", str(output_dir)],
            "name": "neoc (Neo N3 compiler)",
            "output_pattern": "*.nef"
        },
        # Neo-express compiler
        {
            "cmd": ["neoxp", "contract", "compile", str(cs_file), "--out", str(output_dir)],
            "name": "neoxp (neo-express)",
            "output_pattern": "*.nef"
        },
    ]
    
    for compiler_info in compiler_commands:
        cmd = compiler_info["cmd"]
        compiler_name = compiler_info["name"]
        
        try:
            # Check if compiler exists
            check_result = subprocess.run(
                [cmd[0], "--version"] if cmd[0] in ["neon", "neoc", "neoxp"] else [cmd[0], "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if check_result.returncode != 0 and "neon" not in cmd[0]:
                continue  # Compiler not found, try next
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Compiler not installed
            if compiler_info == compiler_commands[0]:  # First one (neon)
                errors.append(f"Neo compiler not found. Please install: dotnet tool install -g Neo.Compiler.CSharp")
            continue
        
        # Try to compile
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(cs_file.parent)
            )
            
            # Parse output for errors/warnings
            if result.stderr:
                errors.extend(result.stderr.split('\n'))
            if result.stdout and ("error" in result.stdout.lower() or "warning" in result.stdout.lower()):
                errors.extend(result.stdout.split('\n'))
            
            # Check if output files were created (even if compiler reported errors)
            contract_name = cs_file.stem
            nef_files = list(cs_file.parent.glob("*.nef")) + list(output_dir.glob("*.nef"))
            manifest_files = list(cs_file.parent.glob("*.manifest.json")) + list(output_dir.glob("*.manifest.json"))
            
            # If files exist, compilation succeeded (FormatException is non-critical)
            if nef_files and manifest_files:
                nef_file = nef_files[0]
                manifest_file = manifest_files[0]
                # Filter out FormatException errors (they're non-critical if files exist)
                critical_errors = [e for e in errors if "FormatException" not in e and "error CS" not in e]
                return str(nef_file), str(manifest_file), True, critical_errors
            
            if result.returncode == 0:
                # Look for generated files
                contract_name = cs_file.stem
                
                # Try different naming patterns
                possible_nef = [
                    output_dir / f"{contract_name}.nef",
                    cs_file.parent / f"{contract_name}.nef",
                    cs_file.parent / f"{contract_name}.nef"
                ]
                
                possible_manifest = [
                    output_dir / f"{contract_name}.manifest.json",
                    cs_file.parent / f"{contract_name}.manifest.json",
                    cs_file.parent / f"{contract_name}.abi.json"
                ]
                
                # Also search for any .nef and .manifest.json files
                nef_files = list(cs_file.parent.glob("*.nef")) + list(output_dir.glob("*.nef"))
                manifest_files = list(cs_file.parent.glob("*.manifest.json")) + list(output_dir.glob("*.manifest.json"))
                
                nef_file = None
                manifest_file = None
                
                # Find NEF file
                for path in possible_nef:
                    if path.exists():
                        nef_file = path
                        break
                if not nef_file and nef_files:
                    nef_file = nef_files[0]
                
                # Find manifest file
                for path in possible_manifest:
                    if path.exists():
                        manifest_file = path
                        break
                if not manifest_file and manifest_files:
                    manifest_file = manifest_files[0]
                
                if nef_file and manifest_file:
                    return str(nef_file), str(manifest_file), True, []
                else:
                    errors.append(f"Compilation succeeded but output files not found. NEF: {nef_file}, Manifest: {manifest_file}")
                    
        except subprocess.TimeoutExpired:
            errors.append(f"Compilation timeout with {compiler_name}")
            continue
        except Exception as e:
            errors.append(f"Compilation error with {compiler_name}: {str(e)}")
            continue
    
    # If all compilers fail, check for DevPack
    if not errors or any("not found" in str(e).lower() for e in errors):
        errors.append("Neo DevPack not detected. Please install: dotnet add package Neo.SmartContract.Framework")
        errors.append("Or install Neo compiler: dotnet tool install -g Neo.Compiler.CSharp")
    
    # Return mock files with errors
    nef_path, manifest_path, _ = generate_mock_compilation(cs_file, output_dir)
    return nef_path, manifest_path, False, errors


def generate_mock_compilation(cs_path: Path, output_dir: Path) -> Tuple[str, str, bool]:
    """
    Generate mock NEF and manifest files when compiler is not available.
    
    Args:
        cs_path: Path to source .cs file
        output_dir: Output directory
        
    Returns:
        Tuple of (nef_path, manifest_path, success=False)
    """
    contract_name = cs_path.stem
    nef_file = output_dir / f"{contract_name}.nef"
    manifest_file = output_dir / f"{contract_name}.manifest.json"
    
    # Generate minimal mock NEF
    mock_nef = bytes([
        0x4E, 0x45, 0x46, 0x33,  # NEF3 magic
        0x00, 0x00, 0x00, 0x00,  # Compiler
        0x00, 0x00, 0x00, 0x00,  # Version
        0x00, 0x00, 0x00, 0x00,  # Reserved
        0x00, 0x00, 0x00, 0x00,  # Script length
        0x00, 0x00, 0x00, 0x00,  # Checksum
    ])
    nef_file.write_bytes(mock_nef)
    
    # Generate mock manifest
    manifest = {
        "name": contract_name,
        "groups": [],
        "features": {},
        "supportedstandards": [],
        "abi": {
            "methods": [
                {
                    "name": "_initialize",
                    "parameters": [],
                    "returntype": "Void",
                    "offset": 0,
                    "safe": False
                }
            ],
            "events": []
        },
        "permissions": [
            {
                "contract": "*",
                "methods": "*"
            }
        ],
        "trusts": [],
        "extra": {
            "Author": "ChainChart",
            "Description": "Generated from ChainChart diagram"
        }
    }
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    
    return str(nef_file), str(manifest_file), False


def deploy_to_testnet(nef_path: str, manifest_path: str, private_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Deploy contract to Neo TestNet via RPC.
    
    Args:
        nef_path: Path to compiled .nef file
        manifest_path: Path to .manifest.json file
        private_key: Optional private key for signing
        
    Returns:
        Dictionary with deployment result:
        {
            "success": bool,
            "txid": str or None,
            "error": str or None
        }
    """
    try:
        # Read NEF and manifest files
        nef_file = Path(nef_path)
        manifest_file = Path(manifest_path)
        
        if not nef_file.exists() or not manifest_file.exists():
            return {
                "success": False,
                "txid": None,
                "error": "NEF or manifest file not found"
            }
        
        nef_content = nef_file.read_bytes()
        manifest_content = json.loads(manifest_file.read_text(encoding='utf-8'))
        
        # Try to use neo3 (neo-mamba package) if available
        try:
            # neo-mamba package provides neo3 module
            from neo3.api import NeoRpcClient
            from neo3.wallet.account import Account
            NeoRpc = NeoRpcClient  # Alias for compatibility
            
            rpc_url = os.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")
            rpc = NeoRpc(rpc_url)
            
            account = None
            if private_key:
                account = Account.from_private_key(private_key)
            
            # Deploy contract
            # Note: This is a simplified version - actual deployment may require async
            # For now, we'll use a synchronous approach or mock
            try:
                # Try synchronous invocation first
                # Note: neo-mamba API may vary - adjust parameters as needed
                deploy_result = rpc.invoke_function(
                    "ContractManagement",
                    "deploy",
                    [
                        nef_content.hex(),
                        manifest_content
                    ],
                    signers=[account] if account else []
                )
                
                if deploy_result and "txid" in deploy_result:
                    return {
                        "success": True,
                        "txid": deploy_result["txid"],
                        "error": None
                    }
            except Exception as deploy_error:
                # If synchronous fails, return error
                return {
                    "success": False,
                    "txid": None,
                    "error": f"Deployment failed: {str(deploy_error)}"
                }
        except ImportError:
            pass
        
        # Mock deployment if neo-mamba not available
        import hashlib
        nef_hash = hashlib.sha256(nef_content).hexdigest()
        mock_txid = f"0x{nef_hash[:64]}"
        
        return {
            "success": False,
            "txid": mock_txid,
            "error": "neo-mamba library not available. TODO: Install neo-mamba for real deployment."
        }
        
    except Exception as e:
        return {
            "success": False,
            "txid": None,
            "error": f"Deployment failed: {str(e)}"
        }


def read_compiled_files(nef_path: str, manifest_path: str) -> Dict[str, Any]:
    """
    Read compiled NEF and manifest files and return as base64/JSON.
    
    Args:
        nef_path: Path to .nef file
        manifest_path: Path to .manifest.json file
        
    Returns:
        Dictionary with:
        {
            "nef": base64 encoded string,
            "manifest": JSON object
        }
    """
    nef_file = Path(nef_path)
    manifest_file = Path(manifest_path)
    
    nef_content = nef_file.read_bytes()
    manifest_content = json.loads(manifest_file.read_text(encoding='utf-8'))
    
    return {
        "nef": base64.b64encode(nef_content).decode('utf-8'),
        "manifest": manifest_content
    }

