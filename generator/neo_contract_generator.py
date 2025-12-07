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
    
    # Create a map of node IDs to nodes for quick lookup
    node_map = {n.get("id"): n for n in nodes}
    
    for node in function_nodes:
        node_data = node.get("data", {})
        func_name = node_data.get("name", f"function_{node.get('id', '')}")
        params = node_data.get("params", [])
        return_type = node_data.get("returnType", "")
        visibility = node_data.get("visibility", "public")
        payable = node_data.get("payable", False)
        node_id = node.get("id", "")
        
        # Sanitize function name
        func_name = sanitize_identifier(func_name)
        
        # If duplicate name, append node ID to make it unique
        if func_name in seen_names:
            func_name = f"{func_name}_{node_id}"
        seen_names.add(func_name)
        
        # Parse parameters - handle multiple formats
        param_list = []
        if isinstance(params, list):
            for param in params:
                if isinstance(param, dict):
                    # Handle object format: {"name": "x", "type": "Integer"}
                    param_name = sanitize_identifier(param.get("name", ""))
                    param_type_str = param.get("type", "string")
                    param_type = map_type_to_neo(param_type_str)
                    if param_name:
                        param_list.append(f"{param_type} {param_name}")
                elif isinstance(param, str):
                    # Parse "Type name" format (e.g., "address to", "uint256 amount")
                    parts = param.strip().split()
                    if len(parts) >= 2:
                        param_type = map_type_to_neo(parts[0])
                        param_name = sanitize_identifier(parts[1])
                        param_list.append(f"{param_type} {param_name}")
                    elif len(parts) == 1:
                        # Just a type, generate a name
                        param_type = map_type_to_neo(parts[0])
                        param_name = f"param{len(param_list)}"
                        param_list.append(f"{param_type} {param_name}")
        elif isinstance(params, str) and params:
            # Parse comma-separated string (e.g., "address to, uint256 amount")
            for param in params.split(","):
                param = param.strip()
                if param:
                    parts = param.split()
                    if len(parts) >= 2:
                        param_type = map_type_to_neo(parts[0])
                        param_name = sanitize_identifier(parts[1])
                        param_list.append(f"{param_type} {param_name}")
                    elif len(parts) == 1:
                        # Just a type, generate a name
                        param_type = map_type_to_neo(parts[0])
                        param_name = f"param{len(param_list)}"
                        param_list.append(f"{param_type} {param_name}")
        
        params_str = ", ".join(param_list) if param_list else ""
        payable_attr = " payable" if payable else ""
        
        # Determine return type
        if return_type:
            return_type_cs = map_type_to_neo(return_type)
        else:
            return_type_cs = "void"
        
        # Generate function body based on connected nodes
        function_body = generate_function_body(node_id, nodes, edges, node_map)
        
        code += f"        public static {return_type_cs} {func_name}({params_str}){payable_attr}\n"
        code += "        {\n"
        code += function_body
        code += "        }\n\n"
    
    return code


def generate_function_body(function_id: str, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]]) -> str:
    """
    Generate function body code by tracing edges from function node.
    
    Args:
        function_id: ID of the function node
        nodes: List of all nodes
        edges: List of all edges
        node_map: Map of node ID to node for quick lookup
        
    Returns:
        C# code string for function body
    """
    body_lines = []
    
    # Find all edges starting from this function
    outgoing_edges = [e for e in edges if e.get("from") == function_id]
    
    if not outgoing_edges:
        # No connections, return empty body with comment
        return "            // Add your logic here\n"
    
    # Find state nodes for reference
    state_nodes = {n.get("id"): n for n in nodes if n.get("type") == "state"}
    
    # Build execution path by following edges
    visited = set()
    execution_order = []
    
    def trace_path(current_id: str, depth: int = 0):
        """Recursively trace execution path from current node."""
        if depth > 20:  # Prevent infinite loops
            return
        if current_id in visited:
            return
        
        visited.add(current_id)
        current_node = node_map.get(current_id)
        if not current_node:
            return
        
        node_type = current_node.get("type")
        node_data = current_node.get("data", {})
        
        # Add to execution order
        execution_order.append((current_id, node_type, node_data, current_node))
        
        # Find next nodes
        next_edges = [e for e in edges if e.get("from") == current_id]
        for edge in next_edges:
            next_id = edge.get("to")
            if next_id and next_id not in visited:
                trace_path(next_id, depth + 1)
    
    # Start tracing from connected nodes
    for edge in outgoing_edges:
        next_id = edge.get("to")
        if next_id:
            trace_path(next_id)
    
    # Generate code for each node in execution order
    for node_id, node_type, node_data, node in execution_order:
        if node_type == "operation":
            # Generate operation code
            op_code = generate_operation_code(node_id, node_data, nodes, edges, node_map, state_nodes)
            if op_code:
                body_lines.append(op_code)
        
        elif node_type == "condition":
            # Generate condition code
            condition_code = generate_condition_code(node_id, node_data, nodes, edges, node_map)
            if condition_code:
                body_lines.append(condition_code)
        
        elif node_type == "state":
            # State nodes are targets, not sources of operations
            # But we might need to read from them
            pass
        
        elif node_type == "event":
            # Generate event emission
            event_name = sanitize_identifier(node_data.get("name", "Event"))
            body_lines.append(f"            {event_name}?.Invoke(\"\");")
    
    if not body_lines:
        return "            // Add your logic here\n"
    
    return "\n".join(body_lines) + "\n"


