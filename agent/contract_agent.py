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
            # Use LLM directly to generate contract (not the agent, which may return intermediate steps)
            # Build full prompt with structure details
            full_prompt = prompt + "\n\nStructure JSON:\n" + json.dumps(structure, indent=2)
            
            # Call agent.run() - it was working before, but may return intermediate steps
            # We'll filter those out in the extraction logic
            response = await self.agent.run(full_prompt)
            
            # Extract code from response (may be wrapped in ```csharp``` or ```cs```)
            response_str = str(response)
            print(f"\n{'='*80}")
            print("🔍 LLM RESPONSE DEBUG:")
            print(f"{'='*80}")
            print(f"Response type: {type(response)}")
            print(f"Response length: {len(response_str)} characters")
            print(f"\nFirst 500 characters:")
            print(response_str[:500])
            print(f"\nLast 500 characters:")
            print(response_str[-500:] if len(response_str) > 500 else response_str)
            print(f"{'='*80}\n")
            
            contract_code = self._extract_code_from_response(response_str)
            
            print(f"\n{'='*80}")
            print("🔍 EXTRACTED CODE DEBUG:")
            print(f"{'='*80}")
            print(f"Extracted length: {len(contract_code)} characters")
            print(f"Has namespace: {'namespace' in contract_code}")
            print(f"Has class: {'class' in contract_code}")
            print(f"Has SmartContract: {'SmartContract' in contract_code}")
            if contract_code:
                print(f"\nFirst 300 characters of extracted code:")
                print(contract_code[:300])
            print(f"{'='*80}\n")
            
            # If extraction failed (empty or invalid), use fallback
            # Check for valid C# code: must have class and SmartContract, namespace is optional
            has_valid_structure = (
                contract_code and 
                contract_code.strip() and 
                "class" in contract_code and 
                "SmartContract" in contract_code
            )
            
            if not has_valid_structure:
                print("⚠️ LLM response did not contain valid C# code structure (missing class or SmartContract), using fallback contract generator")
                return self._generate_fallback_contract(structure)
            
            # ALWAYS ensure namespace is ChainChartGenerated (replace any existing namespace)
            import re
            namespace_match = re.search(r'namespace\s+(\w+)', contract_code)
            if namespace_match:
                existing_namespace = namespace_match.group(1)
                if existing_namespace != "ChainChartGenerated":
                    print(f"⚠️ Replacing namespace '{existing_namespace}' with 'ChainChartGenerated'")
                    contract_code = re.sub(
                        r'namespace\s+\w+',
                        'namespace ChainChartGenerated',
                        contract_code
                    )
            else:
                print("⚠️ LLM response missing namespace, wrapping in ChainChartGenerated namespace")
                # Find where to insert namespace (after using statements)
                if 'using' in contract_code:
                    # Find the end of the last using statement
                    using_lines = [line for line in contract_code.split('\n') if line.strip().startswith('using')]
                    if using_lines:
                        last_using_idx = contract_code.rfind(using_lines[-1])
                        next_line = contract_code.find('\n', last_using_idx)
                        if next_line >= 0:
                            contract_code = (
                                contract_code[:next_line+1] +
                                '\nnamespace ChainChartGenerated\n{\n' +
                                contract_code[next_line+1:] +
                                '\n}'
                            )
                        else:
                            contract_code = f"namespace ChainChartGenerated\n{{\n{contract_code}\n}}"
                    else:
                        contract_code = f"namespace ChainChartGenerated\n{{\n{contract_code}\n}}"
                else:
                    contract_code = f"namespace ChainChartGenerated\n{{\n{contract_code}\n}}"
            
            # Ensure contract has a unique name to avoid "Contract already exists" errors
            contract_code = self._ensure_unique_contract_name(contract_code)
            
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

