#!/usr/bin/env python
"""
Simple example: Test a workflow that calls your deployed contract.

This demonstrates how to test workflows after generating a contract.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.chainchart_agent import ChainChartAgent

# Your deployed contract hash (from .env or deployment)
CONTRACT_HASH = "0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab"

# Workflow diagram that tests your deployed contract
# This is a SEPARATE diagram from the one used to generate the contract
WORKFLOW_DIAGRAM = {
    "nodes": [
        {
            "id": "1",
            "type": "function",
            "data": {
                "name": "Counter",  # Calls your deployed contract's Counter() method
                "params": []
            }
        },
        {
            "id": "2",
            "type": "function",
            "data": {
                "name": "Increment",  # Calls your deployed contract's Increment() method
                "params": []
            }
        },
        {
            "id": "3",
            "type": "function",
            "data": {
                "name": "Counter",  # Calls Counter() again to verify it incremented
                "params": []
            }
        },
        {
            "id": "4",
            "type": "event",
            "data": {
                "name": "TestComplete"
            }
        }
    ],
    "edges": [
        {"from": "1", "to": "2"},  # First get counter, then increment
        {"from": "2", "to": "3"},  # After increment, check counter again
        {"from": "3", "to": "4"}   # Finally, log completion
    ]
}


async def test_workflow():
    """Test the workflow execution"""
    print("=" * 60)
    print("🧪 Testing Workflow Execution")
    print("=" * 60)
    print()
    print("This workflow will:")
    print("  1. Call Counter() → Get initial value")
    print("  2. Call Increment() → Increment the counter")
    print("  3. Call Counter() again → Verify it incremented")
    print("  4. Log completion event")
    print()
    
    # Create agent
    agent = ChainChartAgent(debug=True)
    
    # Execute workflow
    print("Executing workflow...")
    print("-" * 60)
    result = await agent.run_workflow(WORKFLOW_DIAGRAM)
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 Execution Results")
    print("=" * 60)
    
    print(f"\n✅ Success: {result.get('success', False)}")
    print(f"📝 Steps executed: {len(result.get('execution_logs', []))}")
    
    print("\n📋 Execution Logs:")
    for log in result.get("execution_logs", []):
        step = log.get("step", "?")
        node_type = log.get("type", "unknown")
        node_id = log.get("node", "?")
        
        if node_type == "function":
            method = log.get("method", "unknown")
            output = log.get("output", {})
            print(f"  Step {step}: {node_type} node '{node_id}' → {method}()")
            if output:
                result_data = output.get("result", [])
                if result_data:
                    print(f"    Result: {result_data}")
        elif node_type == "event":
            event_name = log.get("event", "unknown")
            print(f"  Step {step}: {node_type} node '{node_id}' → Event: {event_name}")
        else:
            print(f"  Step {step}: {node_type} node '{node_id}'")
    
    print(f"\n💾 Final Memory: {result.get('final_memory', {})}")
    
    if result.get("debug_logs"):
        print("\n🔍 Debug Logs:")
        for log in result["debug_logs"][:10]:  # Show first 10
            print(f"  {log}")
    
    print("\n" + "=" * 60)
    print("✅ Workflow test complete!")
    print("=" * 60)
    print("\n💡 This demonstrates:")
    print("  - SpoonOS tools execute workflows")
    print("  - Workflows call your deployed contracts")
    print("  - You can test contract functionality")
    print("\n📝 To test in UI:")
    print("  1. Create a similar diagram in the UI")
    print("  2. Click 'Execute' button")
    print("  3. View results in the UI")


if __name__ == "__main__":
    asyncio.run(test_workflow())

