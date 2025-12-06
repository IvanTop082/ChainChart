# 🧪 How to Test Workflows After Generating a Contract

## Understanding the Two SpoonOS Roles

Your system uses SpoonOS in **two different ways**:

### 1. **Contract Generation** (SpoonOS LLM)
- **What**: Generates C# smart contracts from diagrams
- **How**: Uses `ContractAgent` with SpoonOS LLM (OpenAI)
- **Output**: C# contract code → Compiled → Deployed to TestNet
- **Endpoint**: `POST /export-contract`

### 2. **Workflow Execution** (SpoonOS Tools)
- **What**: Executes workflows that interact with deployed contracts
- **How**: Uses `ChainChartAgent` with SpoonOS tools
- **Output**: Execution logs, memory state, results
- **Endpoint**: `POST /execute-chainchart`

## 🔄 Complete Flow

```
┌─────────────────────────────────────────────────────────┐
│ STEP 1: Generate & Deploy Contract                    │
└─────────────────────────────────────────────────────────┘
   UI Diagram (Counter, Increment, etc.)
        ↓
   SpoonOS LLM (ContractAgent)
        ↓
   C# Contract Generated
        ↓
   Compile → Deploy to TestNet
        ↓
   Contract Hash: 0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab

┌─────────────────────────────────────────────────────────┐
│ STEP 2: Create Workflow Diagram                        │
└─────────────────────────────────────────────────────────┘
   New Diagram with:
   - Function Node: "Counter" (calls contract method)
   - Function Node: "Increment" (calls contract method)
   - Operation Node: Add 1
   - Event Node: "CounterUpdated"

┌─────────────────────────────────────────────────────────┐
│ STEP 3: Execute Workflow                               │
└─────────────────────────────────────────────────────────┘
   Workflow Diagram
        ↓
   SpoonOS Tools (ChainChartAgent)
        ↓
   CallNeoContractTool → Calls deployed contract
        ↓
   Execution Results
```

## 📝 Step-by-Step: Testing a Workflow

### Step 1: Generate and Deploy Contract (Already Done ✅)

You've already:
- Generated a contract with `Counter()`, `Increment()`, `Newfunction()`
- Deployed it to TestNet
- Contract hash: `0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab`

### Step 2: Create a Workflow Diagram

Create a **new diagram** in the UI that **calls** your deployed contract:

**Example Workflow:**
```
1. Function Node: "Counter"
   - Tool: call_neo_contract
   - Method: "Counter"
   - Args: []

2. Operation Node: "Add 1"
   - Op: add
   - Operand A: (result from Counter)
   - Operand B: 1

3. Function Node: "Increment"
   - Tool: call_neo_contract
   - Method: "Increment"
   - Args: []

4. Event Node: "CounterIncremented"
```

### Step 3: Execute the Workflow

**Option A: Via UI**
1. Click "Execute" button in the UI
2. UI sends diagram to `POST /execute-chainchart`
3. Backend executes using `ChainChartAgent`
4. Results displayed in UI

**Option B: Via API**
```bash
POST http://localhost:8000/execute-chainchart
{
  "nodes": [
    {
      "id": "func1",
      "type": "function",
      "label": "Get Counter",
      "metadata": {
        "tool": "call_neo_contract",
        "params": {
          "method": "Counter",
          "args": []
        }
      }
    },
    {
      "id": "func2",
      "type": "function",
      "label": "Increment",
      "metadata": {
        "tool": "call_neo_contract",
        "params": {
          "method": "Increment",
          "args": []
        }
      }
    }
  ],
  "edges": [
    {"from": "func1", "to": "func2"}
  ]
}
```

## 🔧 How It Works Internally

### When You Execute a Workflow:

1. **ChainChartAgent** receives the diagram
2. **Builds FlowGraph** from nodes and edges
3. **Executes nodes sequentially**:
   - **Function Node** → Uses `CallNeoContractTool`
     - Connects to Neo TestNet RPC
     - Calls your deployed contract
     - Returns result
   - **Operation Node** → Uses `OperationTool`
     - Performs arithmetic/logic
     - Stores result in memory
   - **State Node** → Uses `ReadNeoStateTool`
     - Reads from contract storage
   - **Event Node** → Uses `DebugLogTool`
     - Logs the event

4. **Returns execution results**:
   - `execution_logs`: Step-by-step execution
   - `final_memory`: Final memory state
   - `success`: Whether execution completed

## 🧪 Example: Testing Your Counter Contract

### Workflow Diagram:
```json
{
  "nodes": [
    {
      "id": "1",
      "type": "function",
      "data": {
        "name": "Counter",
        "params": []
      }
    },
    {
      "id": "2",
      "type": "function",
      "data": {
        "name": "Increment",
        "params": []
      }
    },
    {
      "id": "3",
      "type": "function",
      "data": {
        "name": "Counter",
        "params": []
      }
    }
  ],
  "edges": [
    {"from": "1", "to": "2"},
    {"from": "2", "to": "3"}
  ]
}
```

### What Happens:
1. **Step 1**: Calls `Counter()` → Returns `0`
2. **Step 2**: Calls `Increment()` → Increments counter, calls `Newfunction()`, emits `NewEvent`
3. **Step 3**: Calls `Counter()` again → Returns `1`

### Expected Result:
```json
{
  "execution_logs": [
    {
      "step": 1,
      "node": "1",
      "type": "function",
      "method": "Counter",
      "result": {"status": "success", "result": [0]}
    },
    {
      "step": 2,
      "node": "2",
      "type": "function",
      "method": "Increment",
      "result": {"status": "success"}
    },
    {
      "step": 3,
      "node": "3",
      "type": "function",
      "method": "Counter",
      "result": {"status": "success", "result": [1]}
    }
  ],
  "final_memory": {},
  "success": true
}
```

## 🎯 Quick Test Script

Create `test_workflow.py`:

```python
import asyncio
import requests

# Your deployed contract hash
CONTRACT_HASH = "0x305e80b49c9bc8a1ea7a4aea99c7ff95074131ab"

# Workflow that tests the contract
workflow = {
    "nodes": [
        {
            "id": "1",
            "type": "function",
            "data": {"name": "Counter", "params": []}
        },
        {
            "id": "2",
            "type": "function",
            "data": {"name": "Increment", "params": []}
        },
        {
            "id": "3",
            "type": "function",
            "data": {"name": "Counter", "params": []}
        }
    ],
    "edges": [
        {"from": "1", "to": "2"},
        {"from": "2", "to": "3"}
    ]
}

# Execute workflow
response = requests.post(
    "http://localhost:8000/execute-chainchart",
    json=workflow
)

print("Execution Results:")
print(response.json())
```

## ✅ Summary

1. **Generate Contract**: SpoonOS LLM creates C# contract → Deploy
2. **Create Workflow**: New diagram that calls deployed contract methods
3. **Execute Workflow**: SpoonOS tools execute → Call real contract on TestNet
4. **View Results**: See execution logs and results

**The key**: Workflows are **separate diagrams** that **call** your deployed contracts!