1. **CRITICAL: Generate a UNIQUE contract class name** - Use a descriptive name based on the diagram's purpose (e.g., "CounterContract", "TokenContract", "VotingContract") followed by a timestamp or unique identifier to ensure uniqueness. Example: "CounterContract_20250612" or "TokenContract_1734567890"
2. Use Neo N3 C# contract template
3. **CRITICAL: Include ALL required using statements at the top:**
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
15. **CRITICAL: StorageMap prefix + key usage**
    - When you create `StorageMap CounterMap = new StorageMap(Storage.CurrentContext, "counter")`, the prefix is "counter"
    - To access the value, use `ByteString.Empty` as the key, NOT the prefix again
    - WRONG: `CounterMap.Get("counter")` - This creates storage key "countercounter" which is incorrect
    - CORRECT: `CounterMap.Get(ByteString.Empty)` - This creates storage key "counter" which is correct
    - WRONG: `CounterMap.Put("counter", value)` - This stores at "countercounter"
    - CORRECT: `CounterMap.Put(ByteString.Empty, value)` - This stores at "counter"
    - Example for counter contract:
      ```csharp
      private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "counter");
      
      public static void increment()
      {
          ByteString value = CounterMap.Get(ByteString.Empty);  // ✅ Correct
          BigInteger counter = value is null ? 0 : (BigInteger)value;
          counter = counter + 1;
          CounterMap.Put(ByteString.Empty, counter);  // ✅ Correct
      }
      ```
16. Follow Neo N3 best practices

## Edge-Based Logic Construction:

- If an edge goes from Function → Operation: Operation belongs in that function
- If an edge goes from Operation → Operation: Second operation uses result of first
- If an edge goes from Condition → Operation: Operation is in the true/false branch
- If an edge goes from Operation → Event: Emit event after operation completes
- If an edge goes from Function → Condition: Condition is checked at start of function

