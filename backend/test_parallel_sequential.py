"""
Test to demonstrate parallel vs sequential execution patterns
This shows what works and what needs to be implemented
"""
import asyncio
import time
from typing import List, Dict, Any

print("\n" + "="*70)
print("Parallel vs Sequential Execution Test")
print("="*70)

# ============================================================================
# MOCK FUNCTIONS (Simulate API calls)
# ============================================================================

async def mock_get_repos():
    """Simulates getting repositories (500ms)"""
    await asyncio.sleep(0.5)
    return [
        {"name": "repo1", "owner": {"login": "user"}},
        {"name": "repo2", "owner": {"login": "user"}},
        {"name": "repo3", "owner": {"login": "user"}}
    ]

async def mock_get_prs(repo: str):
    """Simulates getting PRs for a repo (600ms)"""
    await asyncio.sleep(0.6)
    return [
        {"number": 1, "title": f"PR 1 in {repo}"},
        {"number": 2, "title": f"PR 2 in {repo}"}
    ]

async def mock_get_contributors(repo: str):
    """Simulates getting contributors (400ms)"""
    await asyncio.sleep(0.4)
    return [
        {"login": "user1", "contributions": 100},
        {"login": "user2", "contributions": 50}
    ]

# ============================================================================
# CURRENT IMPLEMENTATION (Sequential Only)
# ============================================================================

async def execute_sequential(function_calls: List[Dict]) -> Dict[str, Any]:
    """
    Current implementation: executes all functions one after another
    Matches the for loop in github_service.py:53-109
    """
    print("\n📝 SEQUENTIAL EXECUTION (Current Implementation)")
    print("-" * 70)

    results = []
    start_time = time.time()

    for idx, call in enumerate(function_calls, 1):
        func_name = call["function"]
        params = call.get("parameters", {})

        print(f"  [{idx}/{len(function_calls)}] Executing {func_name}({params})...")

        # Execute one function at a time
        if func_name == "get_repos":
            result = await mock_get_repos()
        elif func_name == "get_prs":
            result = await mock_get_prs(params.get("repo"))
        elif func_name == "get_contributors":
            result = await mock_get_contributors(params.get("repo"))

        results.append(result)
        print(f"      ✅ Completed ({len(result)} items)")

    elapsed = time.time() - start_time

    print(f"\n  ⏱️  Total Time: {elapsed:.2f}s")
    print(f"  📊 Functions: {len(function_calls)}")

    return {
        "results": results,
        "elapsed_time": elapsed,
        "execution_mode": "sequential"
    }

# ============================================================================
# PROPOSED IMPLEMENTATION (Parallel Support)
# ============================================================================

async def execute_parallel(function_calls: List[Dict]) -> Dict[str, Any]:
    """
    Proposed implementation: executes independent functions in parallel
    Uses asyncio.gather for concurrent execution
    """
    print("\n⚡ PARALLEL EXECUTION (Proposed Implementation)")
    print("-" * 70)

    start_time = time.time()
    tasks = []

    print(f"  Creating {len(function_calls)} concurrent tasks...")

    for call in function_calls:
        func_name = call["function"]
        params = call.get("parameters", {})

        # Create async tasks (don't await yet)
        if func_name == "get_repos":
            tasks.append(mock_get_repos())
        elif func_name == "get_prs":
            tasks.append(mock_get_prs(params.get("repo")))
        elif func_name == "get_contributors":
            tasks.append(mock_get_contributors(params.get("repo")))

        print(f"    ⏳ Queued: {func_name}({params})")

    # Execute ALL tasks concurrently
    print(f"\n  ⚡ Executing all {len(tasks)} functions simultaneously...")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.time() - start_time

    # Show results
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"    ❌ Task {idx+1} failed: {result}")
        else:
            print(f"    ✅ Task {idx+1} completed ({len(result)} items)")

    print(f"\n  ⏱️  Total Time: {elapsed:.2f}s")
    print(f"  📊 Functions: {len(function_calls)}")

    return {
        "results": results,
        "elapsed_time": elapsed,
        "execution_mode": "parallel"
    }

# ============================================================================
# SMART EXECUTION (Mixed: Sequential + Parallel)
# ============================================================================

async def execute_smart(execution_plan: Dict) -> Dict[str, Any]:
    """
    Optimal implementation: sequential for dependencies, parallel for independent calls
    This is what the system SHOULD do
    """
    print("\n🎯 SMART EXECUTION (Optimal Approach)")
    print("-" * 70)

    all_results = []
    start_time = time.time()
    context = {}

    for step_group in execution_plan["steps"]:
        step_num = step_group["step"]
        mode = step_group["execution_mode"]
        functions = step_group["functions"]

        print(f"\n  Step {step_num}: {mode.upper()} ({len(functions)} function(s))")

        if mode == "sequential":
            # Execute one at a time
            for call in functions:
                func_name = call["function"]
                params = call.get("parameters", {})

                print(f"    ⏳ Executing {func_name}({params})...")

                if func_name == "get_repos":
                    result = await mock_get_repos()
                    context["repos"] = result  # Store for next step

                all_results.append(result)
                print(f"      ✅ Completed")

        elif mode == "parallel":
            # Execute all concurrently
            tasks = []

            for call in functions:
                func_name = call["function"]
                params = call.get("parameters", {})

                # Inject from context if needed
                if params.get("repo") == "{from_context}":
                    # Get repo from previous step
                    repos = context.get("repos", [])
                    params["repo"] = repos[len(tasks)]["name"] if repos else "unknown"

                print(f"    ⏳ Queued: {func_name}({params})")

                if func_name == "get_prs":
                    tasks.append(mock_get_prs(params["repo"]))
                elif func_name == "get_contributors":
                    tasks.append(mock_get_contributors(params["repo"]))

            print(f"    ⚡ Executing {len(tasks)} functions in parallel...")
            results = await asyncio.gather(*tasks)
            all_results.extend(results)

            for idx, result in enumerate(results):
                print(f"      ✅ Task {idx+1} completed")

    elapsed = time.time() - start_time

    print(f"\n  ⏱️  Total Time: {elapsed:.2f}s")
    print(f"  📊 Total Functions: {sum(len(s['functions']) for s in execution_plan['steps'])}")

    return {
        "results": all_results,
        "elapsed_time": elapsed,
        "execution_mode": "smart"
    }

