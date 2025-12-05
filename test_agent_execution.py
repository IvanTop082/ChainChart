import asyncio
from agent.chainchart_agent import ChainChartAgent

TEST_DIAGRAM = {
    "nodes": [
        {"id": "1", "type": "state", "data": {"label": "balance"}},
        {"id": "2", "type": "operation", "data": {"op": "add", "a": "balance", "b": "balance"}},
        {"id": "3", "type": "event", "data": {"name": "Finished Flow"}}
    ],
    "edges": [
        {"from": "1", "to": "2"},
        {"from": "2", "to": "3"}
    ]
}

async def main():
    agent = ChainChartAgent()
    result = await agent.run_workflow(TEST_DIAGRAM)

    print("\n=== EXECUTION LOGS ===")
    for log in result["execution_logs"]:
        print(log)

    print("\n=== FINAL MEMORY ===")
    print(result["final_memory"])

if __name__ == "__main__":
    asyncio.run(main())

