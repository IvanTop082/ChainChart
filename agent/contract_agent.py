"""
ContractAgent - LLM-assisted Neo N3 smart contract generation
Uses OpenAI GPT-4 to generate C# contract code from ChainChart structure
"""

import os
import json
from typing import Dict, Any
from spoon_ai.agents import SpoonReactAI
from spoon_ai.chat import ChatBot

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
        """Build detailed prompt for LLM contract generation"""
        
        prompt = f"""Generate a complete Neo N3 smart contract in **C#**, following these specifications:

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
            prompt += f"- if ({cond['expression']})\n"
        
        prompt += "\n### Operations:\n"
        for op in structure.get("operations", []):
            prompt += f"- {op['operand_a']} {op['operation']} {op.get('operand_b', '')}\n"
        
        prompt += """
## Requirements:

1. Use Neo N3 C# contract template
2. Include proper using statements (Neo, Neo.SmartContract, Neo.SmartContract.Framework, etc.)
3. Create storage variables for all State nodes using StorageMap
4. Create public static methods for all Function nodes
5. Implement branching logic for Condition nodes
6. Implement arithmetic/logic for Operation nodes
7. Declare Neo events for all Event nodes
8. Add owner modifier if any modifier nodes exist
9. Include proper Neo contract attributes ([DisplayName], [ManifestExtra])
10. Use BigInteger for numeric types
11. Use ByteString for byte arrays
12. Follow Neo N3 best practices

## Important:
- Return ONLY the C# code
- Wrap code in triple backticks: ```csharp
- Do NOT include explanations or markdown outside code block
- Ensure code is valid, compilable Neo N3 contract
- Use proper Neo storage patterns (StorageMap, StorageContext)

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

