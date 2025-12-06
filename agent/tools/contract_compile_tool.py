"""
ContractCompileTool - Compile C# Neo contract to NEF + manifest.json
"""

import os
import subprocess
import json
import base64
import tempfile
from pathlib import Path
from spoon_ai.tools.base import BaseTool
from typing import Dict, Any


class ContractCompileTool(BaseTool):
    """
    Compile a Neo C# contract into NEF and manifest.
    Uses Neo compiler (neoc or neo-express) to compile contract.
    """
    
    name: str = "compile_contract"
    description: str = "Compile a Neo C# contract into NEF and manifest"
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "contract_text": {
                "type": "string",
                "description": "C# contract source code"
            }
        },
        "required": ["contract_text"]
    }
    
    async def execute(self, contract_text: str) -> Dict[str, Any]:
        """
        Compile C# contract to NEF and manifest.
        
        Args:
            contract_text: C# source code for Neo contract
            
        Returns:
            {
                "nef": <base64 or hex content>,
                "manifest": <json manifest string>,
                "success": bool,
                "error": str (if failed)
            }
        """
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            contract_file = temp_path / "generated_contract.cs"
            output_dir = temp_path / "compiled"
            output_dir.mkdir(exist_ok=True)
            
            # Write contract to file
            contract_file.write_text(contract_text, encoding='utf-8')
            
            # Try to compile using Neo compiler
            try:
                # Try neoc compiler first (Neo N3 official compiler)
                result = await self._try_compile_neoc(contract_file, output_dir)
                if result["success"]:
                    return result
                
                # Try neo-express compiler
                result = await self._try_compile_neoxp(contract_file, output_dir)
                if result["success"]:
                    return result
                
                # If both fail, return mock data with TODO
                return self._generate_mock_compilation(contract_file)
                
            except Exception as e:
                # Return mock data on any error
                return {
                    "nef": self._mock_nef_hex(),
                    "manifest": self._mock_manifest_json(),
                    "success": False,
                    "error": f"Compilation failed: {str(e)}. Returning mock data. TODO: Install Neo compiler (neoc or neo-express).",
                    "mock": True
                }
    
    async def _try_compile_neoc(self, contract_file: Path, output_dir: Path) -> Dict[str, Any]:
        """Try compiling with neoc (Neo N3 official compiler)"""
        try:
            # Check if neoc is available
            result = subprocess.run(
                ["neoc", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {"success": False}
            
            # Compile contract
            compile_result = subprocess.run(
                ["neoc", "compile", str(contract_file), "-o", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return {"success": False, "error": compile_result.stderr}
            
            # Find generated NEF and manifest files
            nef_file = output_dir / f"{contract_file.stem}.nef"
            manifest_file = output_dir / f"{contract_file.stem}.manifest.json"
            
            if nef_file.exists() and manifest_file.exists():
                nef_content = nef_file.read_bytes()
                manifest_content = manifest_file.read_text(encoding='utf-8')
                
                return {
                    "nef": base64.b64encode(nef_content).decode('utf-8'),
                    "manifest": manifest_content,
                    "success": True,
                    "mock": False
                }
            
            return {"success": False}
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return {"success": False}
    
    async def _try_compile_neoxp(self, contract_file: Path, output_dir: Path) -> Dict[str, Any]:
        """Try compiling with neo-express compiler"""
        try:
            # Check if neo-express is available
            result = subprocess.run(
                ["neoxp", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {"success": False}
            
            # Compile using neo-express
            compile_result = subprocess.run(
                ["neoxp", "contract", "compile", str(contract_file), "--out", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return {"success": False, "error": compile_result.stderr}
            
            # Find generated files
            nef_file = output_dir / f"{contract_file.stem}.nef"
            manifest_file = output_dir / f"{contract_file.stem}.manifest.json"
            
            if nef_file.exists() and manifest_file.exists():
                nef_content = nef_file.read_bytes()
                manifest_content = manifest_file.read_text(encoding='utf-8')
                
                return {
                    "nef": base64.b64encode(nef_content).decode('utf-8'),
                    "manifest": manifest_content,
                    "success": True,
                    "mock": False
                }
            
            return {"success": False}
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return {"success": False}
    
    def _generate_mock_compilation(self, contract_file: Path) -> Dict[str, Any]:
        """Generate mock compilation result when compiler is not available"""
        return {
            "nef": self._mock_nef_hex(),
            "manifest": self._mock_manifest_json(),
            "success": False,
            "error": "Neo compiler (neoc or neo-express) not found. TODO: Install Neo compiler to enable real compilation.",
            "mock": True
        }
    
    def _mock_nef_hex(self) -> str:
        """Generate mock NEF file content (base64 encoded)"""
        # Mock NEF file structure (minimal valid NEF)
        mock_nef = bytes([
            0x4E, 0x45, 0x46, 0x33,  # NEF3 magic
            0x00, 0x00, 0x00, 0x00,  # Compiler
            0x00, 0x00, 0x00, 0x00,  # Version
            0x00, 0x00, 0x00, 0x00,  # Reserved
            0x00, 0x00, 0x00, 0x00,  # Script length
            # Minimal script
            0x00, 0x00, 0x00, 0x00,  # Checksum
        ])
        return base64.b64encode(mock_nef).decode('utf-8')
    
    def _mock_manifest_json(self) -> str:
        """Generate mock manifest JSON"""
        manifest = {
            "name": "ChainChartContract",
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
        return json.dumps(manifest, indent=2)

