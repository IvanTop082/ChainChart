"""
Deploy contract using neon-js via Node.js (EXACTLY like NeoNova)

This uses the exact same library (neon-js) that NeoNova uses,
ensuring 100% compatibility and no signing issues.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def deploy_contract_with_neonjs(
    nef_path: str,
    manifest_path: str,
    private_key: Optional[str] = None,
    rpc_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deploy contract using neon-js via Node.js (EXACTLY like NeoNova)
    
    This replicates NeoNova's approach by using the same library (neon-js)
    that NeoNova uses, ensuring identical behavior.
    
    Args:
        nef_path: Path to .nef file
        manifest_path: Path to .manifest.json file
        private_key: WIF private key
        rpc_url: Neo RPC URL
        
    Returns:
        {
            "success": bool,
            "tx_hash": str or None,
            "error": str or None
        }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Check files exist
    nef_file = Path(nef_path)
    manifest_file = Path(manifest_path)
    
    if not nef_file.exists() or not manifest_file.exists():
        return {
            "success": False,
            "tx_hash": None,
            "error": "NEF or manifest file not found"
        }
    
    # Get configuration
    if not rpc_url:
        rpc_url = os.getenv("NEO_RPC_URL", "http://seed3t5.neo.org:20332")
    
    if not private_key:
        # Try multiple ways to get private key
        try:
            from deployment.config import NEO_PRIVATE_KEY
            private_key = NEO_PRIVATE_KEY
        except ImportError:
            private_key = os.getenv("NEO_PRIVATE_KEY")
        
        if not private_key:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                private_key = os.getenv("NEO_PRIVATE_KEY")
            except ImportError:
                pass
    
    if not private_key:
        return {
            "success": False,
            "tx_hash": None,
            "error": "NEO_PRIVATE_KEY required. Set it in .env file or environment variable."
        }
    
    # Check if Node.js is available
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            raise FileNotFoundError("Node.js not found")
        logger.info(f"✅ Node.js available: {result.stdout.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {
            "success": False,
            "tx_hash": None,
            "error": "Node.js is required to use neon-js. Install Node.js from https://nodejs.org/"
        }
    
    # Check if neon-js is installed
    deploy_script = Path(__file__).parent.parent / "deploy_with_neonjs.js"
    if not deploy_script.exists():
        return {
            "success": False,
            "tx_hash": None,
            "error": f"deploy_with_neonjs.js not found at {deploy_script}"
        }
    
    # Check if @cityofzion/neon-js is installed
    try:
        result = subprocess.run(
            ['node', '-e', "require('@cityofzion/neon-js')"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(Path(__file__).parent.parent)
        )
        if result.returncode != 0:
            return {
                "success": False,
                "tx_hash": None,
                "error": "neon-js not installed. Run: npm install @cityofzion/neon-js"
            }
    except Exception as e:
        logger.warning(f"Could not verify neon-js installation: {e}")
        # Continue anyway - let the script handle it
    
    # Run Node.js deployment script
    try:
        logger.info("🚀 Deploying using neon-js (exactly like NeoNova)...")
        logger.info(f"   NEF: {nef_path}")
        logger.info(f"   Manifest: {manifest_path}")
        logger.info(f"   RPC: {rpc_url}")
        
        result = subprocess.run(
            [
                'node',
                str(deploy_script),
                str(nef_file.absolute()),
                str(manifest_file.absolute()),
                private_key,
                rpc_url
            ],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=str(Path(__file__).parent.parent)
        )
        
        # Parse JSON output
        try:
            output = result.stdout.strip()
            # Extract JSON from output (handle any extra logging)
            json_start = output.find('{')
            json_end = output.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                output = output[json_start:json_end]
            
            deploy_result = json.loads(output)
            
            if deploy_result.get("success"):
                logger.info(f"✅ Deployment successful! TX: {deploy_result.get('tx_hash')}")
                return deploy_result
            else:
                error_msg = deploy_result.get("error", "Unknown error")
                logger.error(f"❌ Deployment failed: {error_msg}")
                return deploy_result
                
        except json.JSONDecodeError as json_err:
            # If JSON parsing fails, return error with full output
            error_output = result.stderr or result.stdout
            logger.error(f"❌ Failed to parse deployment result: {json_err}")
            logger.error(f"   Output: {error_output}")
            return {
                "success": False,
                "tx_hash": None,
                "error": f"Failed to parse deployment result. Output: {error_output[:500]}"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "tx_hash": None,
            "error": "Deployment timed out after 2 minutes"
        }
    except Exception as e:
        import traceback
        error_msg = f"Failed to run neon-js deployment: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "tx_hash": None,
            "error": error_msg
        }

