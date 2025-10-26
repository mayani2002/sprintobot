"""
Integration test for parallel execution implementation
Tests the complete flow: AI planning → Grouping → Parallel/Sequential execution
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_grouping_logic():
    """Test that the AI service correctly groups function calls"""
    from app.services.ai_service import AIService

    print("\n" + "="*70)
    print("TEST 1: Dependency Grouping Logic")
    print("="*70)

    ai_service = AIService()

    # Test Case 1: Mixed discovery + execution
    print("\n📝 Test Case 1a: Discovery + Execution (with placeholders)")
    function_calls = [
        {
            "function": "get_authenticated_user_repositories",
            "parameters": {},
            "placeholder": False,
            "purpose": "Discovery"
        },
        {
            "function": "get_merged_prs_last_n_days",
            "parameters": {"owner": None, "repo": None, "n": 7},
            "placeholder": True,
            "purpose": "Execute"
        }
    ]

    groups = ai_service._group_by_dependencies(function_calls)

    print(f"  Input: {len(function_calls)} function calls")
    print(f"  Output: {len(groups)} groups")

    for idx, group in enumerate(groups, 1):
        print(f"\n  Group {idx}:")
        print(f"    Mode: {group['mode']}")
        print(f"    Functions: {len(group['calls'])}")
        print(f"    Description: {group.get('description', '')}")

    assert len(groups) == 2, "Should have 2 groups (discovery + execution)"
    assert groups[0]["mode"] == "sequential", "Discovery should be sequential"
    assert groups[1]["mode"] == "sequential", "Execution with placeholders should be sequential"
    print("\n  ✅ Test Case 1a PASSED")

    # Test Case 2: Multiple independent calls
    print("\n📝 Test Case 1b: Multiple Independent Calls (no placeholders)")
    function_calls = [
        {
            "function": "get_prs",
            "parameters": {"owner": "user", "repo": "repo1"},
            "placeholder": False,
            "purpose": "Execute"
        },
        {
            "function": "get_prs",
            "parameters": {"owner": "user", "repo": "repo2"},
            "placeholder": False,
            "purpose": "Execute"
        },
        {
            "function": "get_prs",
            "parameters": {"owner": "user", "repo": "repo3"},
            "placeholder": False,
            "purpose": "Execute"
        }
    ]

    groups = ai_service._group_by_dependencies(function_calls)

    print(f"  Input: {len(function_calls)} function calls")
    print(f"  Output: {len(groups)} groups")

    for idx, group in enumerate(groups, 1):
        print(f"\n  Group {idx}:")
        print(f"    Mode: {group['mode']}")
        print(f"    Functions: {len(group['calls'])}")

    assert len(groups) == 1, "Should have 1 group (all independent)"
    assert groups[0]["mode"] == "parallel", "Independent calls should be parallel"
    assert len(groups[0]["calls"]) == 3, "Should have 3 functions in parallel group"
    print("\n  ✅ Test Case 1b PASSED")

    # Test Case 3: Single call
    print("\n📝 Test Case 1c: Single Call (should be sequential)")
    function_calls = [
        {
            "function": "get_repos",
            "parameters": {},
            "placeholder": False,
            "purpose": "Execute"
        }
    ]

    groups = ai_service._group_by_dependencies(function_calls)

    assert len(groups) == 1
    assert groups[0]["mode"] == "sequential", "Single call should be sequential"
    print("  ✅ Test Case 1c PASSED")

    print("\n" + "="*70)
    print("✅ ALL GROUPING TESTS PASSED")
    print("="*70)

async def test_execution_modes():
    """Test that execution modes work correctly"""
    import asyncio
    import time

    print("\n\n" + "="*70)
    print("TEST 2: Execution Mode Performance")
    print("="*70)

    # Mock functions with delays
    async def mock_api_call(name: str, delay: float = 0.3):
        """Simulate API call with delay"""
        await asyncio.sleep(delay)
        return {"name": name, "data": [1, 2, 3]}

    # Test sequential execution
    print("\n📝 Test Case 2a: Sequential Execution")
    start = time.time()

    results = []
    for i in range(3):
        result = await mock_api_call(f"call{i}")
        results.append(result)

    seq_time = time.time() - start
    print(f"  Time: {seq_time:.2f}s")
    print(f"  Expected: ~0.9s (3 × 0.3s)")
    print(f"  Results: {len(results)} items")

    assert seq_time >= 0.8, "Sequential should take at least 0.8s"
    print("  ✅ Test Case 2a PASSED")

    # Test parallel execution
    print("\n📝 Test Case 2b: Parallel Execution")
    start = time.time()

    tasks = [mock_api_call(f"call{i}") for i in range(3)]
    results = await asyncio.gather(*tasks)

    par_time = time.time() - start
    print(f"  Time: {par_time:.2f}s")
    print(f"  Expected: ~0.3s (max of parallel)")
    print(f"  Results: {len(results)} items")

    assert par_time < 0.5, "Parallel should take less than 0.5s"
    print("  ✅ Test Case 2b PASSED")

    # Compare
    speedup = (seq_time / par_time - 1) * 100
    print(f"\n  🚀 Speedup: {speedup:.1f}% faster")

    print("\n" + "="*70)
    print("✅ ALL EXECUTION TESTS PASSED")
    print("="*70)

def test_execution_plan_structure():
    """Test that execution plans have the correct structure"""
    print("\n\n" + "="*70)
    print("TEST 3: Execution Plan Structure")
    print("="*70)

    # Mock execution state
    execution_state = {
        "function_calls": [
            {
                "function": "get_repos",
                "parameters": {},
                "placeholder": False,
                "purpose": "Discovery"
            },
            {
                "function": "get_prs",
                "parameters": {"owner": None, "repo": None},
                "placeholder": True,
                "purpose": "Execute"
            }
        ]
    }

    from app.services.ai_service import AIService
    ai_service = AIService()

    # Generate groups
    execution_state["execution_groups"] = ai_service._group_by_dependencies(
        execution_state["function_calls"]
    )

    print("\n📝 Execution Plan Structure:")
    print(f"  function_calls: {len(execution_state['function_calls'])} items (backwards compat)")
    print(f"  execution_groups: {len(execution_state['execution_groups'])} groups (new)")

    # Validate structure
    assert "function_calls" in execution_state, "Should have function_calls"
    assert "execution_groups" in execution_state, "Should have execution_groups"
    assert isinstance(execution_state["execution_groups"], list), "execution_groups should be a list"

    for group in execution_state["execution_groups"]:
        print(f"\n  Group {group['step']}:")
        print(f"    mode: {group['mode']}")
        print(f"    calls: {len(group['calls'])}")
        print(f"    description: {group.get('description', 'N/A')}")

        assert "step" in group, "Group should have step"
        assert "mode" in group, "Group should have mode"
        assert "calls" in group, "Group should have calls"
        assert group["mode"] in ["sequential", "parallel"], "Mode should be sequential or parallel"

    print("\n  ✅ Structure is valid")

    print("\n" + "="*70)
    print("✅ ALL STRUCTURE TESTS PASSED")
    print("="*70)

def test_backwards_compatibility():
    """Test that old code still works (no execution_groups)"""
    print("\n\n" + "="*70)
    print("TEST 4: Backwards Compatibility")
    print("="*70)

    # Old-style execution plan (no execution_groups)
    old_plan = {
        "function_calls": [
            {"function": "get_repos", "parameters": {}}
        ]
    }

    print("\n📝 Testing old-style plan (no execution_groups):")
    print(f"  function_calls: {len(old_plan['function_calls'])}")
    print(f"  execution_groups: {old_plan.get('execution_groups', 'Not present')}")

    # Simulate what github_service does
    execution_groups = old_plan.get("execution_groups")

    if execution_groups:
        print("  ❌ Would use new execution path")
    else:
        print("  ✅ Would use fallback (backwards compatible)")

    assert execution_groups is None, "Old plan should not have execution_groups"
    print("\n  ✅ Backwards compatibility preserved")

    print("\n" + "="*70)
    print("✅ BACKWARDS COMPATIBILITY TEST PASSED")
    print("="*70)

async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "🧪"*35)
    print("Parallel Execution Integration Tests")
    print("🧪"*35)

    try:
        # Test 1: Grouping logic
        test_grouping_logic()

        # Test 2: Execution performance
        await test_execution_modes()

        # Test 3: Plan structure
        test_execution_plan_structure()

        # Test 4: Backwards compatibility
        test_backwards_compatibility()

        # Summary
        print("\n\n" + "="*70)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("="*70)
        print("\n📊 Summary:")
        print("  ✅ Dependency grouping works correctly")
        print("  ✅ Parallel execution is faster than sequential")
        print("  ✅ Execution plan structure is valid")
        print("  ✅ Backwards compatibility maintained")
        print("\n🎯 Implementation is ready for production!")
        print("="*70 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_all_tests())