def generate_operation_code(op_id: str, op_data: Dict[str, Any], nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]], state_nodes: Dict[str, Dict[str, Any]]) -> str:
    """Generate C# code for an operation node."""
    op = op_data.get("op", "add")
    operand_a = op_data.get("operand_a", op_data.get("a", ""))
    operand_b = op_data.get("operand_b", op_data.get("b", ""))
    value = op_data.get("value", "")
    
    # Check if this operation connects to a state node (for storage updates)
    next_edges = [e for e in edges if e.get("from") == op_id]
    target_state = None
    for edge in next_edges:
        target_id = edge.get("to")
        if target_id in state_nodes:
            target_state = state_nodes[target_id]
            break
    
    # If there's a value expression, try to use it
    if value:
        # Try to convert the value expression to C# code
        code = value
        
        # Replace state variable references with actual variable names
        for state_id, state_node in state_nodes.items():
            state_label = state_node.get("data", {}).get("label", "")
            if state_label:
                state_var = sanitize_identifier(state_label)
                # Replace state references (handle both with and without spaces)
                code = code.replace(state_label, state_var)
                # Also try replacing with sanitized version
                code = code.replace(state_label.replace(" ", ""), state_var)
        
        # If operation targets a state node, generate storage update
        if target_state:
            state_label = target_state.get("data", {}).get("label", "")
            state_var = sanitize_identifier(state_label)
            # Extract the right-hand side of the expression
            if "=" in code:
                # Already has assignment
                return f"            Set{state_var.capitalize()}({code.split('=')[1].strip()});"
            else:
                # Need to evaluate expression and store
                return f"            Set{state_var.capitalize()}({code});"
        
        # Handle assignment operations
        if "=" in code and "==" not in code:
            # This is an assignment
            return f"            {code};"
        elif code.endswith(";"):
            return f"            {code}"
        else:
            return f"            {code};"
    
    # Generate based on operation type
    if target_state:
        # Operation updates a state variable
        state_label = target_state.get("data", {}).get("label", "")
        state_var = sanitize_identifier(state_label)
        
        if op == "add" or op == "+":
            if operand_b:
                return f"            Set{state_var.capitalize()}({state_var} + {operand_b});"
            else:
                return f"            Set{state_var.capitalize()}({state_var} + 1);"
        elif op == "subtract" or op == "-":
            if operand_b:
                return f"            Set{state_var.capitalize()}({state_var} - {operand_b});"
            else:
                return f"            Set{state_var.capitalize()}({state_var} - 1);"
        elif op == "multiply" or op == "*":
            return f"            Set{state_var.capitalize()}({state_var} * {operand_b});"
        elif op == "divide" or op == "/":
            return f"            Set{state_var.capitalize()}({state_var} / {operand_b});"
        else:
            return f"            // Operation: {op} on {state_var}"
    else:
        # Generic operation without state target
        if op == "add" or op == "+":
            return f"            {operand_a} = {operand_a} + {operand_b};"
        elif op == "subtract" or op == "-":
            return f"            {operand_a} = {operand_a} - {operand_b};"
        elif op == "multiply" or op == "*":
            return f"            {operand_a} = {operand_a} * {operand_b};"
        elif op == "divide" or op == "/":
            return f"            {operand_a} = {operand_a} / {operand_b};"
        else:
            # Generic operation
            if operand_a and operand_b:
                return f"            // Operation: {op} on {operand_a} and {operand_b}"
            else:
                return f"            // Operation: {op}"


def generate_condition_code(condition_id: str, condition_data: Dict[str, Any], nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]]) -> str:
    """Generate C# code for a condition node (if/else)."""
    expression = condition_data.get("expression", "true")
    
    # Find true and false paths
    true_path_edges = [e for e in edges if e.get("from") == condition_id]
    # In Neo, we'll generate a simple if statement
    # For now, just generate the condition check
    
    return f"            if ({expression})\n            {{\n                // True path\n            }}\n            else\n            {{\n                // False path\n            }}"


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