## Important:
- **CRITICAL: Return ONLY the C# code, nothing else**
- **DO NOT include any explanations, questions, or conversational text**
- **DO NOT say "Thank you", "Let me", "I will", or ask for confirmation**
- Wrap code in triple backticks: ```csharp
- If you cannot generate code, return an empty response
- Ensure code is valid, compilable Neo N3 contract
- Use proper Neo storage patterns (StorageMap, StorageContext)
- **The edges define the actual function logic - use them!**

**Generate the complete contract code now (code only, no explanations):**
"""
        return prompt
    
    def _ensure_unique_contract_name(self, contract_code: str) -> str:
        """Ensure contract class name is ALWAYS unique by adding timestamp + random"""
        import re
        import time
        import random
        
        # Find the class name in the contract
        class_match = re.search(r'public\s+class\s+(\w+)\s*:\s*SmartContract', contract_code)
        if not class_match:
            # If no class found, try to find any class declaration
            class_match = re.search(r'class\s+(\w+)\s*:\s*SmartContract', contract_code)
        
        if class_match:
            original_name = class_match.group(1)
            
            # ALWAYS add a unique identifier (timestamp + random) to ensure uniqueness
            # This ensures every contract gets a different name, even if code is identical
            timestamp = str(int(time.time() * 1000))  # Use milliseconds for better precision
            random_suffix = str(random.randint(1000, 9999))  # Add random 4-digit number
            unique_id = f"{timestamp}_{random_suffix}"
            
            # Extract base name (remove any existing timestamp)
            base_name = re.sub(r'_\d+(_\d+)?$', '', original_name)
            if not base_name:
                base_name = original_name
            
            new_name = f"{base_name}_{unique_id}"
            
            # Replace class name (handle both with and without "public")
            contract_code = re.sub(
                rf'\bclass\s+{re.escape(original_name)}\b',
                f'class {new_name}',
                contract_code
            )
            contract_code = re.sub(
                rf'\bpublic\s+class\s+{re.escape(original_name)}\b',
                f'public class {new_name}',
                contract_code
            )
            
            # ALWAYS ensure namespace is ChainChartGenerated (replace any existing namespace)
            # Use a more robust pattern that handles namespaces with underscores and numbers
            namespace_match = re.search(r'namespace\s+([\w_]+)', contract_code)
            if namespace_match:
                existing_namespace = namespace_match.group(1)
                if existing_namespace != "ChainChartGenerated":
                    # Replace the namespace with ChainChartGenerated (match the full namespace declaration)
                    contract_code = re.sub(
                        r'namespace\s+[\w_]+',
                        'namespace ChainChartGenerated',
                        contract_code
                    )
            else:
                # No namespace found, wrap the code in ChainChartGenerated namespace
                # Find the first using statement or class declaration
                if 'using' in contract_code:
                    # Insert namespace after using statements
                    using_end = contract_code.rfind('using')
                    if using_end >= 0:
                        # Find the end of the last using statement
                        next_line = contract_code.find('\n', using_end)
                        if next_line >= 0:
                            contract_code = (
                                contract_code[:next_line+1] +
                                '\nnamespace ChainChartGenerated\n{\n' +
                                contract_code[next_line+1:] +
                                '\n}'
                            )
                else:
                    # No using statements, wrap entire code
                    contract_code = f"namespace ChainChartGenerated\n{{\n{contract_code}\n}}"
            
            # Update ManifestExtra name if present
            contract_code = re.sub(
                r'(\[ManifestExtra\("name",\s*")' + re.escape(original_name) + r'("\)\])',
                r'\1' + new_name + r'\2',
                contract_code,
                flags=re.IGNORECASE
            )
        else:
            # No class found - add a default unique contract
            import time
            import random
            timestamp = str(int(time.time() * 1000))
            random_suffix = str(random.randint(1000, 9999))
            unique_id = f"{timestamp}_{random_suffix}"
            default_name = f"Contract_{unique_id}"
            
            # Try to inject a class if none exists (shouldn't happen, but just in case)
            if "class" not in contract_code and "namespace" in contract_code:
                # Add a basic class
                contract_code = contract_code.replace(
                    "namespace ChainChartGenerated",
                    f"namespace ChainChartGenerated\n{{\n    public class {default_name} : SmartContract\n    {{\n        // Contract code\n    }}\n}}"
                )
        
        return contract_code
    
    def _extract_code_from_response(self, response: Any) -> str:
        """Extract C# code from LLM response, filtering out intermediate reasoning steps"""
        import re
        response_str = str(response)
        
        # Filter out common intermediate reasoning patterns from ReAct agents
        # These patterns indicate intermediate steps, not final code
        intermediate_patterns = [
            r"Step \d+:\s*Thinking completed",
            r"Step \d+:\s*No action needed",
            r"Task finished",
            r"^Thinking:",
            r"^Action:",
            r"^Observation:",
        ]
        
        for pattern in intermediate_patterns:
            if re.search(pattern, response_str, re.IGNORECASE | re.MULTILINE):
                print(f"   ⚠️ Detected intermediate reasoning pattern: {pattern}")
                # Try to find code blocks after the intermediate text
                # Look for the last code block in the response
                code_blocks = re.findall(r'```(?:csharp|cs)?\s*\n(.*?)```', response_str, re.DOTALL)
                if code_blocks:
                    print(f"   ✅ Found {len(code_blocks)} code block(s) after intermediate text, using last one")
                    return code_blocks[-1].strip()
                # If no code blocks, continue with normal extraction
        
        print(f"🔍 Code extraction: Looking for code blocks...")
        print(f"   Has ```csharp: {'```csharp' in response_str}")
        print(f"   Has ```cs: {'```cs' in response_str}")
        print(f"   Has ```: {'```' in response_str}")
        print(f"   Has namespace: {'namespace' in response_str}")
        print(f"   Has using: {'using' in response_str}")
        
        # Try to extract code from markdown code blocks
        if "```csharp" in response_str:
            print("   ✅ Found ```csharp block")
            start = response_str.find("```csharp") + len("```csharp")
            end = response_str.find("```", start)
            if end > start:
                extracted = response_str[start:end].strip()
                print(f"   ✅ Extracted {len(extracted)} characters from ```csharp block")
                return extracted
            else:
                print("   ❌ ```csharp block found but no closing ```")
        elif "```cs" in response_str:
            print("   ✅ Found ```cs block")
            start = response_str.find("```cs") + len("```cs")
            end = response_str.find("```", start)
            if end > start:
                extracted = response_str[start:end].strip()
                print(f"   ✅ Extracted {len(extracted)} characters from ```cs block")
                return extracted
            else:
                print("   ❌ ```cs block found but no closing ```")
        elif "```" in response_str:
            print("   ✅ Found generic ``` block")
            start = response_str.find("```") + 3
            end = response_str.find("```", start)
            if end > start:
                extracted = response_str[start:end].strip()
                print(f"   ✅ Extracted {len(extracted)} characters from generic ``` block")
                return extracted
            else:
                print("   ❌ ``` block found but no closing ```")
        
        # If no code blocks, try to find C# code patterns
        # Look for namespace or using statements (indicates C# code)
        if "namespace" in response_str or "using" in response_str:
            print("   ✅ Found namespace or using statements, attempting extraction...")
            # Try to extract complete contract - from first "using" to matching closing braces
            using_start = response_str.find("using")
            if using_start >= 0:
                print(f"   Found 'using' at position {using_start}")
                # Find all opening and closing braces to match them properly
                brace_count = 0
                start_idx = using_start
                last_brace_idx = -1
                
                # Find the first opening brace after "using" statements
                for i in range(using_start, len(response_str)):
                    if response_str[i] == '{':
                        if brace_count == 0:
                            start_idx = using_start  # Start from first "using"
                        brace_count += 1
                    elif response_str[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_brace_idx = i
                            break
                
                if last_brace_idx > using_start:
                    extracted = response_str[using_start:last_brace_idx + 1].strip()
                    print(f"   ✅ Extracted {len(extracted)} characters using brace matching")
                    # Verify it looks like valid C# code
                    if "class" in extracted and "SmartContract" in extracted:
                        print(f"   ✅ Extracted code contains 'class' and 'SmartContract'")
                        return extracted
                    else:
                        print(f"   ⚠️ Extracted code missing 'class' or 'SmartContract'")
                        print(f"      Has 'class': {'class' in extracted}")
                        print(f"      Has 'SmartContract': {'SmartContract' in extracted}")
                else:
                    print(f"   ❌ Could not find matching braces (last_brace_idx: {last_brace_idx}, using_start: {using_start})")
            
            # Fallback: Try to extract code between namespace and closing brace
            namespace_match = re.search(r'(namespace\s+\w+\s*\{[\s\S]*?\})', response_str, re.MULTILINE | re.DOTALL)
            if namespace_match:
                extracted = namespace_match.group(1).strip()
                print(f"   ✅ Extracted {len(extracted)} characters using namespace regex")
                
                # Check for conversational phrases BEFORE returning (Bug 3 fix)
                conversational_phrases = ["thank you", "please confirm", "let me", "i will", "could you",
                                          "proceed step by step", "if yes", "if you want"]
                found_phrases = [phrase for phrase in conversational_phrases if phrase in response_str.lower()]
                if found_phrases:
                    print(f"   ⚠️ Detected conversational phrases in response: {found_phrases}")
                    print("   ❌ Returning empty string to trigger fallback (invalid LLM response)")
                    return ""  # Empty string will trigger fallback contract generation
                
                # Validate extracted code contains essential elements
                if "class" in extracted and "SmartContract" in extracted:
                    print(f"   ✅ Extracted code contains 'class' and 'SmartContract'")
                    return extracted
                elif "class" in extracted:
                    print(f"   ⚠️ Extracted code contains 'class' but missing 'SmartContract'")
                    # Still return it, but log warning
                    return extracted
                else:
                    print(f"   ⚠️ Extracted code missing 'class'")
        
        # If still no code found, the LLM might have given a conversational response
        # Return empty string to trigger fallback
        conversational_phrases = ["thank you", "please confirm", "let me", "i will", "could you",
                                  "proceed step by step", "if yes", "if you want"]
        found_phrases = [phrase for phrase in conversational_phrases if phrase in response_str.lower()]
        if found_phrases:
            print(f"   ⚠️ Detected conversational phrases: {found_phrases}")
            print("   ❌ Returning empty string to trigger fallback")
            return ""  # Empty string will trigger fallback contract generation
        
        # Last resort: return response as-is (might be valid code without code blocks)
        print(f"   ⚠️ No code blocks found, returning response as-is ({len(response_str)} chars)")
        return response_str.strip()
    
    def _generate_fallback_contract(self, structure: Dict[str, Any]) -> str:
        """Generate basic contract structure if LLM fails"""
        import time
        import random
        # Use milliseconds + random for better uniqueness
        timestamp = str(int(time.time() * 1000))
        random_suffix = str(random.randint(1000, 9999))
        contract_name = f"ChainChartContract_{timestamp}_{random_suffix}"
        
        contract = f"""using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

namespace ChainChartGenerated
{{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Generated from ChainChart diagram (fallback)")]
    public class {contract_name} : SmartContract
    {{
"""
        
        # Add storage variables
        for var in structure.get("variables", []):
            var_name = var['name']
            # Sanitize variable name for C# identifier
            var_name_safe = var_name.replace(' ', '_').replace('-', '_')
            contract += f"        private static readonly StorageMap {var_name_safe}Map = new StorageMap(Storage.CurrentContext, \"{var_name}\");\n"
        
        # Add events
        for event in structure.get("events", []):
            event_name = event['name']
            params_str = event.get('parameters', '') or ''
            # Use Action without parameters if params_str is empty
            if params_str:
                contract += f"        public static event Action<{params_str}> {event_name};\n\n"
            else:
                contract += f"        public static event Action {event_name};\n\n"
        
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

