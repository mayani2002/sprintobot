"""
Test a specific query that's failing
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

from app.services.github_service import GitHubService

async def test_query():
    """Test the failing query"""

    print("\n" + "="*80)
    print("🧪 Testing Query: 'fetch latest prs from the user yt-dlp'")
    print("="*80)

    service = GitHubService()

    # Try the exact query
    query = "fetch latest prs from the user yt-dlp"

    print(f"\n📝 Query: '{query}'")
    print("-" * 80)

    try:
        result = await service.process_natural_query(query)

        print("\n" + "="*80)
        print("📊 RESULTS")
        print("="*80)

        # Check for errors
        if "error" in result:
            print(f"\n❌ ERROR DETECTED:")
            print(f"   {result['error']}")

            # Print full result for debugging
            print(f"\n🔍 Full Result:")
            import json
            print(json.dumps(result, indent=2, default=str))

        else:
            print(f"\n✅ SUCCESS")
            print(f"   Method: {result.get('method')}")
            print(f"   Iterations: {result.get('iterations')}")
            print(f"   Success: {result.get('success')}")

            # Show execution plan
            execution_plan = result.get('execution_plan', {})
            function_calls = execution_plan.get('function_calls', [])

            print(f"\n📋 Function Calls Executed:")
            for idx, call in enumerate(function_calls, 1):
                func_name = call.get('function')
                params = call.get('parameters', {})
                clean_params = {k: v for k, v in params.items() if not k.startswith('_')}
                print(f"   {idx}. {func_name}({clean_params})")

                if 'error' in call:
                    print(f"      ❌ Error: {call['error']}")
                elif 'result' in call:
                    res = call['result']
                    if isinstance(res, list):
                        print(f"      ✅ Result: {len(res)} items")
                    elif isinstance(res, dict) and 'error' in res:
                        print(f"      ❌ Error: {res['error']}")

            # Show results
            results_data = result.get('results', [])
            print(f"\n📈 Data Retrieved:")
            for idx, res in enumerate(results_data, 1):
                if isinstance(res, list):
                    print(f"   Result {idx}: {len(res)} items")
                elif isinstance(res, dict):
                    if 'error' in res:
                        print(f"   Result {idx}: ❌ Error - {res.get('error')}")
                    else:
                        print(f"   Result {idx}: {res}")

        print("\n" + "="*80)

        return result

    except Exception as e:
        print(f"\n❌ EXCEPTION OCCURRED:")
        print(f"   {str(e)}")
        import traceback
        print("\n🔍 Full Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query())
