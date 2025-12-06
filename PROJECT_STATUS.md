# ChainChart Project Status: UI Data → SpoonOS → Smart Contract

## Current Architecture Overview

The project has **two separate systems** that process UI diagram data:

1. **Workflow Execution System** (`ChainChartAgent`) - Executes diagrams using SpoonOS
2. **Contract Generation System** - Generates C# smart contracts from diagrams

---

## 1. UI Data Format

The frontend sends diagram data in this format:

```typescript
{
  nodes: [
    {
      id: "node1",
      type: "state" | "function" | "event" | "operation" | "condition" | "modifier",
      label: "VariableName",
      value: "optional value",
      position: { x, y },
      metadata: {
        // Type-specific metadata
        expression: "...",  // For conditions
        params: [...],      // For functions
        operand_a: "...",  // For operations
        operand_b: "...",
        op: "add" | "sub" | ...
      }
    }
  ],
  edges: [
    {
      from: "nodeId:position",  // e.g., "node1:output"
      to: "nodeId:position"      // e.g., "node2:input"
    }
  ]
}
```

---

## 2. Data Transformation

**File**: `api_server.py` → `transform_ui_to_backend_format()`

This function converts UI format to backend format:

### UI Format → Backend Format

| UI Field | Backend Field | Transformation |
|----------|---------------|----------------|
| `node.type` | `node.type` | Direct mapping |
| `node.label` | `node.data.label` or `node.data.name` | Type-dependent |
| `node.value` | `node.data.*` | Parsed based on type |
| `node.metadata.*` | `node.data.*` | Extracted and mapped |
| `edge.from: "nodeId:position"` | `edge.from: "nodeId"` | Position stripped |
| `edge.to: "nodeId:position"` | `edge.to: "nodeId"` | Position stripped |

### Node Type Transformations

- **State**: `label` → `data.label` (storage key name)
- **Function**: `label` → `data.name`, `metadata.params` → `data.params`
- **Event**: `label` → `data.name`
- **Operation**: `metadata.op` → `data.op`, `metadata.operand_a/b` → `data.a/b`
- **Condition**: `metadata.expression` → `data.expression`
- **Modifier**: `label` → `data.name`, `metadata.expression` → `data.expression`

---

## 3. Workflow Execution System (SpoonOS)

**Endpoint**: `POST /execute-chainchart`

**Flow**:
```
UI Diagram (JSON)
  ↓
transform_ui_to_backend_format()
  ↓
ChainChartAgent.run_workflow()
  ↓
build_flowgraph() → FlowGraph
  ↓
Execute nodes sequentially using:
  - ReadNeoStateTool (reads from blockchain)
  - CallNeoContractTool (calls contract methods)
  - OperationTool (performs arithmetic/logic)
  - DebugLogTool (logs events)
  ↓
Returns: execution_logs, final_memory, debug_info
```

**Key Files**:
- `agent/chainchart_agent.py` - Main agent orchestrator
- `agent/flowgraph.py` - Graph data structure
- `agent/chainchart_executor.py` - Node execution logic
- `agent/chainchart_tools.py` - SpoonOS tools

**Status**: ✅ **WORKING** - Executes workflows and calls Neo blockchain

---

## 4. Contract Generation System

There are **TWO different contract generation approaches**:

### A. LLM-Based Generation (ContractAgent)

**Endpoint**: `POST /generate-contract`

**Flow**:
```
UI Diagram (JSON)
  ↓
transform_ui_to_backend_format()
  ↓
ContractAgent.generate_contract()
  ↓
ContractGenerateTool.execute() → Extract structure
  ↓
LLM (OpenAI GPT-4) → Generate C# code
  ↓
Returns: contract_text (C# code)
```

**Key Files**:
- `agent/contract_agent.py` - LLM-based generator
- `agent/tools/contract_generate_tool.py` - Structure extractor

**Status**: ⚠️ **PARTIALLY WORKING** - Uses LLM, may have API key issues

### B. Deterministic Generation (generate_contract_from_diagram)

**Endpoints**: `POST /export-contract`, `POST /compile-contract`

