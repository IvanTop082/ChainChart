"""
Debug script to analyze Neo N3 transaction structure
"""

import struct
import base64

def analyze_transaction_hex(tx_hex: str):
    """Analyze a transaction hex string"""
    data = bytes.fromhex(tx_hex)
    
    print("=" * 60)
    print("Transaction Analysis")
    print("=" * 60)
    print(f"Total size: {len(data)} bytes")
    print()
    
    offset = 0
    
    # Version (1 byte)
    version = data[offset]
    print(f"Version: {version} (offset {offset})")
    offset += 1
    
    # Nonce (4 bytes)
    nonce = struct.unpack('<I', data[offset:offset+4])[0]
    print(f"Nonce: {nonce} (0x{nonce:08x}) (offset {offset})")
    offset += 4
    
    # SystemFee (8 bytes)
    system_fee = struct.unpack('<Q', data[offset:offset+8])[0]
    print(f"SystemFee: {system_fee} (offset {offset})")
    offset += 8
    
    # NetworkFee (8 bytes)
    network_fee = struct.unpack('<Q', data[offset:offset+8])[0]
    print(f"NetworkFee: {network_fee} (offset {offset})")
    offset += 8
    
    # ValidUntilBlock (4 bytes)
    valid_until = struct.unpack('<I', data[offset:offset+4])[0]
    print(f"ValidUntilBlock: {valid_until} (offset {offset})")
    offset += 4
    
    # Signers (variable)
    signers_count = data[offset]
    print(f"Signers count: {signers_count} (offset {offset})")
    offset += 1
    
    if signers_count > 0:
        # Account (20 bytes)
        account = data[offset:offset+20]
        print(f"  Account: {account.hex()} (offset {offset})")
        offset += 20
        
        # Scope (1 byte)
        scope = data[offset]
        print(f"  Scope: {scope} (0x{scope:02x}) (offset {offset})")
        offset += 1
    
    # Attributes (variable)
    if offset < len(data):
        attrs_count = data[offset]
        print(f"Attributes count: {attrs_count} (offset {offset})")
        offset += 1
    
    # Script (variable)
    if offset < len(data):
        # Read var int for script length
        script_len_byte = data[offset]
        if script_len_byte < 0xFD:
            script_len = script_len_byte
            offset += 1
        elif script_len_byte == 0xFD:
            script_len = struct.unpack('<H', data[offset+1:offset+3])[0]
            offset += 3
        elif script_len_byte == 0xFE:
            script_len = struct.unpack('<I', data[offset+1:offset+5])[0]
            offset += 5
        else:  # 0xFF
            script_len = struct.unpack('<Q', data[offset+1:offset+9])[0]
            offset += 9
        
        print(f"Script length: {script_len} (offset {offset})")
        script = data[offset:offset+script_len]
        print(f"  Script (first 50 bytes): {script[:50].hex()}...")
        offset += script_len
    
    # Witnesses (variable)
    if offset < len(data):
        witnesses_count = data[offset]
        print(f"Witnesses count: {witnesses_count} (offset {offset})")
        offset += 1
        
        if witnesses_count > 0:
            # Read invocation script
            inv_len_byte = data[offset]
            if inv_len_byte < 0xFD:
                inv_len = inv_len_byte
                offset += 1
            elif inv_len_byte == 0xFD:
                inv_len = struct.unpack('<H', data[offset+1:offset+3])[0]
                offset += 3
            else:
                inv_len = struct.unpack('<I', data[offset+1:offset+5])[0]
                offset += 5
            
            print(f"  Invocation script length: {inv_len} (offset {offset})")
            invocation = data[offset:offset+inv_len]
            print(f"    Invocation (first 20 bytes): {invocation[:20].hex()}...")
            offset += inv_len
            
            # Read verification script
            ver_len_byte = data[offset]
            if ver_len_byte < 0xFD:
                ver_len = ver_len_byte
                offset += 1
            elif ver_len_byte == 0xFD:
                ver_len = struct.unpack('<H', data[offset+1:offset+3])[0]
                offset += 3
            else:
                ver_len = struct.unpack('<I', data[offset+1:offset+5])[0]
                offset += 5
            
            print(f"  Verification script length: {ver_len} (offset {offset})")
            verification = data[offset:offset+ver_len]
            print(f"    Verification: {verification.hex()}")
            offset += ver_len
    
    print()
    print(f"Remaining bytes: {len(data) - offset}")
    if offset < len(data):
        print(f"  Extra data: {data[offset:].hex()[:100]}...")
    
    print("=" * 60)

if __name__ == "__main__":
    # Test with the last error transaction
    tx_hex = "00a068747100000000000000000000000000000000bc48d20001dc9f282f06ebbeda871a78e83bca5f79242bd3da0100fd7e010e45017b226e616d65223a22436f6e7472616374222c2267726f757073223a5b5d2c226665617475726573223a7b7d2c22737570706f727465647374616e6461726473223a5b5d2c22616269223a7b226d6574686f6473223a5b7b226e616d65223a225f696e697469616c697a65222c22706172616d6574657273223a5b5d2c2272657475726e74797065223a22566f6964222c226f6666736574223a302c2273616665223a66616c73657d5d2c226576656e7473223a5b5d7d2c227065726d697373696f6e73223a5b7b22636f6e7472616374223a222a222c226d6574686f6473223a222a227d5d2c22747275737473223a5b5d2c226578747261223a7b22417574686f72223a22436861696e4368617274222c224465736372697074696f6e223a2247656e6572617465642066726f6d20436861696e4368617274206469616772616d227d7d0c184e4546330000000000000000000000000000000000000000e8fda3fa4346ea532a258fc497ddaddb6437c9fdff6465706c6f790001420c40cb467d4af22ab6f1e11e8370aa22429ae02f7393350b220a4f208a8cb4d02b8a82a9508adf4f869bebc849572bef91c69a20725c4467dcd538c2e48216be4e12240d2103974b45969ebdf6432990b5b5739120c5fcc966c7cd78be385d586b1832c3fece57"
    analyze_transaction_hex(tx_hex)

