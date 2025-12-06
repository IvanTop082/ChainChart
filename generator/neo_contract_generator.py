"""
Neo Contract Generator - Deterministic C# contract generation from ChainChart JSON
Converts ChainChart nodes into Neo N3 smart contract code
"""

from typing import Dict, Any, List
from pathlib import Path


def generate_storage_variables(nodes: List[Dict[str, Any]]) -> str:
    """
    Convert ChainChart State nodes into C# StorageMap variables.
    
    Args:
        nodes: List of ChainChart nodes
        
    Returns:
        C# code string for storage variable declarations
    """
    state_nodes = [n for n in nodes if n.get("type") == "state"]
    
    if not state_nodes:
        return ""
    
    code = "        // Storage Variables\n"
    
    # Track seen variable names to prevent duplicates
    seen_names = set()
    
    for node in state_nodes:
        node_data = node.get("data", {})
        label = node_data.get("label", f"state_{node.get('id', '')}")
        node_id = node.get("id", "")
        
        # Sanitize label for C# identifier - remove ALL spaces and special chars
        var_name = sanitize_identifier(label)
        # Double-check: ensure no spaces remain (defensive)
        var_name = ''.join(var_name.split())  # Remove all whitespace
        
        # If duplicate name, append node ID to make it unique
        if var_name in seen_names:
            var_name = f"{var_name}_{node_id}"
        seen_names.add(var_name)
        
        storage_key = label
        
        # Use property syntax (expression-bodied property is valid C#)
        code += f'        private static StorageMap {var_name}Map => new StorageMap(Storage.CurrentContext, "{storage_key}");\n'
        code += f"        private static BigInteger {var_name}\n"
        code += f"        {{\n"
        code += f"            get\n"
        code += f"            {{\n"
        code += f"                var value = {var_name}Map.Get(ByteString.Empty);\n"
        code += f"                return value is null ? 0 : (BigInteger)value;\n"
        code += f"            }}\n"
        code += f"        }}\n"
        code += f"        private static void Set{var_name.capitalize()}(BigInteger value)\n"
        code += f"        {{\n"
        code += f"            {var_name}Map.Put(ByteString.Empty, (ByteString)value);\n"
        code += f"        }}\n\n"
    
    return code


