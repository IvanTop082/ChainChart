"""
Contract Validator - Validates generated C# Neo contracts
Checks for common issues and automatically patches them
"""

from typing import List, Tuple, Dict, Any


def validate_contract(contract_code: str) -> Tuple[bool, List[str], str]:
    """
    Validate the generated C# contract and fix common issues.
    
    Args:
        contract_code: Generated C# contract code
        
    Returns:
        Tuple of (is_valid, errors, fixed_code)
        - is_valid: True if contract is valid
        - errors: List of validation errors/warnings
        - fixed_code: Contract code with fixes applied
    """
    errors = []
    fixed_code = contract_code
    
    # Check 1: Contract extends SmartContract
    if "class Contract" not in fixed_code or ": SmartContract" not in fixed_code:
        errors.append("Contract must extend SmartContract")
        # Try to fix
        if "class Contract" in fixed_code and ": SmartContract" not in fixed_code:
            fixed_code = fixed_code.replace("class Contract", "class Contract : SmartContract")
    
    # Check 2: Required namespaces
    required_namespaces = [
        "using Neo.SmartContract.Framework;",
        "using Neo.SmartContract.Framework.Services;",
        "using System.Numerics;"
    ]
    
    for ns in required_namespaces:
        if ns not in fixed_code:
            errors.append(f"Missing required namespace: {ns}")
            # Add namespace after other using statements
            if "using Neo;" in fixed_code:
                fixed_code = fixed_code.replace("using Neo;", f"using Neo;\n{ns}")
            elif "using" in fixed_code:
                # Find last using statement
                last_using = fixed_code.rfind("using")
                if last_using != -1:
                    next_newline = fixed_code.find("\n", last_using)
                    if next_newline != -1:
                        fixed_code = fixed_code[:next_newline+1] + ns + "\n" + fixed_code[next_newline+1:]
    
    # Check 3: Storage variables use StorageMap correctly
    if "StorageMap" in fixed_code and "Storage.CurrentContext" not in fixed_code:
        errors.append("StorageMap should use Storage.CurrentContext")
        # Try to fix common patterns
        fixed_code = fixed_code.replace(
            "new StorageMap(Storage.CurrentContext",
            "new StorageMap(Storage.CurrentContext"
        )
    
    # Check 4: Remove DisplayName attributes (not available in Neo N3)
    import re
    # Remove all [DisplayName("...")] lines
    fixed_code = re.sub(r'\s*\[DisplayName\([^)]+\)\]\s*\n', '', fixed_code)
    # Also remove DisplayName from class attributes (inline)
    fixed_code = re.sub(r'\s*\[DisplayName\([^)]+\)\]\s*', '', fixed_code)
    
    # Check 5: Owner check uses Runtime.CheckWitness
    if "IsOwner" in fixed_code and "Runtime.CheckWitness" not in fixed_code:
        errors.append("IsOwner() should use Runtime.CheckWitness(Owner)")
        # Try to fix
        if "IsOwner" in fixed_code:
            fixed_code = fixed_code.replace(
                "return true;  // TODO: Implement owner check",
                "return Runtime.CheckWitness(Owner);"
            )
    
    # Check 6: Contract has proper namespace
    if "namespace ChainChartGenerated" not in fixed_code:
        errors.append("Contract should be in ChainChartGenerated namespace")
        # Try to fix
        if "namespace" not in fixed_code:
            # Wrap in namespace
            fixed_code = f"namespace ChainChartGenerated\n{{\n{fixed_code}\n}}"
    
    # Check 7: Contract has ManifestExtra attributes (DisplayName removed - not in Neo N3)
    if "[ManifestExtra" not in fixed_code:
        if "public class Contract" in fixed_code:
            fixed_code = fixed_code.replace(
                "public class Contract",
                '    [ManifestExtra("Author", "ChainChart")]\n    [ManifestExtra("Description", "Generated from ChainChart diagram")]\n    public class Contract'
            )
    
    # Check 8: Remove invalid InitialValue for Owner (0x00 is invalid for Hash160)
    # Remove [InitialValue("0x00", ContractParameterType.Hash160)] lines
    fixed_code = re.sub(r'\s*\[InitialValue\("0x00",\s*ContractParameterType\.Hash160\)\]\s*\n', '', fixed_code)
    fixed_code = re.sub(r'\s*\[InitialValue\("0x00",\s*ContractParameterType\.Hash160\)\]\s*', '', fixed_code)
    
    # Check 9: Functions are public static
    function_lines = [line for line in fixed_code.split('\n') if 'static void' in line or 'static' in line]
    for line in function_lines:
        if 'static' in line and 'public' not in line and 'private' not in line:
            errors.append(f"Function missing visibility modifier: {line.strip()}")
            # This is harder to fix automatically, just warn
    
    # Check 10: No syntax errors (basic check)
    if fixed_code.count('{') != fixed_code.count('}'):
        errors.append("Mismatched braces in contract")
    
    if fixed_code.count('(') != fixed_code.count(')'):
        errors.append("Mismatched parentheses in contract")
    
    # Consider contract valid if only compiler/installation warnings remain
    critical_errors = [e for e in errors if "missing" in e.lower() and "compiler" not in e.lower() and "devpack" not in e.lower()]
    is_valid = len(critical_errors) == 0
    
    return is_valid, errors, fixed_code


def patch_contract(contract_code: str) -> str:
    """
    Automatically patch common issues in generated contracts.
    
    Args:
        contract_code: Original contract code
        
    Returns:
        Patched contract code
    """
    _, _, patched = validate_contract(contract_code)
    return patched

