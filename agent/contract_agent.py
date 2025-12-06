"""
ContractAgent - LLM-assisted Neo N3 smart contract generation
Uses OpenAI GPT-4 to generate C# contract code from ChainChart structure
"""

import os
import json
from typing import Dict, Any
from spoon_ai.agents import SpoonReactAI
from spoon_ai.chat import ChatBot

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables directly

from .tools.contract_generate_tool import ContractGenerateTool


class ContractAgent:
    """
    Phase 3 Contract Generation Agent:
    - Extracts structure from ChainChart diagram
    - Uses LLM to generate Neo N3 C# contract code
    - Returns complete contract source code
    """
    
    def __init__(self):
        # Initialize LLM for contract generation
        self.llm = ChatBot(
            llm_provider=os.getenv("LLM_PROVIDER") or "openai",
            model_name=os.getenv("LLM_MODEL") or "gpt-4.1",
            temperature=0.2
        )
        
        # Initialize agent with contract generation tool
        self.agent = SpoonReactAI(
            llm=self.llm,
            tools=[ContractGenerateTool()]
        )
        
        # Create tool registry for direct access
        self.tool_registry = {
            "generate_contract_structure": ContractGenerateTool()
        }
    
    async def generate_contract(self, diagram_json: Dict[str, Any]) -> str:
        """
        Generate complete Neo N3 smart contract in C# from ChainChart diagram.
        
        Steps:
        1. Extract structure using ContractGenerateTool
        2. Build LLM prompt with structure and instructions
        3. Generate C# contract code
        4. Return contract text
        
        Args:
            diagram_json: ChainChart diagram with nodes and edges
            
        Returns:
            Complete C# contract code as string
        """
        # Step 1: Extract structure from diagram
        structure_tool = self.tool_registry["generate_contract_structure"]
        structure = await structure_tool.execute(diagram=diagram_json)
        
        # Step 2: Build comprehensive LLM prompt
        prompt = self._build_contract_prompt(structure)
        
        # Step 3: Generate contract code using LLM
        try:
            # Use LLM directly to generate contract
            # Build full prompt with structure details
            full_prompt = prompt + "\n\nStructure JSON:\n" + json.dumps(structure, indent=2)
            
            # Call LLM - use the agent's run method or direct LLM call
            # Try using agent.run() which should handle the LLM call
            messages = [{"role": "user", "content": full_prompt}]
            response = await self.agent.run(full_prompt)
            
            # Extract code from response (may be wrapped in ```csharp``` or ```cs```)
            contract_code = self._extract_code_from_response(str(response))
            
            return contract_code
            
        except Exception as e:
            # Fallback: Generate basic contract structure
            import traceback
            print(f"LLM generation failed: {e}")
            print(traceback.format_exc())
            return self._generate_fallback_contract(structure)
    
    def _build_contract_prompt(self, structure: Dict[str, Any]) -> str:
        """Build detailed prompt for LLM contract generation with full edge utilization"""
        
        prompt = f"""Generate a complete Neo N3 smart contract in **C#** from this ChainChart diagram.

## Contract Structure:

### Storage Variables:
"""
        
        for var in structure.get("variables", []):
            prompt += f"- {var['name']} ({var['type']}, {var['visibility']})\n"
        
        prompt += "\n### Functions:\n"
        for func in structure.get("functions", []):
            params_str = ", ".join(func.get("parameters", [])) if func.get("parameters") else ""
            payable_str = " payable" if func.get("payable") else ""
            prompt += f"- {func['visibility']}{payable_str} static void {func['name']}({params_str})\n"
        
        prompt += "\n### Events:\n"
        for event in structure.get("events", []):
            prompt += f"- event {event['name']}({event.get('parameters', '')})\n"
        
        prompt += "\n### Conditions:\n"
        for cond in structure.get("conditions", []):
            prompt += f"- Condition ID {cond['id']}: if ({cond['expression']})\n"
        
        prompt += "\n### Operations:\n"
        for op in structure.get("operations", []):
            prompt += f"- Operation ID {op['id']}: {op['operand_a']} {op['operation']} {op.get('operand_b', '')}\n"
        
        # CRITICAL: Include edge information for control flow
        edges = structure.get("edges", [])
        if edges:
            prompt += "\n### Control Flow (Edges):\n"
            prompt += "The edges define the execution flow and function logic. Use them to:\n"
            prompt += "1. Determine which operations/conditions belong to which functions\n"
            prompt += "2. Understand the order of operations within functions\n"
            prompt += "3. Implement conditional branching (if/else) based on condition nodes\n"
            prompt += "4. Connect operations to their results and subsequent operations\n\n"
            
            # Group edges by function (if function nodes exist)
            functions = structure.get("functions", [])
            if functions:
                for func in functions:
                    func_id = func['id']
                    func_edges = [e for e in edges if e.get("from") == func_id or e.get("to") == func_id]
                    if func_edges:
                        prompt += f"\nFunction '{func['name']}' (ID: {func_id}) flow:\n"
                        # Build execution path for this function
                        visited = set()
                        def trace_path(node_id, depth=0):
                            if node_id in visited or depth > 20:  # Prevent infinite loops
                                return ""
                            visited.add(node_id)
                            path_str = "  " * depth
                            
                            # Find node
                            all_nodes = structure.get("nodes", [])
                            node = next((n for n in all_nodes if n.get("id") == node_id), None)
                            if node:
                                node_type = node.get("type")
                                node_data = node.get("data", {})
                                
                                if node_type == "operation":
                                    path_str += f"→ Operation: {node_data.get('op', '')} on {node_data.get('a', '')} and {node_data.get('b', '')}\n"
                                elif node_type == "condition":
                                    path_str += f"→ Condition: if ({node_data.get('expression', '')})\n"
                                elif node_type == "event":
                                    path_str += f"→ Emit Event: {node_data.get('name', '')}\n"
                                elif node_type == "state":
                                    path_str += f"→ Read/Write State: {node_data.get('label', '')}\n"
                            
                            # Find outgoing edges
                            outgoing = [e for e in edges if e.get("from") == node_id]
                            for edge in outgoing:
                                next_node_id = edge.get("to")
                                path_str += trace_path(next_node_id, depth + 1)
                            
                            return path_str
                        
                        # Start tracing from function node
                        prompt += trace_path(func_id)
            
            # Also show all edges for reference
            prompt += "\n\nAll Edges (for reference):\n"
            for edge in edges:
                from_type = edge.get("from_type", "unknown")
                to_type = edge.get("to_type", "unknown")
                prompt += f"- {edge.get('from')} ({from_type}) → {edge.get('to')} ({to_type})\n"
        
        prompt += """
## Requirements:

1. Use Neo N3 C# contract template
2. **CRITICAL: Include ALL required using statements at the top:**
   ```
   using Neo;
   using Neo.SmartContract.Framework;
   using Neo.SmartContract.Framework.Services;
   using System;
   using System.Numerics;
   ```
   - `using System;` is REQUIRED for `Action` type used in events
   - `using Neo;` is REQUIRED for Neo types
   - `using Neo.SmartContract.Framework;` is REQUIRED for SmartContract base class
   - `using Neo.SmartContract.Framework.Services;` is REQUIRED for Storage, Runtime, etc.
   - `using System.Numerics;` is REQUIRED for BigInteger
3. **DO NOT use [DisplayName] attributes** - they are not available in Neo N3. Use [ManifestExtra] instead.
4. Create storage variables for all State nodes using StorageMap
5. Create public static methods for all Function nodes
6. **CRITICAL: Use the edge information to build function logic:**
   - Operations connected to a function should be inside that function
   - Conditions should create if/else blocks based on their edges
   - Follow the execution flow defined by edges
   - Operations should execute in the order defined by edge connections
7. Implement branching logic for Condition nodes (use edges to determine true/false paths)
8. Implement arithmetic/logic for Operation nodes in the correct order
9. Declare Neo events for all Event nodes using `public static event Action<...>` and emit them where edges indicate
10. Add owner modifier if any modifier nodes exist
11. Use BigInteger for numeric types
12. Use ByteString for byte arrays
13. **CRITICAL: Do NOT use .ToBigInteger() method** - it doesn't exist in Neo N3
    - Use direct cast instead: `(BigInteger)value`
    - Example: `var result = (BigInteger)storageValue;` NOT `var result = storageValue.ToBigInteger();`
    - When reading from storage: `var value = (BigInteger)storageMap.Get(key);`
14. **CRITICAL: Do NOT use null-coalescing operator (??) with ByteString**
    - `storageMap.Get(key)` returns `ByteString`, not `BigInteger`
    - WRONG: `var value = storageMap.Get(key) ?? 0;` (this causes compilation error)
    - CORRECT: `ByteString value = storageMap.Get(key); return value is null ? 0 : (BigInteger)value;`
    - Or: `var value = storageMap.Get(key); return value is null ? 0 : (BigInteger)value;`
    - Always use `is null` check with ternary operator, NOT `??` operator
15. Follow Neo N3 best practices

## Edge-Based Logic Construction:

- If an edge goes from Function → Operation: Operation belongs in that function
- If an edge goes from Operation → Operation: Second operation uses result of first
- If an edge goes from Condition → Operation: Operation is in the true/false branch
- If an edge goes from Operation → Event: Emit event after operation completes
- If an edge goes from Function → Condition: Condition is checked at start of function

## Important:
- Return ONLY the C# code
- Wrap code in triple backticks: ```csharp
- Do NOT include explanations or markdown outside code block
- Ensure code is valid, compilable Neo N3 contract
- Use proper Neo storage patterns (StorageMap, StorageContext)
- **The edges define the actual function logic - use them!**

Generate the complete contract now:
"""
        return prompt
    
    def _extract_code_from_response(self, response: Any) -> str:
        """Extract C# code from LLM response"""
        response_str = str(response)
        
        # Try to extract code from markdown code blocks
        if "```csharp" in response_str:
            start = response_str.find("```csharp") + len("```csharp")
            end = response_str.find("```", start)
            if end > start:
                return response_str[start:end].strip()
        elif "```cs" in response_str:
            start = response_str.find("```cs") + len("```cs")
            end = response_str.find("```", start)
            if end > start:
                return response_str[start:end].strip()
        elif "```" in response_str:
            start = response_str.find("```") + 3
            end = response_str.find("```", start)
            if end > start:
                return response_str[start:end].strip()
        
        # If no code blocks, return response as-is
        return response_str.strip()
    
    def _generate_fallback_contract(self, structure: Dict[str, Any]) -> str:
        """Generate basic contract structure if LLM fails"""
        contract = """using Neo;
using Neo.SmartContract;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System;

namespace ChainChartContract
{
    [DisplayName("ChainChartContract")]
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Generated from ChainChart diagram")]
    public class ChainChartContract : SmartContract
    {
"""
        
        # Add storage variables
        for var in structure.get("variables", []):
            var_name = var['name']
            contract += f"        private static StorageMap {var_name}Map => new StorageMap(Storage.CurrentContext, \"{var_name}\");\n"
        
        # Add events
        for event in structure.get("events", []):
            event_name = event['name']
            params_str = event.get('parameters', '') or ''
            contract += f"        [DisplayName(\"{event_name}\")]\n"
            contract += f"        public static event Action<{params_str}> {event_name};\n\n"
        
        # Add functions
        for func in structure.get("functions", []):
            func_name = func['name']
            params_str = ", ".join(func.get("parameters", [])) if func.get("parameters") else ""
            payable = " payable" if func.get("payable") else ""
            contract += f"        public static void {func_name}({params_str}){payable}\n"
            contract += "        {\n"
            contract += "            // TODO: Implement function logic\n"
            contract += "        }\n\n"
        
        contract += "    }\n}"
        return contract

