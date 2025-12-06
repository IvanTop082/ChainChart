async def execute_node(agent, node, memory, debug: bool = False):
    """
    Execute a single node in the workflow.
    
    Args:
        agent: ChainChartAgent instance
        node: Node to execute
        memory: Memory dictionary
        debug: Enable debug logging
    """
    node_type = node["type"]
    data = node.get("data", {})
    
    if debug:
        print(f"[DEBUG] Executing node type: {node_type}, data: {data}")

    if node_type == "state":
        key = data["label"]
        result = await agent.run_tool("read_neo_state", {"key": key})
        memory[key] = result
        return result

    if node_type == "condition":
        expr = data["expression"]
        try:
            return eval(expr, {}, memory)
        except Exception as e:
            await agent.run_tool("debug_log", {"msg": f"Condition error: {str(e)}"})
            return False

    if node_type == "operation":
        # Get operands from memory, with error handling
        operand_a_key = data.get("a", "")
        operand_b_key = data.get("b")
        
        # Check if operand_a exists in memory
        if operand_a_key not in memory:
            error_msg = f"Operand '{operand_a_key}' not found in memory. Available keys: {list(memory.keys())}"
            await agent.run_tool("debug_log", {"msg": error_msg})
            raise KeyError(error_msg)
        
        operand_a = memory[operand_a_key]
        
        # Handle operand_b: could be a memory key or a literal value
        operand_b = None
        if operand_b_key:
            # First try to get from memory (if it's a key)
            if operand_b_key in memory:
                operand_b = memory[operand_b_key]
            else:
                # If not in memory, treat it as a literal value (string or number)
                # The OperationTool will handle string-to-number conversion
                operand_b = operand_b_key
        
        return await agent.run_tool("perform_operation", {
            "op": data.get("op", "add"),
            "a": operand_a,
            "b": operand_b
        })

    if node_type == "function":
        return await agent.run_tool("call_neo_contract", {
            "method": data["name"],
            "args": data.get("params", [])
        })

    if node_type == "event":
        return await agent.run_tool("debug_log", {"msg": data["name"]})

    if node_type == "modifier":
        return await agent.run_tool("debug_log", {"msg": f"Modifier applied: {data['name']}"})

    return None
