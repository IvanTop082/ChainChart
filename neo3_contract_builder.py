"""
Minimal NeoVM ScriptBuilder for contract deployment
No external dependencies - pure Python
"""

class ScriptBuilder:
    def __init__(self):
        self.buf = bytearray()

    def emit_push(self, data):
        """Push data onto the stack"""
        if isinstance(data, str):
            data = data.encode()
        elif isinstance(data, bytes):
            pass
        else:
            raise TypeError(f"Cannot push {type(data)}")

        length = len(data)
        
        # Handle different push opcodes based on length
        if length == 0:
            self.buf.append(0x00)  # PUSH0
        elif length <= 0x4B:  # PUSHBYTES
            self.buf.append(0x0C)  # PUSHBYTES opcode
            self.buf.append(length)
            self.buf.extend(data)
        elif length <= 0xFF:
            self.buf.append(0x0D)  # PUSHDATA1
            self.buf.append(length)
            self.buf.extend(data)
        elif length <= 0xFFFF:
            self.buf.append(0x0E)  # PUSHDATA2
            length_bytes = length.to_bytes(2, "little")
            self.buf.extend(length_bytes)
            self.buf.extend(data)
        else:
            self.buf.append(0x0F)  # PUSHDATA4
            self.buf.extend(length.to_bytes(4, "little"))
            self.buf.extend(data)

    def emit_syscall(self, name: str):
        """
        Emit a syscall instruction
        
        Neo N3 syscall format: SYSCALL (0x68) + syscall hash (4 bytes, little-endian)
        The syscall hash is the first 4 bytes of SHA256(interop service name)
        """
        self.buf.append(0x68)  # SYSCALL opcode
        
        # Calculate syscall hash
        # Neo N3 uses interop service names, and the hash is first 4 bytes of SHA256
        import hashlib
        # For System.Contract.Create, the interop service name is "System.Contract.Create"
        name_hash = hashlib.sha256(name.encode('utf-8')).digest()[:4]
        # Hash is stored in little-endian
        self.buf.extend(name_hash)
    
    def emit_contract_call(self, contract_hash_bytes: bytes, method: str):
        """
        Emit a contract call using CALLT opcode
        
        Neo N3 CALLT format:
        - CALLT (0xE8)
        - Contract hash (20 bytes, UInt160, little-endian)
        - Method name (null-terminated UTF-8 string)
        """
        self.buf.append(0xE8)  # CALLT opcode
        
        # Contract hash must be 20 bytes, little-endian (UInt160)
        if len(contract_hash_bytes) != 20:
            raise ValueError(f"Contract hash must be 20 bytes, got {len(contract_hash_bytes)}")
        
        self.buf.extend(contract_hash_bytes)
        
        # Method name as null-terminated UTF-8 string
        method_bytes = method.encode('utf-8') + b'\x00'
        self.buf.extend(method_bytes)

    def to_array(self) -> bytes:
        """Return the compiled script as bytes"""
        return bytes(self.buf)

