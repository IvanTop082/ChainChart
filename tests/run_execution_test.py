#!/usr/bin/env python
"""
Diagnostics script to verify ChainChart execution engine is running (not mocked).
Tests the /execute-chainchart endpoint and detects real vs mock execution.
"""

import requests
import json
import sys
from pathlib import Path

# API endpoint
API_BASE_URL = "http://localhost:8000"

def load_test_diagram():
    """Load the sample ChainChart JSON file."""
    test_file = Path(__file__).parent / "sample_chainchart.json"
    if not test_file.exists():
        print(f"❌ ERROR: Test file not found: {test_file}")
        sys.exit(1)
    
    with open(test_file, 'r') as f:
        return json.load(f)

def check_health():
    """Check if the API server is running and healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print("✅ Health check passed:")
            print(f"   Status: {health.get('status')}")
            print(f"   Agent loaded: {health.get('agent_loaded')}")
            print(f"   Neo tools loaded: {health.get('neo_tools_loaded')}")
            return True
        else:
            print(f"⚠️  Health check returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Cannot connect to API server at {API_BASE_URL}")
        print("   Make sure the server is running: python api_server.py")
        return False
    except Exception as e:
        print(f"⚠️  Health check error: {e}")
        return False

def test_execution():
    """Test the /execute-chainchart endpoint."""
    print("\n" + "="*60)
    print("TESTING /execute-chainchart ENDPOINT")
    print("="*60)
    
    # Load test diagram
    diagram = load_test_diagram()
    print(f"\n📋 Loaded test diagram:")
    print(f"   Nodes: {len(diagram['nodes'])}")
    print(f"   Edges: {len(diagram['edges'])}")
    
    # Send POST request
    print(f"\n📤 Sending POST request to {API_BASE_URL}/execute-chainchart...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/execute-chainchart",
            json=diagram,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Response text: {response.text}")
            return False
        
        # Parse response
        result = response.json()
        
        print("\n" + "="*60)
        print("RESPONSE ANALYSIS")
        print("="*60)
        
        # Check for required fields
        has_execution_logs = "execution_logs" in result
        has_final_memory = "final_memory" in result
        has_success = "success" in result
        
        print(f"\n📊 Response fields:")
        print(f"   execution_logs: {'✅' if has_execution_logs else '❌ MISSING'}")
        print(f"   final_memory: {'✅' if has_final_memory else '❌ MISSING'}")
        print(f"   success: {'✅' if has_success else '❌ MISSING'}")
        
        # Check for debug fields (if debug mode is enabled)
        has_execution_trace = "execution_trace" in result
        has_memory_state = "memory_state" in result
        has_logs = "logs" in result
        has_debug_info = "debug_info" in result
        
        print(f"\n🔍 Debug fields (if debug mode enabled):")
        print(f"   execution_trace: {'✅' if has_execution_trace else '❌ MISSING'}")
        print(f"   memory_state: {'✅' if has_memory_state else '❌ MISSING'}")
        print(f"   logs: {'✅' if has_logs else '❌ MISSING'}")
        print(f"   debug_info: {'✅' if has_debug_info else '❌ MISSING'}")
        
        # Detect real vs mock execution
        print("\n" + "="*60)
        print("EXECUTION DETECTION")
        print("="*60)
        
        is_mock = result.get("mock", False)
        has_error = result.get("error") is not None
        
        if has_error:
            print(f"\n❌ ERROR RETURNED:")
            print(f"   {result.get('error')}")
            return False
        
        if is_mock:
            print(f"\n⚠️  MOCK EXECUTION — engine not wired")
            print(f"   The response indicates mock execution.")
            return False
        
        if not has_execution_logs or not has_final_memory:
            print(f"\n⚠️  INCOMPLETE RESPONSE — missing required fields")
            print(f"   This suggests the execution engine may not be fully integrated.")
            return False
        
        # Check execution_logs content
        execution_logs = result.get("execution_logs", [])
        if not execution_logs:
            print(f"\n⚠️  EMPTY EXECUTION LOGS")
            print(f"   No execution steps were logged.")
            return False
        
        # Check if logs have meaningful content
        has_meaningful_logs = False
        for log in execution_logs:
            if "step" in log and "node" in log and "type" in log:
                has_meaningful_logs = True
                break
        
        if not has_meaningful_logs:
            print(f"\n⚠️  EXECUTION LOGS LACK STRUCTURE")
            print(f"   Logs exist but don't have expected structure.")
            return False
        
        # Check final_memory content
        final_memory = result.get("final_memory", {})
        if not isinstance(final_memory, dict):
            print(f"\n⚠️  FINAL_MEMORY IS NOT A DICT")
            print(f"   Expected dict, got {type(final_memory)}")
            return False
        
        print(f"\n✅ REAL EXECUTION DETECTED")
        print(f"   Execution logs: {len(execution_logs)} steps")
        print(f"   Final memory keys: {list(final_memory.keys())}")
        
        # Print detailed execution trace
        print("\n" + "="*60)
        print("EXECUTION TRACE")
        print("="*60)
        for log in execution_logs:
            print(f"\nStep {log.get('step', '?')}: Node {log.get('node', '?')} ({log.get('type', '?')})")
            if "output" in log:
                print(f"  Output: {log['output']}")
            if "result" in log:
                print(f"  Result: {log['result']}")
            if "emitted" in log:
                print(f"  Emitted: {log['emitted']}")
        
        print("\n" + "="*60)
        print("FINAL MEMORY STATE")
        print("="*60)
        print(json.dumps(final_memory, indent=2))
        
        # Print debug info if available
        if has_debug_info:
            print("\n" + "="*60)
            print("DEBUG INFO")
            print("="*60)
            print(json.dumps(result.get("debug_info"), indent=2))
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Cannot connect to API server at {API_BASE_URL}")
        print("   Make sure the server is running: python api_server.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("="*60)
    print("CHAINCHART EXECUTION ENGINE DIAGNOSTICS")
    print("="*60)
    
    # Step 1: Health check
    print("\n[1/2] Checking API health...")
    if not check_health():
        sys.exit(1)
    
    # Step 2: Test execution
    print("\n[2/2] Testing execution endpoint...")
    success = test_execution()
    
    print("\n" + "="*60)
    if success:
        print("✅ ALL TESTS PASSED - Real execution engine is working!")
    else:
        print("❌ TESTS FAILED - Execution engine may not be properly wired")
    print("="*60)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

