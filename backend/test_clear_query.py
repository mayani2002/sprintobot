"""
Test with a clearer query
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

async def test_queries():
    """Test different query formulations"""

    print("\n" + "="*80)
    print("🧪 Testing Different Query Formulations")
    print("="*80)

    service = GitHubService()

    queries = [
        "Get repositories for user yt-dlp",
        "Show me PRs from yt-dlp's repositories",
        "List PRs in repositories owned by yt-dlp",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Test #{i}: {query}")
        print(f"{'='*80}")

        try:
            result = await service.process_natural_query(query)

            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Method: {result.get('method')}")
                print(f"✅ Success: {result.get('success')}")

                function_calls = result.get('execution_plan', {}).get('function_calls', [])
                for idx, call in enumerate(function_calls, 1):
                    func_name = call.get('function')
                    params = call.get('parameters', {})
                    clean_params = {k: v for k, v in params.items() if not k.startswith('_')}
                    print(f"   {idx}. {func_name}({clean_params})")

                results_data = result.get('results', [])
                for idx, res in enumerate(results_data, 1):
                    if isinstance(res, list):
                        print(f"   Result {idx}: {len(res)} items")
                    elif isinstance(res, dict) and 'error' in res:
                        print(f"   Result {idx}: Error - {res.get('error')}")

        except Exception as e:
            print(f"❌ Exception: {str(e)}")

        await asyncio.sleep(1)  # Rate limiting

if __name__ == "__main__":
    asyncio.run(test_queries())