def generate_functions(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """
    Convert Function nodes into C# public static methods.
    
    Args:
        nodes: List of ChainChart nodes
        edges: List of ChainChart edges (for control flow)
        
    Returns:
        C# code string for function declarations
    """
    function_nodes = [n for n in nodes if n.get("type") == "function"]
    
    if not function_nodes:
        return ""
    
    code = "        // Functions\n"
    
    # Track seen function names to prevent duplicates
    seen_names = set()
    
    for node in function_nodes:
        node_data = node.get("data", {})
        func_name = node_data.get("name", f"function_{node.get('id', '')}")
        params = node_data.get("params", [])
        visibility = node_data.get("visibility", "public")
        payable = node_data.get("payable", False)
        node_id = node.get("id", "")
        
        # Sanitize function name
        func_name = sanitize_identifier(func_name)
        
        # If duplicate name, append node ID to make it unique
        if func_name in seen_names:
            func_name = f"{func_name}_{node_id}"
        seen_names.add(func_name)
        
        # Parse parameters
        param_list = []
        if isinstance(params, list):
            for param in params:
                if isinstance(param, str):
                    # Parse "Type name" format
                    parts = param.strip().split()
                    if len(parts) >= 2:
                        param_type = map_type_to_neo(parts[0])
                        param_name = sanitize_identifier(parts[1])
                        param_list.append(f"{param_type} {param_name}")
        elif isinstance(params, str) and params:
            # Parse comma-separated string
            for param in params.split(","):
                param = param.strip()
                if param:
                    parts = param.split()
                    if len(parts) >= 2:
                        param_type = map_type_to_neo(parts[0])
                        param_name = sanitize_identifier(parts[1])
                        param_list.append(f"{param_type} {param_name}")
        
        params_str = ", ".join(param_list) if param_list else ""
        payable_attr = " payable" if payable else ""
        
        code += f"        public static void {func_name}({params_str}){payable_attr}\n"
        code += "        {\n"
        code += "            // TODO: Implement function logic based on connected nodes\n"
        code += "        }\n\n"
    
    return code


def generate_events(nodes: List[Dict[str, Any]]) -> str:
    """
    Convert Event nodes into [DisplayName(...)] public static event declarations.
    
    Args:
        nodes: List of ChainChart nodes
        
    Returns:
        C# code string for event declarations
    """
    event_nodes = [n for n in nodes if n.get("type") == "event"]
    
    if not event_nodes:
        return ""
    
    code = "        // Events\n"
    
    # Track seen event names to prevent duplicates
    seen_names = set()
    
    for node in event_nodes:
        node_data = node.get("data", {})
        event_name = node_data.get("name", f"Event_{node.get('id', '')}")
        params = node_data.get("params", "")
        node_id = node.get("id", "")
        
        # Sanitize event name
        event_name = sanitize_identifier(event_name)
        
        # If duplicate name, append node ID to make it unique
        original_name = event_name
        if event_name in seen_names:
            event_name = f"{event_name}_{node_id}"
        seen_names.add(event_name)
        
        # Parse event parameters - extract only types, not parameter names
        if isinstance(params, str) and params:
            # Map common types - extract only the type, not the parameter name
            param_types = []
            for param in params.split(","):
                param = param.strip()
                if param:
                    # Split by space and take first part (the type)
                    parts = param.split()
                    if len(parts) >= 1:
                        # Only use the type, ignore parameter name
                        param_type = map_type_to_neo(parts[0])
                        param_types.append(param_type)
            
            # If no valid types found, use default
            params_str = ", ".join(param_types) if param_types else "string"
        else:
            params_str = "string"
        
        # DisplayName removed - not needed for Neo N3
        code += f"        public static event Action<{params_str}> {event_name};\n\n"
    
    return code


def generate_modifiers(nodes: List[Dict[str, Any]]) -> str:
    """
    Optional: convert special nodes into owner checks or time locks.
    
    Args:
        nodes: List of ChainChart nodes
        
    Returns:
        C# code string for modifier/access control logic
    """
    modifier_nodes = [n for n in nodes if n.get("type") == "modifier"]
    
    if not modifier_nodes:
        # Default owner check
        return """        // Owner Check Modifier
        private static bool IsOwner()
        {
            return Runtime.CheckWitness(Owner);
        }

"""
    
    code = "        // Modifiers\n"
    
    for node in modifier_nodes:
        node_data = node.get("data", {})
        modifier_name = node_data.get("name", f"modifier_{node.get('id', '')}")
        expression = node_data.get("expression", "true")
        
        modifier_name = sanitize_identifier(modifier_name)
        
        code += f"        private static bool {modifier_name}()\n"
        code += "        {\n"
        code += f"            // TODO: Implement modifier logic: {expression}\n"
        code += "            return true;\n"
        code += "        }\n\n"
    
    return code


def generate_contract_class(
    storage: str,
    functions: str,
    events: str,
    modifiers: str
) -> str:
    """
    Wrap everything in a valid Neo smart contract class.
    
    Args:
        storage: C# code for storage variables
        functions: C# code for functions
        events: C# code for events
        modifiers: C# code for modifiers
        
    Returns:
        Complete C# contract code
    """
    contract = """using Neo;
using Neo.SmartContract;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;
using System.Runtime.InteropServices;

namespace ChainChartGenerated
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Generated from ChainChart diagram")]
    public class Contract : SmartContract
    {
        private static readonly UInt160 Owner = default;

"""
    
    # Add storage variables
    if storage:
        contract += storage
    
    # Add modifiers
    if modifiers:
        contract += modifiers
    else:
        contract += """        // Owner Check Modifier
        private static bool IsOwner()
        {
            return Runtime.CheckWitness(Owner);
        }

"""
    
    # Add events
    if events:
        contract += events
    else:
        contract += """        // Events
        public static event Action<string> Log;

"""
    
    # Add functions
    if functions:
        contract += functions
    else:
        contract += """        // Functions
        public static void _initialize()
        {
            // Contract initialization
        }

"""
    
    contract += "    }\n}"
    
    return contract


def write_contract_to_file(contract_code: str, output_path: str) -> None:
    """
    Write generated .cs file to disk.
    
    Args:
        contract_code: Complete C# contract code
        output_path: Path where to write the .cs file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contract_code, encoding='utf-8')


def sanitize_identifier(name: str) -> str:
    """Sanitize a name to be a valid C# identifier."""
    import re
    # First, remove all spaces and special characters, keep alphanumeric and underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', name)
    # Remove any remaining whitespace (just in case)
    sanitized = sanitized.replace(' ', '').replace('\t', '').replace('\n', '')
    # Ensure it starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = '_' + sanitized
    # If empty, use default
    if not sanitized:
        sanitized = 'Item'
    # Ensure no spaces remain
    assert ' ' not in sanitized, f"Sanitized identifier still contains space: '{sanitized}' from '{name}'"
    return sanitized


def map_type_to_neo(type_str: str) -> str:
    """Map common type names to Neo N3 types."""
    type_mapping = {
        'uint256': 'BigInteger',
        'uint': 'BigInteger',
        'int': 'BigInteger',
        'address': 'UInt160',
        'bytes': 'ByteString',
        'string': 'string',
        'bool': 'bool',
        'BigInteger': 'BigInteger',
        'ByteString': 'ByteString',
        'UInt160': 'UInt160',
        'UInt256': 'UInt256',
    }
    
    # Try exact match first
    if type_str in type_mapping:
        return type_mapping[type_str]
    
    # Try case-insensitive match
    for key, value in type_mapping.items():
        if key.lower() == type_str.lower():
            return value
    
    # Default to BigInteger for numeric types, string for others
    if any(num in type_str.lower() for num in ['int', 'uint', 'number']):
        return 'BigInteger'
    
    return 'string'


def generate_contract_from_diagram(diagram_json: Dict[str, Any]) -> str:
    """
    Main entry point: Generate complete contract from ChainChart diagram.
    
    Args:
        diagram_json: ChainChart diagram with nodes and edges
        
    Returns:
        Complete C# contract code
    """
    nodes = diagram_json.get("nodes", [])
    edges = diagram_json.get("edges", [])
    
    # Generate components
    storage = generate_storage_variables(nodes)
    functions = generate_functions(nodes, edges)
    events = generate_events(nodes)
    modifiers = generate_modifiers(nodes)
    
    # Combine into complete contract
    contract = generate_contract_class(storage, functions, events, modifiers)
    
    return contract

