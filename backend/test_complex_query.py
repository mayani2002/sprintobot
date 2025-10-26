"""
Test complex multi-step queries
Run: python test_complex_query.py
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
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value

load_env_file()

async def test_complex_queries():
    from app.services.github_service import GitHubService
    
    service = GitHubService()
    
    # Test queries of increasing complexity
    test_queries = [
        "What was the latest PR in my last 4 projects?",
        "Show me all open PRs across my repositories",
        "Which repositories have PRs waiting for review?",
        "List the most active repositories with recent PRs"
    ]
    
    print("=" * 70)
    print("Complex Query Test Suite")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 70)
        
        result = await service.process_natural_query(query)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Query Type: {result.get('query_type', 'simple')}")
            
            if result.get('query_type') == 'multi_step':
                print(f"   Complexity: {result.get('complexity')}")
                print(f"   Steps: {result.get('steps_executed')}")
                print(f"   Results: {len(result.get('result', []))}")
                print(f"\n   Summary:\n{result.get('summary', 'No summary')}")
            else:
                print(f"   Function: {result.get('function_called')}")
                print(f"   Results: {len(result.get('result', []))}")
        
        print()
        await asyncio.sleep(1)  # Rate limiting
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_complex_queries())
