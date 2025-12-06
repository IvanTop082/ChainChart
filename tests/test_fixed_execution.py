#!/usr/bin/env python
"""Quick test to verify the execution fix works"""
import json
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.chainchart_agent import ChainChartAgent

async def test():
    agent = ChainChartAgent()
    ui_diagram = json.loads(Path('tests/sample_chainchart.json').read_text())
    
    # Transform UI format to backend format (same as API does)
    from api_server import transform_ui_to_backend_format
    backend_diagram = transform_ui_to_backend_format(ui_diagram)
    
    result = await agent.run_workflow(backend_diagram)
    print('✅ Execution successful!')
    print(f'Steps: {len(result["execution_logs"])}')
    print(f'Final memory: {result["final_memory"]}')
    print('\nExecution logs:')
    for log in result['execution_logs']:
        print(f"  Step {log.get('step')}: {log.get('type')} - {log}")

if __name__ == "__main__":
    asyncio.run(test())

