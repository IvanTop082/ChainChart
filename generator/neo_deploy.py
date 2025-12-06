"""
Neo Contract Deployment Module
Handles deployment of compiled contracts to Neo TestNet
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

# Configure Neo settings at module level (before any Transaction objects are created)
# Note: Settings are configured lazily when needed, not at import time
try:
    from neo3 import settings
    # Don't configure settings at import time - do it when actually deploying
    # This avoids AttributeError if settings.network doesn't exist yet
    NEO3_AVAILABLE = True
except ImportError:
    NEO3_AVAILABLE = False
    pass  # neo3 not available


def deploy_to_testnet(nef_path: str, manifest_path: str, private_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Deploy contract to Neo TestNet via RPC.
    
    Tries multiple approaches:
    1. Direct RPC invokecontract (if available)
    2. neo-mamba TxBuilder (current approach with witness hash issues)
    
    Args:
        nef_path: Path to compiled .nef file
        manifest_path: Path to .manifest.json file
        private_key: Optional private key for signing (WIF format)
        
    Returns:
        Dictionary with deployment result:
        {
            "success": bool,
            "tx_hash": str or None,  # Transaction hash (0x...)
            "error": str or None,
            "mock": bool  # True if mock deployment
        }
    """
    # Try direct RPC approach first (simpler, might work better)
    try:
        from generator.neo_deploy_rpc import deploy_via_rpc_raw
        print("   🔄 Trying direct RPC approach...")
        result = deploy_via_rpc_raw(nef_path, manifest_path, private_key)
        if result.get("success"):
            return result
        else:
            print(f"   ⚠️  Direct RPC approach failed: {result.get('error')}")
            print(f"   🔄 Falling back to neo-mamba approach...")
    except Exception as e:
        print(f"   ⚠️  Direct RPC approach not available: {e}")
        print(f"   🔄 Using neo-mamba approach...")
    
    # Original neo-mamba approach
    try:
        # Read NEF and manifest files
        nef_file = Path(nef_path)
        manifest_file = Path(manifest_path)
        
        if not nef_file.exists() or not manifest_file.exists():
            return {
                "success": False,
                "tx_hash": None,
                "error": "NEF or manifest file not found",
                "mock": False
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
            
            account = None
            # Try to get private key from parameter, config, or environment
            if not private_key or private_key == "":
                try:
                    from deployment.config import NEO_PRIVATE_KEY
                    private_key = NEO_PRIVATE_KEY
                except ImportError:
                    private_key = os.getenv("NEO_PRIVATE_KEY")
            
            if private_key and private_key != "":
                try:
                    # neo-mamba uses Account.from_wif for WIF format private keys
                    account = Account.from_wif(private_key)
                except Exception as e:
                    return {
                        "success": False,
                        "tx_hash": None,
                        "error": f"Invalid private key format: {str(e)}. Make sure NEO_PRIVATE_KEY is in WIF format.",
                        "mock": False
                    }
            else:
                return {
                    "success": False,
                    "tx_hash": None,
                    "error": "NEO_PRIVATE_KEY not found. Set it in .env file or provide it in the request.",
                    "mock": False
                }
            
            # Build deployment transaction using neo3 (neo-mamba)
            try:
                # ContractManagement script hash: 0xfffdc93764dbaddd97c48f252a53ea4643faa3fd
                contract_management_hash = "0xfffdc93764dbaddd97c48f252a53ea4643faa3fd"
                
                # Prepare signers
                signers = []
                if account:
                    # Convert Account to Signer
                    from neo3.network.payloads import verification
                    signer = verification.Signer(
                        account.script_hash,  # script_hash is a property, not a method
                        verification.WitnessScope.CALLED_BY_ENTRY
                    )
                    signers = [signer]
                
                # neo3 uses async API - use asyncio
                import asyncio
                
                async def async_deploy(account_param=None, private_key_param=None):
                    # Use account from parameter or try to load it
                    account = account_param
                    private_key = private_key_param
                    
                    # If account is None, try to load it from private_key
                    if account is None and private_key:
                        try:
                            from neo3.wallet.account import Account
                            account = Account.from_wif(private_key)
                        except Exception as e:
                            raise ValueError(f"Failed to create account from private key: {str(e)}")
                    # Configure Neo N3 TestNet settings for neo-mamba
                    # Transaction class imports 'from neo3 import settings' which gets the Settings instance
                    from neo3 import settings
                    
                    # Transaction class expects settings.settings.network.magic
                    # Create self-reference if it doesn't exist
                    if not hasattr(settings, 'settings'):
                        settings.settings = settings
                    
                    # Network settings for Neo N3 TestNet
                    # Check if network attribute exists before setting
                    if hasattr(settings, 'network'):
                        if hasattr(settings.network, 'magic'):
                            settings.network.magic = 844378958  # Neo N3 TestNet magic number
                        if hasattr(settings.network, 'fee_per_byte'):
                            settings.network.fee_per_byte = 1000
                        if hasattr(settings.network, 'execution_fee_factor'):
                            settings.network.execution_fee_factor = 30
                    
                    # Also set on settings.settings if it exists
                    if hasattr(settings, 'settings'):
                        if hasattr(settings.settings, 'network'):
                            if hasattr(settings.settings.network, 'magic'):
                                settings.settings.network.magic = 844378958
                            if hasattr(settings.settings.network, 'fee_per_byte'):
                                settings.settings.network.fee_per_byte = 1000
                            if hasattr(settings.settings.network, 'execution_fee_factor'):
                                settings.settings.network.execution_fee_factor = 30
                    
                    if hasattr(settings, 'standalone'):
                        settings.standalone = False
                        if hasattr(settings, 'settings'):
                            settings.settings.standalone = False
                    
                    # Protocol settings (only if protocol attribute exists)
                    if hasattr(settings, 'protocol'):
                        if hasattr(settings.protocol, 'max_valid_until_block_increment'):
                            settings.protocol.max_valid_until_block_increment = 2102400  # ~1 month
                        if hasattr(settings.protocol, 'max_transactions_per_block'):
                            settings.protocol.max_transactions_per_block = 512
                        if hasattr(settings.protocol, 'memory_pool_max_transactions'):
                            settings.protocol.memory_pool_max_transactions = 50000
                    
                    print("   ✅ Deployment environment configured.")
                    
                    # Create RPC client within async context
                    rpc = NeoRpc(rpc_url)
                    
                    # Convert NEF bytes to NEF object and manifest dict to ContractManifest object
                    from neo3.contracts import nef, manifest as contract_manifest
                    from neo3.core import types as neo_types
                    from neo3 import vm
                    from neo3.api.helpers import txbuilder
                    from neo3.network.payloads import transaction
                    
                    # Use manifest_content from outer scope
                    manifest_dict = manifest_content
                    
                    # Parse NEF from bytes
                    try:
                        nef_obj = nef.NEF.deserialize_from_bytes(nef_content)
                    except Exception as nef_error:
                        # If NEF parsing fails, use raw bytes (some NEF files might not be fully valid)
                        nef_obj = nef_content
                    
                    # Parse manifest from dict
                    # Ensure manifest has all required fields
                    if not isinstance(manifest_dict, dict):
                        manifest_dict = json.loads(manifest_dict) if isinstance(manifest_dict, str) else manifest_dict
                    
                    # Add missing required fields if not present
                    if "abi" not in manifest_dict:
                        manifest_dict["abi"] = {"methods": [], "events": []}
                    if "groups" not in manifest_dict:
                        manifest_dict["groups"] = []
                    if "features" not in manifest_dict:
                        manifest_dict["features"] = {}
                    if "supportedstandards" not in manifest_dict:
                        manifest_dict["supportedstandards"] = []
                    if "permissions" not in manifest_dict:
                        manifest_dict["permissions"] = []
                    if "trusts" not in manifest_dict:
                        manifest_dict["trusts"] = []
                    
                    try:
                        manifest_obj = contract_manifest.ContractManifest.from_json(manifest_dict)
                    except Exception as manifest_error:
                        # If manifest parsing fails, return error with details
                        raise ValueError(f"Failed to parse manifest: {str(manifest_error)}. Manifest: {manifest_dict}")
                    
                    # ALTERNATIVE APPROACH: Build transaction manually with protocol_magic parameter
                    # This ensures the transaction uses the correct network magic from the start
                    print("   🔄 Using manual transaction construction with protocol_magic...")
                    
                    # Build script to call ContractManagement.deploy
                    contract_mgmt_hash = neo_types.UInt160.from_string("fffdc93764dbaddd97c48f252a53ea4643faa3fd")
                    
                    # Build script using ScriptBuilder
                    sb = vm.ScriptBuilder()
                    # Push manifest (as serialized bytes)
                    manifest_dict = manifest_obj.to_json() if not isinstance(manifest_obj, dict) else manifest_obj
                    import json
                    manifest_bytes = json.dumps(manifest_dict).encode('utf-8')
                    sb.emit_push(manifest_bytes)
                    
                    # Push NEF (as serialized bytes)
                    if isinstance(nef_obj, bytes):
                        nef_bytes = nef_obj
                    else:
                        nef_bytes = nef_obj.to_array()
                    sb.emit_push(nef_bytes)
                    
                    # Call deploy method
                    sb.emit_contract_call(contract_mgmt_hash, "deploy")
                    script = sb.to_array()
                    
                    # Ensure settings are configured BEFORE any transaction operations
                    from neo3 import settings
                    if not hasattr(settings, 'settings'):
                        settings.settings = settings
                    # Set network magic if attributes exist
                    if hasattr(settings, 'network') and hasattr(settings.network, 'magic'):
                        settings.network.magic = 844378958
                    if hasattr(settings, 'settings') and hasattr(settings.settings, 'network') and hasattr(settings.settings.network, 'magic'):
                        settings.settings.network.magic = 844378958
                    
                    # CRITICAL: Set protocol_magic on the settings object itself
                    # Some neo-mamba versions need this for witness hash calculation
                    if hasattr(settings, 'protocol_magic'):
                        settings.protocol_magic = 844378958
                    
                    # Build transaction manually with protocol_magic parameter
                    # This ensures the transaction uses the correct network magic
                    from neo3.network.payloads import transaction as tx_payload
                    from neo3.network.payloads import verification
                    
                    if not account:
                        # Try to load private key from environment/config if not already loaded
                        if not private_key or private_key == "":
                            try:
                                from deployment.config import NEO_PRIVATE_KEY
                                private_key = NEO_PRIVATE_KEY
                            except ImportError:
                                private_key = os.getenv("NEO_PRIVATE_KEY")
                        
                        if private_key and private_key != "":
                            try:
                                account = Account.from_wif(private_key)
                            except Exception as e:
                                raise ValueError(f"Deployment requires a valid private key. Error loading key: {str(e)}")
                        else:
                            raise ValueError(
                                "Deployment requires NEO_PRIVATE_KEY. "
                                "Please set it in .env file (NEO_PRIVATE_KEY=your_wif_key) or provide it in the request."
                            )
                    
                    # Create signer
                    signer = verification.Signer(
                        account.script_hash,
                        verification.WitnessScope.CALLED_BY_ENTRY
                    )
                    
                    # Import signing before using it
                    from neo3.api.helpers import signing
                    from neo3.api.helpers.signing import SigningDetails
                    
                    # Use TxBuilder to calculate fees correctly, then manually construct with protocol_magic
                    if account is None:
                        raise ValueError("Account is None - cannot create TxBuilder. Check that NEO_PRIVATE_KEY is set.")
                    
                    if script is None or len(script) == 0:
                        raise ValueError("Deployment script is empty or None. Check NEF and manifest files.")
                    
                    try:
                        tx_builder = txbuilder.TxBuilder(rpc, script)
                    except Exception as builder_error:
                        raise ValueError(f"Failed to create TxBuilder: {str(builder_error)}")
                    
                    if tx_builder is None:
                        raise ValueError("TxBuilder creation returned None.")
                    
                    try:
                        signing_func = signing.sign_with_account(account)
                    except Exception as sign_func_error:
                        raise ValueError(f"Failed to create signing function: {str(sign_func_error)}")
                    
                    if signing_func is None:
                        raise ValueError("sign_with_account returned None. Check account validity.")
                    
                    try:
                        tx_builder.add_signer(signing_func, signer)
                        await tx_builder.init()
                        await tx_builder.calculate_system_fee()
                        await tx_builder.set_valid_until_block()
                        await tx_builder.calculate_network_fee()
                    except Exception as builder_error:
                        raise ValueError(f"TxBuilder operation failed: {str(builder_error)}")
                    
                    # Get the calculated fees from the builder
                    # Build unsigned to get the transaction with calculated fees
                    # Note: build_unsigned() is not async, it returns a Transaction directly
                    try:
                        unsigned_tx_with_fees = tx_builder.build_unsigned()
                    except Exception as build_error:
                        raise ValueError(f"Failed to build unsigned transaction: {str(build_error)}")
                    
                    if unsigned_tx_with_fees is None:
                        raise ValueError("TxBuilder.build_unsigned() returned None. Check transaction builder configuration.")
                    
                    # Validate all required attributes exist before using them
                    required_attrs = ['version', 'nonce', 'system_fee', 'network_fee', 'valid_until_block', 
                                     'attributes', 'signers', 'script']
                    missing_attrs = [attr for attr in required_attrs if not hasattr(unsigned_tx_with_fees, attr)]
                    if missing_attrs:
                        raise ValueError(f"Transaction missing required attributes: {', '.join(missing_attrs)}")
                    
                    # Create a new transaction with protocol_magic explicitly set
                    # This ensures the witness hash is calculated correctly
                    try:
                        unsigned_tx = tx_payload.Transaction(
                            version=unsigned_tx_with_fees.version,
                            nonce=unsigned_tx_with_fees.nonce,
                            system_fee=unsigned_tx_with_fees.system_fee,
                            network_fee=unsigned_tx_with_fees.network_fee,
                            valid_until_block=unsigned_tx_with_fees.valid_until_block,
                            attributes=unsigned_tx_with_fees.attributes or [],
                            signers=unsigned_tx_with_fees.signers or [],
                            script=unsigned_tx_with_fees.script or b'',
                            witnesses=None,
                            protocol_magic=844378958  # CRITICAL: Explicitly set TestNet magic
                        )
                    except Exception as tx_error:
                        raise ValueError(f"Failed to create Transaction object: {str(tx_error)}")
                    
                    if unsigned_tx is None:
                        raise ValueError("Transaction creation returned None. Check transaction parameters.")
                    
                    # Sign the transaction with the correct network magic
                    if account is None:
                        raise ValueError(
                            "Cannot sign transaction - account is None. "
                            "Check that NEO_PRIVATE_KEY is set correctly in .env file."
                        )
                    
                    if signing_func is None:
                        raise ValueError(
                            "Cannot sign transaction - signing function is None. "
                            "Check that account was created correctly."
                        )
                    
                    signing_details = SigningDetails(network=844378958)  # TestNet magic
                    try:
                        signed_tx = await signing_func(unsigned_tx, signing_details)
                    except Exception as sign_error:
                        raise ValueError(
                            f"Transaction signing failed: {str(sign_error)}. "
                            "Check that the account and private key are valid."
                        )
                    
                    if signed_tx is None:
                        raise ValueError(
                            "Transaction signing failed - signing function returned None. "
                            "Check that the account and private key are valid."
                        )
                    
                    # Validate signed_tx has required attributes
                    if not hasattr(signed_tx, 'hash'):
                        raise ValueError("Signed transaction missing 'hash' attribute. Transaction may not be properly signed.")
                    
                    try:
                        tx_hash_str = str(signed_tx.hash) if signed_tx.hash else None
                        witness_count = len(signed_tx.witnesses) if hasattr(signed_tx, 'witnesses') and signed_tx.witnesses else 0
                        print(f"   📝 Transaction hash: {tx_hash_str}")
                        print(f"   📝 Witness count: {witness_count}")
                    except Exception as print_error:
                        print(f"   ⚠️  Could not print transaction details: {print_error}")
                    
                    # Send transaction
                    try:
                        tx_hash_result = await rpc.send_transaction(signed_tx)
                    except Exception as send_error:
                        raise ValueError(f"Failed to send transaction to RPC: {str(send_error)}")
                    
                    # Extract transaction hash
                    tx_hash = None
                    if tx_hash_result is None:
                        raise ValueError("RPC send_transaction returned None. Check RPC connection and transaction validity.")
                    
                    if isinstance(tx_hash_result, dict):
                        tx_hash = tx_hash_result.get("hash") or tx_hash_result.get("txid") or tx_hash_result.get("result")
                    elif hasattr(tx_hash_result, "hash"):
                        tx_hash = str(tx_hash_result.hash) if tx_hash_result.hash else None
                    elif hasattr(tx_hash_result, "txid"):
                        tx_hash = str(tx_hash_result.txid) if tx_hash_result.txid else None
                    else:
                        tx_hash = str(tx_hash_result) if tx_hash_result else None
                    
                    if not tx_hash:
                        raise ValueError(f"Could not extract transaction hash from RPC response: {tx_hash_result}")
                    
                    return {"tx_hash": tx_hash, "result": tx_hash_result}
                
                # Run async deployment
                # Check if event loop is already running
                try:
                    loop = asyncio.get_running_loop()
                    # If loop exists, we need to use a different approach
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, async_deploy(account, private_key))
                        deploy_result = future.result()
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run
                    deploy_result = asyncio.run(async_deploy(account, private_key))
                
                # Extract transaction hash from result
                tx_hash = None
                if deploy_result is None:
                    raise ValueError("Deployment result is None. Check deployment process.")
                
                if isinstance(deploy_result, dict):
                    tx_hash = deploy_result.get("txid") or deploy_result.get("tx_hash") or deploy_result.get("hash") or deploy_result.get("result")
                elif hasattr(deploy_result, "txid"):
                    tx_hash = str(deploy_result.txid) if deploy_result.txid else None
                elif hasattr(deploy_result, "hash"):
                    tx_hash = str(deploy_result.hash) if deploy_result.hash else None
                elif hasattr(deploy_result, "tx_hash"):
                    tx_hash = str(deploy_result.tx_hash) if deploy_result.tx_hash else None
                else:
                    tx_hash = str(deploy_result) if deploy_result else None
                
                if not tx_hash:
                    raise ValueError(f"Could not extract transaction hash from deployment result: {deploy_result}")
                
                if tx_hash:
                    # Ensure 0x prefix
                    if not tx_hash.startswith("0x"):
                        tx_hash = "0x" + tx_hash
                    
                    return {
                        "success": True,
                        "tx_hash": tx_hash,
                        "error": None,
                        "mock": False
                    }
                else:
                    # Result doesn't contain tx hash - might need to send transaction
                    # Try to extract from result structure
                    return {
                        "success": False,
                        "tx_hash": None,
                        "error": f"Deployment result does not contain transaction hash. Result structure: {type(deploy_result)}, Available keys: {dir(deploy_result) if hasattr(deploy_result, '__dict__') else 'N/A'}",
                        "mock": False
                    }
                    
            except (TypeError, AttributeError) as api_error:
                # API might have different signature - return helpful error with traceback
                import traceback
                tb = traceback.format_exc()
                return {
                    "success": False,
                    "tx_hash": None,
                    "error": f"neo3 API error: {str(api_error)}. Check neo3 API documentation for correct method signature.\nTraceback: {tb}",
                    "mock": False
                }
                
            except Exception as deploy_error:
                # Log the actual error for debugging
                error_msg = str(deploy_error)
                return {
                    "success": False,
                    "tx_hash": None,
                    "error": f"Deployment failed: {error_msg}",
                    "mock": False
                }
                
        except ImportError as import_error:
            # neo3 not available, return mock
            # Log the import error for debugging
            import_error_msg = str(import_error)
            pass
        
        # Mock deployment if neo3 (neo-mamba) not available or deployment failed
        nef_hash = hashlib.sha256(nef_content).hexdigest()
        mock_txid = f"0x{nef_hash[:64]}"
        
        return {
            "success": False,
            "tx_hash": mock_txid,
            "error": "neo3 (neo-mamba) library not available or deployment failed. TODO: Install neo-mamba for real deployment: pip install neo-mamba. If installed, check deployment error above.",
            "mock": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "tx_hash": None,
            "error": f"Deployment failed: {str(e)}",
            "mock": False
        }

