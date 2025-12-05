from spoon_ai.tools.base import BaseTool
from typing import Any, Dict, Optional

class ReadNeoStateTool(BaseTool):
    name: str = "read_neo_state"
    description: str = "Retrieve a storage value from Neo blockchain."
    parameters: dict = {
        "type": "object",
        "properties": {"key": {"type": "string"}},
        "required": ["key"]
    }

    async def execute(self, key: str) -> Any:
        # Return mocked numeric values for testing
        mock_values = {
            "balance": 100,
            "amount": 50,
            "total": 200
        }
        return mock_values.get(key, 0)

class CallNeoContractTool(BaseTool):
    name: str = "call_neo_contract"
    description: str = "Call a Neo smart contract function."
    parameters: dict = {
        "type": "object",
        "properties": {"method": {"type": "string"}, "args": {"type": "array"}},
        "required": ["method"]
    }

    async def execute(self, method: str, args: Optional[list] = None) -> Dict[str, Any]:
        return {"status": "mocked_contract_call", "method": method, "args": args or []}

class OperationTool(BaseTool):
    name: str = "perform_operation"
    description: str = "Execute a math/logic operation."
    parameters: dict = {
        "type": "object",
        "properties": {"op": {"type": "string"}, "a": {}, "b": {}},
        "required": ["op", "a"]
    }

    async def execute(self, op: str, a: Any, b: Any = None) -> Any:
        if op == "add": return a + b
        if op == "sub": return a - b
        if op == "mul": return a * b
        if op == "div": return a / b
        if op == "and": return bool(a and b)
        if op == "or": return bool(a or b)
        return None

class DebugLogTool(BaseTool):
    name: str = "debug_log"
    description: str = "Send debug messages to the frontend."
    parameters: dict = {
        "type": "object",
        "properties": {"msg": {"type": "string"}},
        "required": ["msg"]
    }

    async def execute(self, msg: str) -> Dict[str, str]:
        return {"debug": msg}