**Flow**:
```
UI Diagram (JSON)
  ↓
transform_ui_to_backend_format()
  ↓
generate_contract_from_diagram()
  ↓
Parse nodes → Generate:
  - Storage variables (from state nodes)
  - Functions (from function nodes)
  - Events (from event nodes)
  - Modifiers (from modifier nodes)
  - Logic (from operation/condition nodes)
  ↓
Returns: Complete C# contract code
```

**Key Files**:
- `generator/neo_contract_generator.py` - Deterministic generator
- `generator/contract_validator.py` - Validates and patches code

**Status**: ✅ **WORKING** - Currently used for export/compile endpoints

---

## 5. Current Status Summary

### ✅ What's Working

1. **UI → Backend Transformation**: `transform_ui_to_backend_format()` correctly converts UI format
2. **Workflow Execution**: `ChainChartAgent` executes diagrams using SpoonOS tools
3. **Deterministic Contract Generation**: `generate_contract_from_diagram()` generates C# contracts
4. **Contract Compilation**: Neo compiler integration works
5. **Contract Deployment**: Can deploy to Neo N3 TestNet

### ⚠️ What Needs Clarification

1. **Dual Generation Systems**: 
   - `/generate-contract` uses LLM-based `ContractAgent`
   - `/export-contract` uses deterministic `generate_contract_from_diagram()`
   - **Question**: Should we use one or both? Which is preferred?

2. **SpoonOS Integration for Contract Generation**:
   - `ContractAgent` uses SpoonOS LLM but may not be actively used
   - Main export uses deterministic generator (no SpoonOS)
   - **Question**: Should contract generation use SpoonOS or stay deterministic?

3. **Data Flow Completeness**:
   - UI data → Backend transformation ✅
   - Backend → SpoonOS execution ✅
   - Backend → Contract generation ✅
   - **Question**: Is the graph structure fully utilized in contract generation?

---

## 6. Data Flow Diagram

```
┌─────────────────┐
│   UI Diagram    │
│  (nodes, edges) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ transform_ui_to_       │
│ backend_format()        │
└────────┬────────────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────────┐
│ ChainChartAgent │  │ Contract Generation │
│ (Execution)    │  │                     │
│                 │  │ Option A:           │
│ - FlowGraph     │  │ ContractAgent       │
│ - Execute nodes │  │ (LLM-based)         │
│ - SpoonOS tools │  │                     │
│                 │  │ Option B:           │
│ Returns:        │  │ generate_contract_ │
│ - logs          │  │ from_diagram()     │
│ - memory        │  │ (Deterministic)    │
└─────────────────┘  └──────────┬──────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │ C# Contract  │
                        │ Code         │
                        └───────┬───────┘
                                │
                                ▼
                        ┌───────────────┐
                        │ Compile       │
                        │ (NEF +        │
                        │  Manifest)    │
                        └───────┬───────┘
                                │
                                ▼
                        ┌───────────────┐
                        │ Deploy to     │
                        │ Neo TestNet   │
                        └───────────────┘
```

---

## 7. Recommendations

### Option 1: Keep Both Systems
- Use **deterministic generator** for production (reliable, fast)
- Keep **LLM generator** for experimentation/future use

### Option 2: Consolidate to Deterministic
- Remove `ContractAgent` and LLM-based generation
- Use only `generate_contract_from_diagram()` for all contract generation
- Simpler, more predictable

### Option 3: Enhance Deterministic with SpoonOS
- Keep deterministic generation
- Use SpoonOS tools to enhance contract generation (e.g., better logic parsing)
- Best of both worlds

---

## 8. Next Steps

1. **Clarify contract generation approach**: Choose one or document both
2. **Verify graph structure usage**: Ensure edges/control flow are fully utilized
3. **Test end-to-end flow**: UI → Transform → Generate → Compile → Deploy
4. **Document node type mappings**: Complete mapping of UI node types to C# contract elements

---

## Questions to Answer

1. **Should contract generation use SpoonOS LLM or stay deterministic?**
2. **Are graph edges fully utilized in contract generation?** (Currently mainly uses nodes)
3. **Should we keep both generation systems or consolidate?**
4. **How should control flow (edges) be represented in the generated contract?**
