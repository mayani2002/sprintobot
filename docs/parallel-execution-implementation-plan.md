# Parallel Execution Implementation Plan

## Overview
Implement parallel execution support for independent function calls to achieve 50-90% performance improvement.

---

## Architecture Design

### Current Flow
```
Query → AI Plans (list of calls) → Execute (for loop) → Results
```

### New Flow
```
Query → AI Plans (grouped by dependencies) → Execute (parallel + sequential) → Results
                ↓
        {
          "execution_groups": [
            {
              "step": 1,
              "mode": "sequential",
              "calls": [discovery_call]
            },
            {
              "step": 2,
              "mode": "parallel",
              "depends_on": 1,
              "calls": [call1, call2, call3]
            }
          ]
        }
```

---

## Implementation Steps

### Step 1: Add Execution Group Structure

**Changes to `ai_service.py`**

Add new method `_group_by_dependencies()`:
```python
def _group_by_dependencies(self, function_calls: List[Dict]) -> List[Dict]:
    """
    Group function calls into parallel and sequential batches.

    Rules:
    1. Functions with placeholder=True must run sequentially (need discovery)
    2. Functions with placeholder=False can run in parallel
    3. Discovery calls always run first
    """
    groups = []

    # Separate discovery (sequential) from execution (potentially parallel)
    discovery_calls = [c for c in function_calls if c.get("purpose") == "Discovery"]
    execution_calls = [c for c in function_calls if c.get("purpose") != "Discovery"]

    # Group 1: Discovery (always sequential)
    if discovery_calls:
        groups.append({
            "step": 1,
            "mode": "sequential",
            "calls": discovery_calls
        })

    # Group 2: Execution
    if execution_calls:
        # Check if all execution calls are independent (no placeholders)
        has_placeholders = any(c.get("placeholder") for c in execution_calls)

        if not has_placeholders and len(execution_calls) > 1:
            # Multiple independent calls - can parallelize
            groups.append({
                "step": len(groups) + 1,
                "mode": "parallel",
                "calls": execution_calls,
                "depends_on": len(groups) if groups else None
            })
        else:
            # Has dependencies - must be sequential
            groups.append({
                "step": len(groups) + 1,
                "mode": "sequential",
                "calls": execution_calls,
                "depends_on": len(groups) if groups else None
            })

    return groups
```

**Update `_plan_iterative()` to use grouping:**
```python
# OLD CODE:
execution_state["function_calls"].append({
    "function": step.get("action"),
    "parameters": {},
    "placeholder": True,
    "step": step.get("step", 1)
})

# NEW CODE:
all_calls = []
# ... collect all calls ...

# Group by dependencies
execution_state["execution_groups"] = self._group_by_dependencies(all_calls)
execution_state["function_calls"] = all_calls  # Keep for backwards compatibility
```

---

### Step 2: Implement Parallel Executor

**Changes to `github_service.py`**

Add new method `_execute_parallel_batch()`:
```python
async def _execute_parallel_batch(self, calls: List[Dict], accumulated_context: Dict) -> List[Any]:
    """
    Execute multiple independent function calls concurrently.

    Uses asyncio.gather to run all functions simultaneously.
    Handles errors per-function without failing the entire batch.
    """
    import asyncio

    print(f"\n⚡ PARALLEL EXECUTION: {len(calls)} function(s)")
    print("─" * 60)

    tasks = []
    call_info_list = []

    for idx, call_info in enumerate(calls, 1):
        function_name = call_info.get("function")
        parameters = call_info.get("parameters", {})

        # Resolve placeholders if needed
        if call_info.get("placeholder"):
            parameters = self._resolve_placeholders(
                parameters,
                accumulated_context,
                call_info.get("purpose", "")
            )

        print(f"  [{idx}] Queuing: {function_name}({parameters})")

        # Create async task
        if hasattr(self.integration, function_name):
            method = getattr(self.integration, function_name)
            tasks.append(method(**parameters))
            call_info_list.append(call_info)
        else:
            print(f"    ⚠️  Unknown function: {function_name}")
            tasks.append(asyncio.sleep(0))  # Dummy task
            call_info_list.append(call_info)

    # Execute all tasks concurrently
    print(f"\n  ⚡ Executing all {len(tasks)} functions simultaneously...")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    final_results = []
    for idx, (result, call_info) in enumerate(zip(results, call_info_list), 1):
        if isinstance(result, Exception):
            print(f"    ❌ [{idx}] Failed: {str(result)}")
            call_info["error"] = str(result)
            call_info["result"] = {"error": str(result)}
            final_results.append({"error": str(result)})
        else:
            result_summary = f"{len(result)} items" if isinstance(result, list) else "completed"
            print(f"    ✅ [{idx}] Completed: {result_summary}")
            call_info["result"] = result
            call_info["placeholder"] = False
            final_results.append(result)

            # Store in context
            accumulated_context[call_info["function"]] = result

    return final_results
```

