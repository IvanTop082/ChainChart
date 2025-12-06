# ChainChart UI + Backend Integration Guide

## Overview

This guide explains how the Phase 1 UI integrates with the Phase 2 SpoonOS backend agent for ChainChart workflow execution.

## Architecture

```
┌─────────────────┐         HTTP POST         ┌─────────────────┐
│   UI (Next.js)  │  ──────────────────────>  │  FastAPI Server │
│  Builder Page   │                            │  (Port 8000)    │
└─────────────────┘                            └─────────────────┘
                                                       │
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │ ChainChartAgent │
                                              │  (SpoonOS SDK)  │
                                              └─────────────────┘
```

## File Locations

### Backend Files
- **`api_server.py`** - FastAPI server with `/execute-chainchart` endpoint
- **`agent/chainchart_agent.py`** - ChainChartAgent class with `run_workflow()` method
- **`agent/chainchart_executor.py`** - Node execution logic
- **`agent/chainchart_tools.py`** - SpoonOS tools (mocked for now)

### Frontend Files
- **`ChainChart_ui/app/builder/page.tsx`** - Main builder page with Run button
- **`ChainChart_ui/components/DebugPanel.tsx`** - Debug panel component
- **`ChainChart_ui/lib/api.ts`** - API client functions

## Where JSON Export Happens

The JSON export is produced in **`ChainChart_ui/app/builder/page.tsx`** at line 103-112:

```typescript
const serializeDiagram = () => {
  const data = JSON.stringify({ nodes, edges }, null, 2);
  // Download as file
  const blob = new Blob([data], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${projectName || 'chainchart_logic'}_${Date.now()}.json`;
  a.click();
};
```

## API Integration Point

The **`runChainChart()`** function is called from the builder page:

**Location**: `ChainChart_ui/lib/api.ts`

```typescript
export async function runChainChart(diagram: DiagramData): Promise<ExecutionResponse> {
  const response = await fetch(`${API_BASE_URL}/execute-chainchart`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(diagram),
  });
  // ...
}
```

**Called from**: `ChainChart_ui/app/builder/page.tsx` in `handleRunWorkflow()` function (line ~140-165)

## Exact Integration Points

### 1. Run Button Added to Toolbar

**File**: `ChainChart_ui/app/builder/page.tsx`
**Location**: Toolbar section, before Export button (around line 213)

```tsx
<Button 
  variant="outline" 
  size="sm" 
  className="border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 font-bold"
  onClick={handleRunWorkflow}
  disabled={isExecuting || nodes.length === 0}
>
  {isExecuting ? (
    <>
      <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Running...
    </>
  ) : (
    <>
      <Play className="w-4 h-4 mr-2" /> Run Workflow
    </>
  )}
</Button>
```

### 2. Fetch Call Location

**File**: `ChainChart_ui/lib/api.ts`
**Function**: `runChainChart()`
**Endpoint**: `http://localhost:8000/execute-chainchart`

The exact fetch call:

```typescript
const response = await fetch(`${API_BASE_URL}/execute-chainchart`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(diagram),
});
```

### 3. Backend API Endpoint

**File**: `api_server.py`
**Endpoint**: `POST /execute-chainchart`
**Handler**: `execute_chainchart()` function

## Data Flow

1. **UI Diagram Format** (UI nodes/edges):
   ```json
   {
     "nodes": [
       {
         "id": "node_123",
         "type": "state",
         "label": "balance",
         "value": "",
         "metadata": {...}
       }
     ],
     "edges": [
       {
         "from": "node_123:right",
         "to": "node_456:left"
       }
     ]
   }
   ```

2. **Transformation** (in `api_server.py`):
   - Extracts node IDs from edge positions
   - Transforms node metadata to backend format
   - Converts operation expressions to op/a/b format

3. **Backend Format**:
   ```json
   {
     "nodes": [
       {
         "id": "node_123",
         "type": "state",
         "data": {
           "label": "balance"
         }
       }
     ],
     "edges": [
       {
         "from": "node_123",
         "to": "node_456"
       }
     ]
   }
   ```

4. **Execution Result**:
   ```json
   {
     "execution_logs": [
       {
         "step": 1,
         "node": "node_123",
         "type": "state",
         "result": 100,
         "memory": {"balance": 100}
       }
     ],
     "final_memory": {"balance": 100},
     "success": true
   }
   ```

## Running the Integration

### 1. Start Backend Server

```bash
# Install dependencies
pip install -r reqirements.txt

# Run API server
python api_server.py
```

Server will start on `http://localhost:8000`

### 2. Start UI Server

```bash
cd ChainChart_ui
npm install
npm run dev
```

UI will start on `http://localhost:3000`

### 3. Test Integration

1. Open UI at `http://localhost:3000/builder`
2. Add nodes to canvas
3. Connect nodes with edges
4. Click **"Run Workflow"** button in toolbar
5. Debug panel will appear at bottom showing execution results

## Debug Panel Features

The DebugPanel component displays:
- **Execution Logs**: Step-by-step execution trace
- **Memory State**: Final memory values after execution
- **Errors**: Any execution errors with full traceback

## Error Handling

- Empty diagram validation
- Backend connection errors
- Execution errors with full error messages
- Loading states during execution

## Node Type Transformations

- **State**: Uses `label` as storage key
- **Operation**: Parses expression to extract op, a, b
- **Condition**: Uses `metadata.expression`
- **Function**: Uses `label` as function name
- **Event**: Uses `label` as event name
- **Modifier**: Uses `metadata.expression` for access control

## Notes

- All backend tools are currently mocked (return test values)
- No real Neo RPC calls yet
- This is for testing workflow execution flow only
- Backend expects diagram to have at least one node
- Execution starts from first node in graph

