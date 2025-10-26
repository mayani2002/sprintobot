"""
Test the new intelligent AI query handling system
Run: python test_with_new_ai.py
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def load_env_file():
    """Load environment variables"""
    env_path = Path(__file__).parent.parent / "config" / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value
        print(f"✓ Loaded environment from {env_path}\n")

load_env_file()

async def test_queries():
    """Test different query types"""
    from app.services.github_service import GitHubService
    
    service = GitHubService()
    
    test_cases = [
        {
            "name": "Simple Query (Should list repositories)",
            "query": "Show me my repositories",
            "expected_method": "single_pass",
            "expected_function": "get_authenticated_user_repositories"
        },
        {
            "name": "Time-based Query WITHOUT repo (Should be ITERATIVE)",
            "query": "Get PRs merged in the last 7 days",
            "expected_method": "iterative",  # Changed from single_pass
            "expected_function": "get_authenticated_user_repositories"  # First step
        },
        {
            "name": "Time-based Query WITH repo (Should be single-pass)",
            "query": "Get PRs merged in the last 7 days from owner/myrepo",
            "expected_method": "single_pass",
            "expected_function": "get_merged_prs_last_n_days"
        },
        {
            "name": "Specific PR Query (Should get PR details)",
            "query": "Show me details of PR #1 from owner/repo",
            "expected_method": "single_pass",
            "expected_function": "get_pr_details"
        }
    ]
    
    results = []
    
    for test in test_cases:
        print("=" * 70)
        print(f"🧪 TEST: {test['name']}")
        print(f"   Query: \"{test['query']}\"")
        print(f"   Expected Function: {test['expected_function']}")
        print("=" * 70)
        
        result = await service.process_natural_query(test["query"])
        
        # Get the actual function called
        actual_function = None
        if result.get("execution_plan", {}).get("function_calls"):
            actual_function = result["execution_plan"]["function_calls"][0].get("function")
        
        # Check both method AND function
        method_correct = result.get("method") == test["expected_method"]
        function_correct = actual_function == test["expected_function"]
        
        success = result.get("success", False) and method_correct and function_correct
        
        results.append({
            "test": test["name"],
            "success": success,
            "method": result.get("method"),
            "expected_method": test["expected_method"],
            "actual_function": actual_function,
            "expected_function": test["expected_function"],
            "function_correct": function_correct,
            "iterations": result.get("iterations", 0),
            "efficiency": result.get("efficiency", "unknown")
        })
        
        print("\n📋 RESULT:")
        print(f"   Actual Function: {actual_function}")
        print(f"   Expected Function: {test['expected_function']}")
        print(f"   Function Match: {'✅' if function_correct else '❌'}")
        print("\n")
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"{status} {r['test']}")
        print(f"   Method: {r['method']} (expected: {r['expected_method']})")
        
        func_status = "✅" if r["function_correct"] else "❌"
        print(f"   {func_status} Function: {r['actual_function']} (expected: {r['expected_function']})")
        print(f"   Iterations: {r['iterations']} | Efficiency: {r['efficiency']}")
    
    total = len(results)
    passed = len([r for r in results if r["success"]])
    
    print(f"\n{'='*70}")
    if passed == total:
        print(f"✅ ALL TESTS PASSED: {passed}/{total}")
    else:
        print(f"⚠️  SOME TESTS FAILED: {passed}/{total} passed")
        print(f"\n🔍 Issues Found:")
        for r in results:
            if not r["success"]:
                print(f"   ❌ {r['test']}")
                if not r["function_correct"]:
                    print(f"      Wrong function: {r['actual_function']} (expected {r['expected_function']})")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(test_queries())