Add new method `_execute_sequential_batch()`:
```python
async def _execute_sequential_batch(self, calls: List[Dict], accumulated_context: Dict) -> List[Any]:
    """
    Execute function calls sequentially (existing logic, extracted to method).
    """
    print(f"\n📝 SEQUENTIAL EXECUTION: {len(calls)} function(s)")
    print("─" * 60)

    results = []

    for idx, call_info in enumerate(calls, 1):
        function_name = call_info.get("function")
        parameters = call_info.get("parameters", {})

        # Resolve placeholders
        if call_info.get("placeholder"):
            print(f"  [{idx}] Resolving placeholders for {function_name}...")
            original_params = dict(parameters)
            parameters = self._resolve_placeholders(
                parameters,
                accumulated_context,
                call_info.get("purpose", "")
            )
            if parameters != original_params:
                print(f"      ✨ Injected parameters: {parameters}")

        print(f"  [{idx}] Executing: {function_name}({parameters})")

        # Execute
        if hasattr(self.integration, function_name):
            try:
                method = getattr(self.integration, function_name)
                result = await method(**parameters)
                results.append(result)
                call_info["result"] = result
                call_info["placeholder"] = False
                accumulated_context[function_name] = result

                result_summary = f"{len(result)} items" if isinstance(result, list) else "completed"
                print(f"      ✅ Completed: {result_summary}")

            except Exception as e:
                print(f"      ❌ Failed: {str(e)}")
                call_info["error"] = str(e)
                call_info["result"] = {"error": str(e)}
                results.append({"error": str(e)})
        else:
            print(f"      ⚠️  Unknown function: {function_name}")
            error_msg = f"Function {function_name} not found"
            call_info["error"] = error_msg
            results.append({"error": error_msg})

    return results
```

---

### Step 3: Update Main Execution Loop

**Replace the existing for loop in `process_natural_query()`:**

```python
# OLD CODE (lines 53-109):
for idx, call_info in enumerate(execution_plan.get("function_calls", [])):
    # ... sequential execution ...

# NEW CODE:
# Check if we have grouped execution plan
execution_groups = execution_plan.get("execution_groups")

if execution_groups:
    # NEW: Group-based execution (parallel + sequential)
    print(f"\n📋 Executing {len(execution_groups)} group(s)")

    for group in execution_groups:
        step = group.get("step")
        mode = group.get("mode")
        calls = group.get("calls", [])

        print(f"\n{'='*70}")
        print(f"Step {step}: {mode.upper()} - {len(calls)} function(s)")
        print(f"{'='*70}")

        if mode == "parallel":
            batch_results = await self._execute_parallel_batch(calls, accumulated_context)
        else:  # sequential
            batch_results = await self._execute_sequential_batch(calls, accumulated_context)

        final_results.extend(batch_results)
else:
    # FALLBACK: Old-style flat execution (backwards compatible)
    batch_results = await self._execute_sequential_batch(
        execution_plan.get("function_calls", []),
        accumulated_context
    )
    final_results.extend(batch_results)
```

---

## Data Structure Changes

### Before (Flat List)
```python
{
  "function_calls": [
    {"step": 1, "function": "get_repos", "placeholder": False},
    {"step": 2, "function": "get_prs", "placeholder": True},
    {"step": 3, "function": "get_prs", "placeholder": True}
  ]
}
```

