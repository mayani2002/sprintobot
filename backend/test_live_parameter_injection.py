"""
Live test for parameter injection with real APIs
Tests that our fixes work end-to-end
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def load_env_file():
    env_path = Path(__file__).parent.parent / "config" / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

load_env_file()

async def test_parameter_injection_live():
    """Test parameter injection with a query that requires discovery"""
    from app.services.github_service import GitHubService

    print("\n" + "="*70)
    print("🧪 Live Parameter Injection Test")
    print("="*70)

    service = GitHubService()

    # This query should trigger iterative execution:
    # Step 1: Discover repositories
    # Step 2: Use discovered params in get_prs call
    query = "Show me all open PRs"

    print(f"\n📝 Query: '{query}'")
    print("-" * 70)
    print("Expected behavior:")
    print("  1. Detect missing owner/repo")
    print("  2. Create 2-step plan")
    print("  3. Execute discovery")
    print("  4. Inject discovered params")
    print("  5. Execute main query")
    print("-" * 70)

    result = await service.process_natural_query(query)

    print("\n" + "="*70)
    print("📊 RESULTS")
    print("="*70)

    # Check execution plan
    execution_plan = result.get("execution_plan", {})
    function_calls = execution_plan.get("function_calls", [])
    method = result.get("method")

    print(f"\n1. Execution Method: {method}")
    print(f"2. Number of function calls: {len(function_calls)}")

    # Check for parameter injection evidence
    injection_found = False
    for i, call in enumerate(function_calls, 1):
        print(f"\n   Step {i}: {call.get('function')}")
        params = call.get('parameters', {})
        print(f"   Parameters: {params}")

        # Check if params were injected (not None)
        if call.get('function') != 'get_authenticated_user_repositories':
            if 'owner' in params and params['owner'] is not None:
                print(f"   ✨ Parameter injection detected!")
                print(f"      → owner: {params.get('owner')}")
                print(f"      → repo: {params.get('repo')}")
                injection_found = True

    print("\n" + "="*70)
    print("✅ TEST RESULTS")
    print("="*70)

    if method == "iterative" and len(function_calls) >= 2:
        print("✅ Used iterative execution (as expected)")
    else:
        print(f"⚠️  Used {method} execution with {len(function_calls)} calls")

    if injection_found:
        print("✅ Parameter injection VERIFIED - params were discovered and injected!")
    else:
        print("⚠️  Parameter injection not clearly visible (may have used fallback)")

    # Check results
    results = result.get("results", [])
    print(f"\n📈 Query returned {len(results)} result(s)")

    if result.get("success"):
        print("\n🎉 SUCCESS - Query executed without errors!")
    else:
        print("\n⚠️  Query completed with warnings")

    print("="*70 + "\n")

    return result

if __name__ == "__main__":
    try:
        result = asyncio.run(test_parameter_injection_live())
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
