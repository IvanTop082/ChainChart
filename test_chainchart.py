import asyncio

from agent.chainchart_agent import create_chainchart_agent
from agent.chainchart_parser import parse_chainchart
from agent.chainchart_executor import execute_node

# ---------------------------------------------
# A CLEAN, SIMPLE DIAGRAM TO TEST EVERYTHING
# ---------------------------------------------
TEST_DIAGRAM = {
    "nodes": [
        {
            "id": "1",
            "type": "state",
            "data": {"label": "balance"}
        },
        {
            "id": "2",
            "type": "operation",
            "data": {"op": "add", "a": "balance", "b": "balance"}
        },
        {
            "id": "3",
            "type": "event",
            "data": {"name": "Computation Finished"}
        }
    ],
    "edges": [
        {"from": "1", "to": "2"},
        {"from": "2", "to": "3"}
    ]
}


async def run_test():
    print("\n=== INITIALIZING AGENT ===")
    agent = create_chainchart_agent()

    print("\n=== PARSING DIAGRAM ===")
    nodes, edges = parse_chainchart(TEST_DIAGRAM)

    print("\n=== BEGIN EXECUTION ===")
    memory = {}
    logs = []

    current = "1"
    step = 0

    while current:
        step += 1
        node = nodes[current]

        print(f"\n--- Step {step}: Executing Node {current} ({node['type']}) ---")
        result = await execute_node(agent, node, memory)
        print(f"Result: {result}")
        print(f"Memory: {memory}")

        logs.append({
            "step": step,
            "node": current,
            "type": node["type"],
            "result": result,
            "memory": memory.copy()
        })

        next_list = edges.get(current, [])
        if not next_list:
            break
        current = next_list[0]

    print("\n=== WORKFLOW COMPLETED ===")
    return logs


if __name__ == "__main__":
    asyncio.run(run_test())

