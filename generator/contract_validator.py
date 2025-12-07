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
    # Check if any class extends SmartContract (more flexible than just "Contract")
    has_smartcontract = ": SmartContract" in fixed_code
    has_class = "class " in fixed_code
    
    if not has_class:
        errors.append("Contract must have a class declaration")
    elif not has_smartcontract:
        errors.append("Contract must extend SmartContract")
        # Try to fix - find the first class declaration and add : SmartContract
        import re
        class_match = re.search(r'(public\s+)?class\s+(\w+)(\s*\{|\s*:)', fixed_code)
        if class_match:
            class_decl = class_match.group(0)
            if ": SmartContract" not in class_decl:
                # Replace class declaration to add : SmartContract
                new_decl = class_decl.replace(" {", " : SmartContract {").replace(":", " : SmartContract")
                fixed_code = fixed_code.replace(class_decl, new_decl, 1)
    
    # Check 2: Required namespaces
    required_namespaces = [
        "using Neo;",
        "using Neo.SmartContract.Framework;",
        "using Neo.SmartContract.Framework.Services;",
        "using System.Numerics;"
    ]
    
    # Check if Action is used (needs System)
    if "Action<" in fixed_code or "event Action" in fixed_code:
        if "using System;" not in fixed_code:
            required_namespaces.append("using System;")
    
    # Check if ManifestExtra is used (needs Attributes namespace)
    if "[ManifestExtra" in fixed_code or "ManifestExtraAttribute" in fixed_code:
        if "using Neo.SmartContract.Framework.Attributes;" not in fixed_code:
            required_namespaces.append("using Neo.SmartContract.Framework.Attributes;")
    
    # Ensure all required namespaces are present
    # First, collect all missing namespaces
    missing_namespaces = [ns for ns in required_namespaces if ns not in fixed_code]
    
    if missing_namespaces:
        # Find where to insert using statements
        # They should be at the very top, before namespace or any other code
        
        # Find the first non-whitespace line
        lines = fixed_code.split('\n')
        first_code_line_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('//'):
                first_code_line_idx = i
                break
        
        # Check if there are existing using statements
        using_statements = []
        using_end_idx = first_code_line_idx
        
        for i in range(first_code_line_idx):
            line = lines[i].strip()
            if line.startswith('using '):
                using_statements.append(line)
                using_end_idx = i + 1
        
        # Add missing using statements after existing ones (or at the start)
        for ns in missing_namespaces:
            errors.append(f"Missing required namespace: {ns}")
            # Insert after last using statement, or at the beginning
            if using_statements:
                # Insert after the last using statement
                lines.insert(using_end_idx, ns)
                using_end_idx += 1
            else:
                # Insert at the very beginning
                lines.insert(0, ns)
                using_end_idx += 1
        
        fixed_code = '\n'.join(lines)
    
    # Check 3: Fix ByteString.ToBigInteger() - this method doesn't exist in Neo N3
    # Must use direct cast (BigInteger) instead
    import re
    
    # First, fix double casts that might result from previous fixes
    fixed_code = re.sub(r'\(BigInteger\)\(BigInteger\)', r'(BigInteger)', fixed_code)
    
    # Comprehensive fix for .ToBigInteger() - handle ALL patterns
    # This is a multi-step approach to catch all cases
    
    # Step 1: Fix simple patterns: variable.ToBigInteger()
    fixed_code = re.sub(r'(\b[a-zA-Z_][a-zA-Z0-9_]*)\s*\.ToBigInteger\(\)', r'(BigInteger)\1', fixed_code)
    
    # Step 2: Fix method call patterns: obj.Method().ToBigInteger() or obj.Method(arg).ToBigInteger()
    # Match: identifier, optional property access, method call with args, then .ToBigInteger()
    def fix_method_call_tobiginteger(match):
        expr = match.group(1).strip()
        # Remove trailing whitespace
        expr = expr.rstrip()
        return f'(BigInteger)({expr})'
    
    # Pattern for method calls: matches expressions like storageMap.Get(key) or value.ToString()
    # This pattern is more permissive to catch all method call chains
    method_pattern = r'([a-zA-Z_][a-zA-Z0-9_.]*(?:\([^)]*\))+)\s*\.ToBigInteger\(\)'
    fixed_code = re.sub(method_pattern, fix_method_call_tobiginteger, fixed_code)
    
    # Step 3: Fix property access patterns: obj.Property.ToBigInteger()
    property_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+)\s*\.ToBigInteger\(\)'
    fixed_code = re.sub(property_pattern, fix_method_call_tobiginteger, fixed_code)
    
    # Step 4: Final pass - catch any remaining .ToBigInteger() patterns
    # This is a fallback that handles edge cases
    if '.ToBigInteger()' in fixed_code:
        # Line-by-line fix for any remaining cases
        lines = fixed_code.split('\n')
        for i, line in enumerate(lines):
            if '.ToBigInteger()' in line:
                # Find the expression before .ToBigInteger()
                # Match everything up to .ToBigInteger() that's not whitespace or operators
                # This is a more aggressive pattern
                match = re.search(r'([a-zA-Z_][a-zA-Z0-9_.()\[\]"]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*(?:\([^)]*\))?)*)\s*\.ToBigInteger\(\)', line)
                if match:
                    expr = match.group(1).strip()
                    # Replace in the line
                    old_pattern = expr + '.ToBigInteger()'
                    new_pattern = f'(BigInteger)({expr})'
                    lines[i] = line.replace(old_pattern, new_pattern)
                else:
                    # Last resort: just replace .ToBigInteger() with empty and wrap previous expression
                    # Find the last identifier/expression before .ToBigInteger()
                    match = re.search(r'([^=;\s]+)\s*\.ToBigInteger\(\)', line)
                    if match:
                        expr = match.group(1).strip()
                        lines[i] = line.replace(f'{expr}.ToBigInteger()', f'(BigInteger)({expr})')
        fixed_code = '\n'.join(lines)
    
    # Step 5: Final verification - if still has .ToBigInteger(), log warning
    if '.ToBigInteger()' in fixed_code:
        errors.append("Warning: Some .ToBigInteger() patterns could not be automatically fixed")
    
    # Check 3.5: Fix invalid null-coalescing operator (??) with ByteString
    # Pattern: storageMap.Get(key) ?? 0 or value ?? 0 where value is ByteString
    # This is invalid because ByteString ?? int doesn't work in C#
    # Should be: ByteString value = storageMap.Get(key); return value is null ? 0 : (BigInteger)value;
    
    # Fix patterns like: var x = storageMap.Get(key) ?? 0;
    # Or: return storageMap.Get(key) ?? 0;
    lines = fixed_code.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if '??' in line:
            # Check if this line contains a storage operation (ByteString)
            is_storage_op = '.Get(' in line or 'Map' in line or 'Storage' in line
            
            if is_storage_op:
                # Pattern 1: var x = expr ?? number;
                match = re.search(r'(var\s+\w+\s*=\s*)([^;]+?)\s*\?\?\s*(\d+)\s*;', line)
                if match:
                    var_decl = match.group(1)  # "var x = "
                    expr = match.group(2).strip()  # storageMap.Get(key)
                    default = match.group(3).strip()  # 0
                    var_name_match = re.search(r'var\s+(\w+)', var_decl)
                    if var_name_match:
                        var_name = var_name_match.group(1)
                        temp_var = f'temp_{var_name}'
                        indent = len(line) - len(line.lstrip())
                        # Replace the line with two lines
                        lines[i] = f'{" " * indent}ByteString {temp_var} = {expr};'
                        lines.insert(i + 1, f'{" " * indent}{var_decl}{temp_var} is null ? {default} : (BigInteger){temp_var};')
                        i += 1  # Skip the inserted line
                        continue
                
                # Pattern 2: return expr ?? number;
                match = re.search(r'return\s+([^;]+?)\s*\?\?\s*(\d+)\s*;', line)
                if match:
                    expr = match.group(1).strip()
                    default = match.group(2).strip()
                    temp_var = 'temp_return'
                    indent = len(line) - len(line.lstrip())
                    # Replace the line with two lines
                    lines[i] = f'{" " * indent}ByteString {temp_var} = {expr};'
                    lines.insert(i + 1, f'{" " * indent}return {temp_var} is null ? {default} : (BigInteger){temp_var};')
                    i += 1  # Skip the inserted line
                    continue
                
                # Pattern 3: Any expression ?? number (fallback)
                # Replace with ternary operator inline
                match = re.search(r'([a-zA-Z_][a-zA-Z0-9_.]*(?:\([^)]*\))*)\s*\?\?\s*(\d+)', line)
                if match:
                    expr = match.group(1).strip()
                    default = match.group(2).strip()
                    # Replace with ternary operator
                    lines[i] = line.replace(
                        f'{expr} ?? {default}',
                        f'({expr} is null ? {default} : (BigInteger){expr})'
                    )
        i += 1
    
    fixed_code = '\n'.join(lines)
    
    # Check 4: Storage variables use StorageMap correctly
    if "StorageMap" in fixed_code and "Storage.CurrentContext" not in fixed_code:
        errors.append("StorageMap should use Storage.CurrentContext")
        # Try to fix common patterns
        fixed_code = fixed_code.replace(
            "new StorageMap(Storage.CurrentContext",
            "new StorageMap(Storage.CurrentContext"
        )
    
    # Check 5: Remove DisplayName attributes (not available in Neo N3)
    # Remove all [DisplayName("...")] lines (standalone)
    fixed_code = re.sub(r'\s*\[DisplayName\([^)]+\)\]\s*\n', '', fixed_code)
    # Remove DisplayName from class attributes (inline with other attributes)
    fixed_code = re.sub(r'\[DisplayName\([^)]+\)\]\s*,?\s*', '', fixed_code)
    # Remove DisplayNameAttribute references
    fixed_code = re.sub(r'\s*\[DisplayNameAttribute\([^)]+\)\]\s*\n', '', fixed_code)
    fixed_code = re.sub(r'\[DisplayNameAttribute\([^)]+\)\]\s*,?\s*', '', fixed_code)
    # Remove any remaining DisplayName references
    fixed_code = re.sub(r'\s*DisplayName\s*', '', fixed_code)
    
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
        else:
            # Replace existing namespace with ChainChartGenerated
            import re
            fixed_code = re.sub(r'namespace\s+\w+\s*\{', 'namespace ChainChartGenerated\n{', fixed_code, count=1)
    
    # Check 7: Contract has ManifestExtra attributes (DisplayName removed - not in Neo N3)
    if "[ManifestExtra" not in fixed_code:
        # Find any public class declaration and add ManifestExtra before it
        import re
        class_match = re.search(r'(public\s+class\s+\w+)', fixed_code)
        if class_match:
            class_decl = class_match.group(1)
            manifest_extra = '    [ManifestExtra("Author", "ChainChart")]\n    [ManifestExtra("Description", "Generated from ChainChart diagram")]\n    '
            fixed_code = fixed_code.replace(class_decl, manifest_extra + class_decl, 1)
    
    # Check 8: Remove invalid InitialValue for Owner (0x00 is invalid for Hash160)
    # Remove [InitialValue("0x00", ContractParameterType.Hash160)] lines
    fixed_code = re.sub(r'\s*\[InitialValue\("0x00",\s*ContractParameterType\.Hash160\)\]\s*\n', '', fixed_code)
    fixed_code = re.sub(r'\s*\[InitialValue\("0x00",\s*ContractParameterType\.Hash160\)\]\s*', '', fixed_code)
    
    # Check 8.5: Fix variable names with spaces (invalid C# syntax)
    # Pattern: "private static StorageMap Variable Name =>" -> "private static StorageMap VariableName =>"
    # This fixes cases like "New stateMap" -> "NewstateMap"
    # Also handles cases where multiple statements are on one line
    lines = fixed_code.split('\n')
    for i, line in enumerate(lines):
        # Fix StorageMap declarations: "StorageMap Word1 Word2 =>" -> "StorageMap Word1Word2 =>"
        # Handle cases where multiple statements are on one line by fixing each occurrence
        original_line = line
        while 'StorageMap' in line and '=>' in line:
            # Match: "StorageMap [identifier with possible spaces] =>"
            # More flexible pattern that handles any whitespace
            match = re.search(r'(private\s+static\s+StorageMap\s+)([a-zA-Z_][a-zA-Z0-9_\s]*?)(\s*=>)', line)
            if match:
                prefix = match.group(1)
                var_name_with_spaces = match.group(2).strip()
                suffix = match.group(3)
                # Remove all spaces from variable name
                var_name = var_name_with_spaces.replace(' ', '').replace('\t', '').replace('\n', '')
                if var_name != var_name_with_spaces:
                    # Replace the variable name part
                    old_pattern = prefix + var_name_with_spaces + suffix
                    new_pattern = prefix + var_name + suffix
                    line = line.replace(old_pattern, new_pattern, 1)  # Replace only first occurrence
                    lines[i] = line
                else:
                    break  # No more spaces to fix
            else:
                break  # No match found
        # Update line if changed
        if line != original_line:
            lines[i] = line
        
        # Fix event declarations with spaces: "event Action<> New event;" -> "event Action<> Newevent;"
        # Handle multiple events on same line - use findall to fix ALL occurrences
        original_line = line
        # Find all event declarations with spaces in their names
        # Pattern: "public static event Action<> Variable Name;" or "event Action<> Variable Name;"
        event_pattern = r'(public\s+static\s+event\s+Action[^;]*?\s+)([a-zA-Z_][a-zA-Z0-9_\s]+?)(\s*[;=])'
        matches = list(re.finditer(event_pattern, line))
        if not matches:
            # Try without "public static"
            event_pattern = r'(event\s+Action[^;]*?\s+)([a-zA-Z_][a-zA-Z0-9_\s]+?)(\s*[;=])'
            matches = list(re.finditer(event_pattern, line))
        
        # Fix all matches that have spaces in the variable name
        for match in reversed(matches):  # Process in reverse to maintain positions
            var_name_with_spaces = match.group(2).strip()
            if ' ' in var_name_with_spaces:
                prefix = match.group(1)
                suffix = match.group(3)
                var_name = var_name_with_spaces.replace(' ', '').replace('\t', '').replace('\n', '')
                old_pattern = prefix + var_name_with_spaces + suffix
                new_pattern = prefix + var_name + suffix
                line = line.replace(old_pattern, new_pattern, 1)
        
        if line != original_line:
            lines[i] = line
        
        # Fix other variable declarations with spaces
        # Pattern: "BigInteger Variable Name" or "void Variable Name("
        while re.search(r'(private\s+static\s+(?:BigInteger|void|string|ByteString|bool)\s+)([a-zA-Z_][a-zA-Z0-9_\s]+?)(\s*[={\(;])', line):
            match = re.search(r'(private\s+static\s+(?:BigInteger|void|string|ByteString|bool)\s+)([a-zA-Z_][a-zA-Z0-9_\s]+?)(\s*[={\(;])', line)
            if match:
                prefix = match.group(1)
                var_name_with_spaces = match.group(2).strip()
                suffix = match.group(3)
                # Remove all spaces from variable name
                var_name = var_name_with_spaces.replace(' ', '').replace('\t', '').replace('\n', '')
                if var_name != var_name_with_spaces:
                    old_pattern = prefix + var_name_with_spaces + suffix
                    new_pattern = prefix + var_name + suffix
                    line = line.replace(old_pattern, new_pattern, 1)
                    lines[i] = line
                else:
                    break
            else:
                break
    
    # Also fix function names with spaces: "void New function(" -> "void Newfunction("
    for i, line in enumerate(lines):
        if 'public static void' in line or 'private static void' in line:
            match = re.search(r'(public\s+static\s+void\s+)([a-zA-Z_][a-zA-Z0-9_\s]+?)(\s*\()', line)
            if match:
                prefix = match.group(1)
                func_name_with_spaces = match.group(2).strip()
                suffix = match.group(3)
                func_name = func_name_with_spaces.replace(' ', '').replace('\t', '').replace('\n', '')
                if func_name != func_name_with_spaces:
                    old_pattern = prefix + func_name_with_spaces + suffix
                    new_pattern = prefix + func_name + suffix
                    lines[i] = line.replace(old_pattern, new_pattern, 1)
    
    fixed_code = '\n'.join(lines)
    
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