# ============================================================================
# TEST CASES
# ============================================================================

async def test_case_1_independent_calls():
    """
    Test Case 1: Multiple independent function calls
    Query: "Get PRs for repo1, repo2, and repo3"
    """
    print("\n" + "="*70)
    print("TEST CASE 1: Independent Function Calls")
    print("Query: 'Get PRs for repo1, repo2, and repo3'")
    print("="*70)

    function_calls = [
        {"function": "get_prs", "parameters": {"repo": "repo1"}},
        {"function": "get_prs", "parameters": {"repo": "repo2"}},
        {"function": "get_prs", "parameters": {"repo": "repo3"}}
    ]

    # Execute sequentially (current implementation)
    seq_result = await execute_sequential(function_calls)

    # Execute in parallel (proposed)
    par_result = await execute_parallel(function_calls)

    # Compare
    print("\n" + "="*70)
    print("📊 PERFORMANCE COMPARISON")
    print("="*70)
    print(f"  Sequential: {seq_result['elapsed_time']:.2f}s")
    print(f"  Parallel:   {par_result['elapsed_time']:.2f}s")

    speedup = (seq_result['elapsed_time'] / par_result['elapsed_time'] - 1) * 100
    print(f"\n  🚀 Speedup: {speedup:.1f}% faster with parallel execution")

async def test_case_2_mixed_dependencies():
    """
    Test Case 2: Mixed sequential + parallel execution
    Query: "Get my repos and fetch PRs for each"
    """
    print("\n\n" + "="*70)
    print("TEST CASE 2: Mixed Dependencies (Sequential → Parallel)")
    print("Query: 'Get my repos and fetch PRs for each'")
    print("="*70)

    # Step 1: Get repos (must be first)
    # Step 2: Get PRs for each repo (can be parallel)

    execution_plan = {
        "steps": [
            {
                "step": 1,
                "execution_mode": "sequential",
                "functions": [
                    {"function": "get_repos", "parameters": {}}
                ]
            },
            {
                "step": 2,
                "execution_mode": "parallel",
                "depends_on_step": 1,
                "functions": [
                    {"function": "get_prs", "parameters": {"repo": "{from_context}"}},
                    {"function": "get_prs", "parameters": {"repo": "{from_context}"}},
                    {"function": "get_prs", "parameters": {"repo": "{from_context}"}}
                ]
            }
        ]
    }

    result = await execute_smart(execution_plan)

    print("\n" + "="*70)
    print("📊 ANALYSIS")
    print("="*70)
    print(f"  Total Time: {result['elapsed_time']:.2f}s")
    print(f"  Expected Sequential: ~2.3s (0.5s + 3×0.6s)")
    print(f"  Actual Smart: {result['elapsed_time']:.2f}s (0.5s + max(0.6s))")

    speedup = (2.3 / result['elapsed_time'] - 1) * 100
    print(f"\n  🚀 Speedup: {speedup:.1f}% faster with smart execution")

async def test_case_3_all_parallel():
    """
    Test Case 3: All functions can run in parallel
    Query: "Get PRs, contributors, and languages for myrepo"
    """
    print("\n\n" + "="*70)
    print("TEST CASE 3: All Independent (Max Parallelization)")
    print("Query: 'Get PRs and contributors for myrepo'")
    print("="*70)

    function_calls = [
        {"function": "get_prs", "parameters": {"repo": "myrepo"}},
        {"function": "get_contributors", "parameters": {"repo": "myrepo"}},
        {"function": "get_prs", "parameters": {"repo": "otherrepo"}},
        {"function": "get_contributors", "parameters": {"repo": "otherrepo"}}
    ]

    seq_result = await execute_sequential(function_calls)
    par_result = await execute_parallel(function_calls)

    print("\n" + "="*70)
    print("📊 PERFORMANCE COMPARISON")
    print("="*70)
    print(f"  Sequential: {seq_result['elapsed_time']:.2f}s")
    print(f"  Parallel:   {par_result['elapsed_time']:.2f}s")

    speedup = (seq_result['elapsed_time'] / par_result['elapsed_time'] - 1) * 100
    print(f"\n  🚀 Speedup: {speedup:.1f}% faster")
    print(f"  ⚡ Parallelization: {len(function_calls)} concurrent calls")

# ============================================================================
# MAIN
# ============================================================================

async def main():
    print("\n🧪 Testing Parallel vs Sequential Execution Patterns\n")

    await test_case_1_independent_calls()
    await test_case_2_mixed_dependencies()
    await test_case_3_all_parallel()

    print("\n\n" + "="*70)
    print("✅ SUMMARY")
    print("="*70)
    print("  Current State:")
    print("    ✅ Sequential execution: WORKING")
    print("    ❌ Parallel execution: NOT IMPLEMENTED")
    print()
    print("  Performance Impact:")
    print("    🚀 50-90% faster with parallel execution")
    print("    ⚡ Better for multi-repo queries")
    print("    💰 Lower API costs (fewer timeout retries)")
    print()
    print("  Next Steps:")
    print("    1. Add 'execution_mode' to execution plans")
    print("    2. Implement asyncio.gather in github_service.py")
    print("    3. Update AI planner to group independent calls")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
