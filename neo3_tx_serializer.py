"""
Lightweight Neo N3 Transaction Serializer
Handles binary serialization of Neo N3 transactions for RPC calls
"""

import struct
import base64
from typing import List, Dict, Any


class Neo3TransactionSerializer:
    """Serialize Neo N3 transactions to binary format"""
    
    # Neo N3 TestNet magic number
    NETWORK_MAGIC = 844378958
    
    @staticmethod
    def serialize_uint8(value: int) -> bytes:
        """Serialize uint8"""
        return struct.pack('<B', value)
    
    @staticmethod
    def serialize_uint16(value: int) -> bytes:
        """Serialize uint16 (little-endian)"""
        return struct.pack('<H', value)
    
    @staticmethod
    def serialize_uint32(value: int) -> bytes:
        """Serialize uint32 (little-endian)"""
        return struct.pack('<I', value)
    
    @staticmethod
    def serialize_uint64(value: int) -> bytes:
        """Serialize uint64 (little-endian)"""
        return struct.pack('<Q', value)
    
    @staticmethod
    def serialize_var_int(value: int) -> bytes:
        """Serialize variable-length integer"""
        if value < 0xFD:
            return struct.pack('<B', value)
        elif value <= 0xFFFF:
            return b'\xFD' + struct.pack('<H', value)
        elif value <= 0xFFFFFFFF:
            return b'\xFE' + struct.pack('<I', value)
        else:
            return b'\xFF' + struct.pack('<Q', value)
    
    @staticmethod
    def serialize_var_bytes(data: bytes) -> bytes:
        """Serialize variable-length bytes"""
        return Neo3TransactionSerializer.serialize_var_int(len(data)) + data
    
    @staticmethod
    def serialize_string(s: str) -> bytes:
        """Serialize string as UTF-8 bytes"""
        data = s.encode('utf-8')
        return Neo3TransactionSerializer.serialize_var_bytes(data)
    
    @staticmethod
    def serialize_signers(signers: List[Dict]) -> bytes:
        """Serialize signers array"""
        result = Neo3TransactionSerializer.serialize_var_int(len(signers))
        for signer in signers:
            # Signer: account (UInt160, 20 bytes, little-endian) + scopes (WitnessScope byte)
            account_hex = signer.get("account", "")
            account_bytes = bytes.fromhex(account_hex)
            if len(account_bytes) != 20:
                raise ValueError(f"Invalid account length: {len(account_bytes)}")
            
            # UInt160 in Neo N3 is stored as 20 bytes in little-endian format
            # The hex string from get_script_hash_from_wif is already in correct order
            # (RIPEMD160 output is already little-endian)
            result += account_bytes
            
            # WitnessScope enum:
            # None = 0x00
            # CalledByEntry = 0x01
            # Global = 0x80
            # CustomContracts = 0x20
            # CustomGroups = 0x40
            scope = signer.get("scopes", "CalledByEntry")
            if isinstance(scope, str):
                if scope == "CalledByEntry":
                    scope_byte = 0x01
                elif scope == "Global":
                    scope_byte = 0x80
                elif scope == "None":
                    scope_byte = 0x00
                else:
                    scope_byte = 0x01  # Default to CalledByEntry
            else:
                scope_byte = int(scope) if isinstance(scope, int) else 0x01
            
            result += Neo3TransactionSerializer.serialize_uint8(scope_byte)
        return result
    
    @staticmethod
    def serialize_attributes(attributes: List) -> bytes:
        """Serialize attributes array"""
        return Neo3TransactionSerializer.serialize_var_int(len(attributes))
    
    @staticmethod
    def serialize_witnesses(witnesses: List[Dict]) -> bytes:
        """Serialize witnesses array"""
        result = Neo3TransactionSerializer.serialize_var_int(len(witnesses))
        for witness in witnesses:
            # Invocation script
            invocation_b64 = witness.get("invocation", "")
            invocation_bytes = base64.b64decode(invocation_b64)
            result += Neo3TransactionSerializer.serialize_var_bytes(invocation_bytes)
            
            # Verification script
            verification_b64 = witness.get("verification", "")
            verification_bytes = base64.b64decode(verification_b64)
            result += Neo3TransactionSerializer.serialize_var_bytes(verification_bytes)
        return result
    
    @classmethod
    def serialize_transaction(cls, tx: Dict[str, Any]) -> bytes:
        """
        Serialize Neo N3 transaction to binary format
        
        Transaction format:
        - version (uint8)
        - nonce (uint32)
        - systemFee (int64 as string, convert to int)
        - networkFee (int64 as string, convert to int)
        - validUntilBlock (uint32)
        - signers (variable)
        - attributes (variable)
        - script (variable bytes)
        - witnesses (variable)
        """
        result = bytearray()
        
        # Version
        result.extend(cls.serialize_uint8(tx.get("version", 0)))
        
        # Nonce
        result.extend(cls.serialize_uint32(tx.get("nonce", 0)))
        
        # SystemFee (int64)
        system_fee = int(tx.get("systemFee", "0"))
        result.extend(cls.serialize_uint64(system_fee))
        
        # NetworkFee (int64)
        network_fee = int(tx.get("networkFee", "0"))
        result.extend(cls.serialize_uint64(network_fee))
        
        # ValidUntilBlock
        result.extend(cls.serialize_uint32(tx.get("validUntilBlock", 0)))
        
        # Signers
        result.extend(cls.serialize_signers(tx.get("signers", [])))
        
        # Attributes
        result.extend(cls.serialize_attributes(tx.get("attributes", [])))
        
        # Script
        script_b64 = tx.get("script", "")
        script_bytes = base64.b64decode(script_b64)
        result.extend(cls.serialize_var_bytes(script_bytes))
        
        # Witnesses (serialize unsigned transaction first, then add witnesses)
        # Note: For signing, we serialize without witnesses, then add them
        witnesses = tx.get("witnesses", [])
        result.extend(cls.serialize_witnesses(witnesses))
        
        return bytes(result)
    
    @classmethod
    def transaction_to_hex(cls, tx: Dict[str, Any]) -> str:
        """Convert transaction to hex string for sendrawtransaction"""
        serialized = cls.serialize_transaction(tx)
        return serialized.hex()
    
    @classmethod
    def serialize_for_signing(cls, tx: Dict[str, Any]) -> bytes:
        """Serialize transaction without witnesses for signing"""
        # Create a copy without witnesses
        tx_copy = tx.copy()
        tx_copy["witnesses"] = []
        return cls.serialize_transaction(tx_copy)

