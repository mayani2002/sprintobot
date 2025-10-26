"""
Comprehensive Query Test Suite
Run: python test_query_suite.py
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
        print(f"✓ Loaded environment from {env_path}\n")
    else:
        print(f"⚠️  Environment file not found at {env_path}\n")

def check_dependencies():
    """Check if required packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = {
        'github': 'PyGithub',
        'google.genai': 'google-genai',
        'fastapi': 'fastapi',
        'pydantic': 'pydantic'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print(f"\n💡 To install, run:")
        print(f"   cd backend")
        print(f"   pip install {' '.join(missing)}")
        print(f"   OR")
        print(f"   pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed\n")
    return True

load_env_file()

# Check dependencies before running tests
if not check_dependencies():
    print("\n⚠️  Please install missing dependencies first.")
    sys.exit(1)

# Test cases organized by category
TEST_QUERIES = {
    "Simple Single-Pass": [
        {
            "query": "Show me my repositories",
            "expected_method": "single_pass",
            "expected_function": "get_authenticated_user_repositories",
            "expected_params": {}
        },
        {
            "query": "Get details of repository mayani/ecohabit",
            "expected_method": "single_pass",
            "expected_function": "get_repository",
            "expected_params": {"owner": "mayani", "repo": "ecohabit"}
        }
    ],
    
    "Iterative (Repo Discovery)": [
        {
            "query": "Get PRs merged in last 7 days",
            "expected_method": "iterative",
            "expected_first_function": "get_authenticated_user_repositories",
            "expected_second_function": "get_merged_prs_last_n_days",
            "expected_params": {"n": 7}
        },
        {
            "query": "Show all open PRs",
            "expected_method": "iterative",
            "expected_first_function": "get_authenticated_user_repositories",
            "expected_second_function": "get_prs",
            "expected_params": {"state": "open"}
        }
    ],
    
    "Time-Based Parameter Extraction": [
        {
            "query": "PRs merged in last 14 days",
            "expected_method": "iterative",
            "expected_params": {"n": 14}
        },
        {
            "query": "PRs waiting for review for 48 hours",
            "expected_method": "iterative",
            "expected_params": {"hours": 48}
        }
    ],
    
    "Repository Specification": [
        {
            "query": "Get PRs from mayani2002/ecohabit",
            "expected_method": "single_pass",
            "expected_function": "get_prs",
            "expected_params": {"owner": "mayani2002", "repo": "ecohabit"}
        },
        {
            "query": "Show merged PRs from lugenx/ecohabit in last 5 days",
            "expected_method": "single_pass",
            "expected_function": "get_merged_prs_last_n_days",
            "expected_params": {"owner": "lugenx", "repo": "ecohabit", "n": 5}
        }
    ],
    
    "Edge Cases": [
        {
            "query": "Show me PRs",
            "expected_method": "iterative",
            "note": "Ambiguous - should discover repos"
        },
        {
            "query": "Get PR #9",
            "expected_method": "iterative",
            "expected_params": {"pr_number": 123},
            "note": "Missing repo - should discover"
        }
    ]
}

async def run_test_suite():
    try:
        from app.services.github_service import GitHubService
    except ImportError as e:
        print(f"❌ Import Error: {str(e)}")
        print("\n💡 Make sure you're in the 'backend' directory and dependencies are installed:")
        print("   cd backend")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    service = GitHubService()
    results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    print("=" * 80)
    print("🧪 SprintoBot Comprehensive Query Test Suite")
    print("=" * 80)
    
    for category, tests in TEST_QUERIES.items():
        print(f"\n{'='*80}")
        print(f"📂 Category: {category}")
        print(f"{'='*80}")
        
        for idx, test in enumerate(tests, 1):
            query = test["query"]
            print(f"\n🔍 Test {idx}: \"{query}\"")
            
            try:
                result = await service.process_natural_query(query)
                
                # Validate method
                actual_method = result.get("method")
                expected_method = test.get("expected_method")
                
                method_match = actual_method == expected_method if expected_method else True
                
                # Validate function
                function_calls = result.get("execution_plan", {}).get("function_calls", [])
                if function_calls:
                    actual_function = function_calls[0].get("function")
                    expected_function = test.get("expected_function")
                    function_match = actual_function == expected_function if expected_function else True
                else:
                    function_match = False
                
                # Validate parameters
                if function_calls:
                    actual_params = function_calls[0].get("parameters", {})
                    expected_params = test.get("expected_params", {})
                    params_match = all(actual_params.get(k) == v for k, v in expected_params.items()) if expected_params else True
                else:
                    params_match = False
                
                passed = method_match and function_match and params_match
                
                if passed:
                    print("   ✅ PASSED")
                    results["passed"] += 1
                else:
                    print("   ❌ FAILED")
                    if not method_match:
                        print(f"      Method: expected={expected_method}, actual={actual_method}")
                    if not function_match:
                        print(f"      Function: expected={test.get('expected_function')}, actual={actual_function}")
                    if not params_match:
                        print(f"      Params: expected={expected_params}, actual={actual_params}")
                    results["failed"] += 1
                
                results["tests"].append({
                    "query": query,
                    "category": category,
                    "passed": passed,
                    "method": actual_method,
                    "function": actual_function if function_calls else None
                })
                
                # Show note if present
                if test.get("note"):
                    print(f"   ℹ️  Note: {test['note']}")
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                results["failed"] += 1
                results["tests"].append({
                    "query": query,
                    "category": category,
                    "passed": False,
                    "error": str(e)
                })
            
            await asyncio.sleep(0.5)  # Rate limiting
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"✅ Passed: {results['passed']}/{total}")
    print(f"❌ Failed: {results['failed']}/{total}")
    print(f"📈 Pass Rate: {pass_rate:.1f}%")
    
    # Breakdown by category
    print("\n📂 Results by Category:")
    for category in TEST_QUERIES.keys():
        category_tests = [t for t in results["tests"] if t.get("category") == category]
        passed = sum(1 for t in category_tests if t.get("passed"))
        total_cat = len(category_tests)
        print(f"   {category}: {passed}/{total_cat}")
    
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_test_suite())