### After (Grouped)
```python
{
  "function_calls": [...],  # Kept for backwards compatibility
  "execution_groups": [
    {
      "step": 1,
      "mode": "sequential",
      "calls": [
        {"function": "get_repos", "placeholder": False}
      ]
    },
    {
      "step": 2,
      "mode": "parallel",
      "depends_on": 1,
      "calls": [
        {"function": "get_prs", "placeholder": True, "repo": "repo1"},
        {"function": "get_prs", "placeholder": True, "repo": "repo2"}
      ]
    }
  ]
}
```

---

## Testing Strategy

### Unit Tests

**Test 1: Dependency Grouping**
```python
def test_group_by_dependencies():
    calls = [
        {"function": "get_repos", "placeholder": False, "purpose": "Discovery"},
        {"function": "get_prs", "placeholder": True, "purpose": "Execute"},
        {"function": "get_prs", "placeholder": True, "purpose": "Execute"}
    ]

    groups = ai_service._group_by_dependencies(calls)

    assert len(groups) == 2
    assert groups[0]["mode"] == "sequential"
    assert groups[1]["mode"] == "sequential"  # Has placeholders
```

**Test 2: Parallel Detection**
```python
def test_parallel_detection():
    calls = [
        {"function": "get_prs", "placeholder": False, "repo": "repo1"},
        {"function": "get_prs", "placeholder": False, "repo": "repo2"}
    ]

    groups = ai_service._group_by_dependencies(calls)

    assert len(groups) == 1
    assert groups[0]["mode"] == "parallel"
    assert len(groups[0]["calls"]) == 2
```

### Integration Tests

**Test 3: Parallel Execution**
```python
async def test_parallel_execution():
    query = "Get PRs for repo1, repo2, repo3"

    result = await github_service.process_natural_query(query)

    assert result["success"] == True
    assert "execution_groups" in result["execution_plan"]
    assert any(g["mode"] == "parallel" for g in result["execution_plan"]["execution_groups"])
```

**Test 4: Mixed Execution**
```python
async def test_mixed_execution():
    query = "Get my repos and show PRs for each"

    result = await github_service.process_natural_query(query)

    groups = result["execution_plan"]["execution_groups"]
    assert len(groups) >= 2
    assert groups[0]["mode"] == "sequential"  # Discovery
    # Second group should be parallel if multiple repos
```

---

## Rollout Plan

### Phase 1: Implementation (4 hours)
- [ ] Add `_group_by_dependencies()` to ai_service.py
- [ ] Add `_execute_parallel_batch()` to github_service.py
- [ ] Add `_execute_sequential_batch()` to github_service.py
- [ ] Update main execution loop

### Phase 2: Testing (2 hours)
- [ ] Unit tests for grouping logic
- [ ] Integration tests with mock functions
- [ ] Real API tests with GitHub

### Phase 3: Monitoring (1 hour)
- [ ] Add execution time tracking
- [ ] Add parallel efficiency metrics
- [ ] Log parallel vs sequential decisions

### Phase 4: Documentation (1 hour)
- [ ] Update API documentation
- [ ] Add examples to README
- [ ] Create performance comparison charts

---

## Success Criteria

- ✅ All existing tests still pass (backwards compatibility)
- ✅ Parallel execution works for independent calls
- ✅ Sequential execution preserved for dependencies
- ✅ Error handling works in both modes
- ✅ 50%+ performance improvement on multi-repo queries
- ✅ No breaking changes to API

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing queries | Keep `function_calls` for backwards compatibility |
| Parallel errors hard to debug | Add detailed logging per task |
| Race conditions | Use asyncio.gather, no shared state |
| API rate limiting | GitHub handles concurrent requests well |

---

## Implementation Checklist

- [ ] Backup current code
- [ ] Create feature branch
- [ ] Implement `_group_by_dependencies()`
- [ ] Implement `_execute_parallel_batch()`
- [ ] Implement `_execute_sequential_batch()`
- [ ] Update `_plan_iterative()`
- [ ] Update `process_natural_query()`
- [ ] Write unit tests
- [ ] Run integration tests
- [ ] Benchmark performance
- [ ] Update documentation
- [ ] Code review
- [ ] Merge to main

---

**Estimated Total Time: 8 hours**
**Expected Performance Gain: 50-90% for multi-repo queries**
