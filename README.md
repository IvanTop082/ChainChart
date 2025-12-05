# ChainChart

Phase 2 Backend - ChainChart workflow execution system using SpoonOS SDK.

## Overview

ChainChart is a workflow execution system that:
- Parses ChainChart JSON diagrams into FlowGraph structures
- Executes nodes step-by-step with memory management
- Integrates with Neo blockchain via SpoonOS tools
- Provides full execution trace logging

## Architecture

- **FlowGraph**: Data structure representing the workflow graph
- **ChainChartAgent**: Main agent orchestrating workflow execution
- **Tools**: Neo state reading, contract calls, operations, debug logging
- **Memory**: Dict-based memory store for workflow state

## Project Structure

```
/agent/
    chainchart_agent.py    # Main ChainChartAgent class
    chainchart_tools.py    # SpoonOS tools (BaseTool subclasses)
    chainchart_executor.py # Node execution logic
    flowgraph.py          # FlowGraph and Memory classes
/test_agent_execution.py  # Test execution script
```

## Installation

1. Install dependencies:
```bash
uv pip install -r reqirements.txt
```

Or with regular pip:
```bash
pip install -r reqirements.txt
```

## Usage

```python
import asyncio
from agent.chainchart_agent import ChainChartAgent

diagram = {
    "nodes": [
        {"id": "1", "type": "state", "data": {"label": "balance"}},
        {"id": "2", "type": "operation", "data": {"op": "add", "a": "balance", "b": "balance"}},
    ],
    "edges": [{"from": "1", "to": "2"}]
}

async def main():
    agent = ChainChartAgent()
    result = await agent.run_workflow(diagram)
    print(result)

asyncio.run(main())
```

## Running Tests

```bash
python test_agent_execution.py
```

## Requirements

- Python 3.8+
- spoon-ai-sdk
- SpoonOS SDK for agent orchestration

## License

[Your License Here]

