async def execute_node(agent, node, memory):
    node_type = node["type"]
    data = node.get("data", {})

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
        return await agent.run_tool("perform_operation", {
            "op": data["op"],
            "a": memory[data["a"]],
            "b": memory.get(data.get("b"))
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
