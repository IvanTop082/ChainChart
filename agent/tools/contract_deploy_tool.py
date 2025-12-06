"""
ContractDeployTool - Deploy NEF + manifest to Neo N3 TestNet
"""

import json
from typing import Dict, Any, Optional
from spoon_ai.tools.base import BaseTool

try:
    # neo-mamba package provides neo3 module
    from neo3.api import NeoRpcClient
    from neo3.wallet.account import Account
    NeoRpc = NeoRpcClient  # Alias for compatibility
    NEO_MAMBA_AVAILABLE = True
except ImportError:
    NEO_MAMBA_AVAILABLE = False


class ContractDeployTool(BaseTool):
    """
    Deploy NEF + manifest.json to Neo N3 TestNet.
    Uses neo-mamba RPC library for deployment.
    """
    
    name: str = "deploy_contract"
    description: str = "Deploy NEF + manifest.json to Neo N3 TestNet"
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "nef": {
                "type": "string",
                "description": "NEF file content (base64 or hex)"
            },
            "manifest": {
                "type": "string",
                "description": "Manifest JSON string"
            },
            "wallet_private_key": {
                "type": "string",
                "description": "Private key for signing deployment (optional)"
            },
            "rpc_url": {
                "type": "string",
                "description": "Neo RPC endpoint URL (defaults to testnet)"
            }
        },
        "required": ["nef", "manifest"]
    }
    
    async def execute(
        self,
        nef: str,
        manifest: str,
        wallet_private_key: Optional[str] = None,
        rpc_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy contract to Neo N3 TestNet.
        
        Args:
            nef: NEF file content (base64 encoded)
            manifest: Manifest JSON string
            wallet_private_key: Optional private key for signing
            rpc_url: Optional RPC URL (defaults to testnet)
            
        Returns:
            {
                "txid": "0x123...",  # Transaction hash
                "success": bool,
                "error": str (if failed)
            }
        """
        # Default RPC URL to Neo TestNet
        if not rpc_url:
            rpc_url = "http://seed3t5.neo.org:20332"
        
        try:
            if NEO_MAMBA_AVAILABLE:
                return await self._deploy_with_neo_mamba(nef, manifest, wallet_private_key, rpc_url)
            else:
                # Return mock deployment if neo-mamba not available
                return self._generate_mock_deployment(nef, manifest)
                
        except Exception as e:
            return {
                "txid": None,
                "success": False,
                "error": f"Deployment failed: {str(e)}",
                "mock": True
            }
    
    async def _deploy_with_neo_mamba(
        self,
        nef: str,
        manifest: str,
        private_key: Optional[str],
        rpc_url: str
    ) -> Dict[str, Any]:
        """Deploy using neo-mamba library"""
        try:
            import base64
            
            # Parse manifest
            manifest_obj = json.loads(manifest)
            
            # Decode NEF (assuming base64)
            try:
                nef_bytes = base64.b64decode(nef)
            except:
                # Try hex if base64 fails
                nef_bytes = bytes.fromhex(nef)
            
            # Create RPC client
            rpc = NeoRpc(rpc_url)
            
            # Create account if private key provided
            account = None
            if private_key:
                account = Account.from_private_key(private_key)
            
            # Build deployment transaction
            # Note: This is a simplified version - actual deployment may require more setup
            deploy_result = await rpc.invoke_function(
                "ContractManagement",
                "deploy",
                [
                    nef_bytes.hex(),
                    manifest_obj
                ],
                signers=[account] if account else []
            )
            
            if deploy_result and "txid" in deploy_result:
                return {
                    "txid": deploy_result["txid"],
                    "success": True,
                    "mock": False
                }
            else:
                return {
                    "txid": None,
                    "success": False,
                    "error": "Deployment transaction failed",
                    "mock": False
                }
                
        except Exception as e:
            return {
                "txid": None,
                "success": False,
                "error": f"neo-mamba deployment error: {str(e)}",
                "mock": True
            }
    
    def _generate_mock_deployment(self, nef: str, manifest: str) -> Dict[str, Any]:
        """Generate mock deployment result when RPC is not available"""
        import hashlib
        
        # Generate mock transaction ID from NEF content
        nef_hash = hashlib.sha256(nef.encode() if isinstance(nef, str) else nef).hexdigest()
        mock_txid = f"0x{nef_hash[:64]}"
        
        return {
            "txid": mock_txid,
            "success": False,
            "error": "neo-mamba library not available. TODO: Install neo-mamba and configure Neo RPC connection for real deployment.",
            "mock": True
        }

