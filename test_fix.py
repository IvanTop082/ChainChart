"""Quick test to verify the params fix"""
import asyncio
from agent.tools.contract_generate_tool import ContractGenerateTool

async def test():
    tool = ContractGenerateTool()
    
    # Test with params as list (like in test_phase3.py)
    diagram = {
        "nodes": [
            {
                "id": "1",
                "type": "function",
                "data": {
                    "name": "transfer",
                    "params": ["BigInteger amount", "ByteString to"],  # List, not string
                    "visibility": "public"
                }
            }
        ],
        "edges": []
    }
    
    try:
        result = await tool.execute(diagram=diagram)
        print("✅ SUCCESS!")
        print(f"Functions found: {len(result.get('functions', []))}")
        if result.get('functions'):
            print(f"Function params: {result['functions'][0].get('parameters')}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

