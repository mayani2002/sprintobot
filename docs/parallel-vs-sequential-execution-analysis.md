# Parallel vs Sequential Function Calling Analysis

## Current Implementation Status

### ✅ Sequential Execution: **IMPLEMENTED**
### ❌ Parallel Execution: **NOT IMPLEMENTED**

---

## What is Currently Working

### Sequential Execution (Dependency-Based)

**Definition:** Functions execute in a planned order where later steps depend on earlier results.

**Current Implementation:**
```
Step 1: get_authenticated_user_repositories()
  ↓ (passes owner/repo to next step)
Step 2: get_merged_prs_last_n_days(owner, repo, n=7)
  ↓
Result
```

**Code Location:** `github_service.py:53-109` (for loop execution)

**Example:**
```python
for idx, call_info in enumerate(execution_plan.get("function_calls", []), 1):
    # Execute each function one after another
    result = await method(**parameters)
    accumulated_context[function_name] = result  # Pass to next step
```

**✅ Working Features:**
- Parameter injection from previous results
- Accumulated context across steps
- Proper dependency resolution
- Error handling per step

---

## What is Missing

### Parallel Execution (Independence-Based)

**Definition:** Functions that don't depend on each other execute simultaneously for better efficiency.

**Why It's Important:**

| Scenario | Current (Sequential) | With Parallel | Time Saved |
|----------|---------------------|---------------|------------|
| Query 3 repos | 3 × 500ms = 1500ms | max(500ms) = 500ms | **67%** |
| Check 5 security settings | 5 × 300ms = 1500ms | max(300ms) = 300ms | **80%** |
| Get details for 10 PRs | 10 × 400ms = 4000ms | max(400ms) = 400ms | **90%** |

---

## Use Cases for Parallel Execution

### Example 1: Multi-Repository Query
**User Query:** "Show me PRs across all my repositories"

**Current (Sequential):**
```
Get repo 1 PRs → 500ms
Get repo 2 PRs → 500ms
Get repo 3 PRs → 500ms
Get repo 4 PRs → 500ms
Total: 2000ms
```

**With Parallel:**
```
Get repo 1 PRs ┐
Get repo 2 PRs ├─ 500ms (all at once)
Get repo 3 PRs │
Get repo 4 PRs ┘
Total: 500ms (75% faster!)
```

---

### Example 2: Security Audit
**User Query:** "Check security settings for all repositories"

**Current (Sequential):**
```
For each repo:
  Check vulnerability alerts → 300ms
  Check private reporting → 300ms
  Check branch protection → 300ms

Total: 3 repos × 900ms = 2700ms
```

**With Parallel:**
```
Repo 1 ┐
Repo 2 ├─ All security checks in parallel → 900ms
Repo 3 ┘

Total: 900ms (66% faster!)
```

---

### Example 3: Mixed Dependencies
**User Query:** "Get PRs and contributors for my top 5 repos"

**Optimal Execution:**
```
Step 1: get_authenticated_user_repositories() → 500ms

Step 2 (parallel batch):
├─ get_prs(repo1) ────────┐
├─ get_contributors(repo1) │
├─ get_prs(repo2) ─────────┤
├─ get_contributors(repo2) ├─ 600ms (all parallel)
├─ get_prs(repo3) ─────────│
└─ get_contributors(repo3) ┘

Total: 1100ms

vs Sequential: 500ms + (6 × 600ms) = 4100ms
Speedup: 73% faster
```

---

## How to Implement Parallel Execution

### 1. Add "Parallel Groups" to Execution Plan

**Current Plan Structure:**
```python
{
  "function_calls": [
    {"step": 1, "function": "get_repos", "parameters": {}},
    {"step": 2, "function": "get_prs", "parameters": {}}
  ]
}
```

**New Plan Structure with Groups:**
```python
{
  "function_calls": [
    {
      "step": 1,
      "execution_mode": "sequential",  # Must run first
      "functions": [
        {"function": "get_repos", "parameters": {}}
      ]
    },
    {
      "step": 2,
      "execution_mode": "parallel",  # Can run simultaneously
      "depends_on_step": 1,
      "functions": [
        {"function": "get_prs", "parameters": {"repo": "repo1"}},
        {"function": "get_prs", "parameters": {"repo": "repo2"}},
        {"function": "get_prs", "parameters": {"repo": "repo3"}}
      ]
    }
  ]
}
```

---

### 2. Update AI Planning Logic

**File:** `ai_service.py:_plan_iterative()`

**Current Logic:**
```python
for step in discovery_steps:
    execution_state["function_calls"].append({
        "function": step.get("action"),
        "step": step.get("step", 1)
    })
```

**Enhanced Logic:**
```python
# Group functions by dependencies
parallel_group = []
sequential_steps = []

for call in all_function_calls:
    if call.has_dependencies():
        sequential_steps.append(call)
    else:
        parallel_group.append(call)

# Create execution plan with groups
if parallel_group:
    execution_state["function_calls"].append({
        "step": 1,
        "execution_mode": "parallel",
        "functions": parallel_group
    })
```

---

### 3. Update Execution Engine

**File:** `github_service.py:process_natural_query()`

**Current Execution:**
```python
for idx, call_info in enumerate(execution_plan.get("function_calls", []), 1):
    result = await method(**parameters)  # One at a time
```

**Enhanced Execution:**
```python
for step_group in execution_plan.get("function_calls", []):
    execution_mode = step_group.get("execution_mode", "sequential")

    if execution_mode == "parallel":
        # Execute all functions in this group concurrently
        tasks = []
        for call in step_group["functions"]:
            method = getattr(self.integration, call["function"])
            tasks.append(method(**call["parameters"]))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    else:  # sequential
        for call in step_group["functions"]:
            result = await method(**call["parameters"])
```

---

## Dependency Detection Algorithm

### How to Determine if Functions Can Run in Parallel

**Rule 1: Same Parameters = Can Parallelize**
```python
get_prs(owner="user", repo="repo1")  ┐
get_prs(owner="user", repo="repo2")  ├─ PARALLEL ✓
get_prs(owner="user", repo="repo3")  ┘
# Same function, different repos, no dependency
```

**Rule 2: Different Functions, No Shared State = Can Parallelize**
```python
get_prs(repo="myrepo")          ┐
get_contributors(repo="myrepo") ├─ PARALLEL ✓
get_languages(repo="myrepo")    ┘
# Different data, no dependency
```

**Rule 3: Output Used as Input = Must be Sequential**
```python
repos = get_repos()              # Step 1: SEQUENTIAL
prs = get_prs(repo=repos[0])    # Step 2: Depends on Step 1
```

**Rule 4: Placeholder Parameters = Depends on Discovery**
```python
{
  "function": "get_prs",
  "parameters": {"owner": None, "repo": None},  # Placeholders
  "placeholder": True  # ← Depends on previous discovery
}
# Must wait for discovery step first
```

---

## Implementation Pseudocode

### AI Service Enhancement

```python
def _create_parallel_execution_plan(self, function_calls: List[Dict]) -> List[Dict]:
    """
    Analyze function calls and group into parallel/sequential steps.
    """
    steps = []
    current_step = 1

    # Separate by dependencies
    independent_calls = []
    dependent_calls = []

    for call in function_calls:
        if call.get("placeholder") or call.get("depends_on"):
            dependent_calls.append(call)
        else:
            independent_calls.append(call)

    # Create parallel group for independent calls
    if independent_calls:
        steps.append({
            "step": current_step,
            "execution_mode": "parallel",
            "functions": independent_calls
        })
        current_step += 1

    # Create sequential group for dependent calls
    if dependent_calls:
        steps.append({
            "step": current_step,
            "execution_mode": "sequential",
            "functions": dependent_calls,
            "depends_on_step": current_step - 1
        })

    return steps
```

### GitHub Service Enhancement

```python
async def _execute_parallel_group(self, functions: List[Dict]) -> List[Any]:
    """
    Execute multiple functions concurrently using asyncio.gather.
    """
    tasks = []

    for call in functions:
        method = getattr(self.integration, call["function"])
        tasks.append(method(**call["parameters"]))

    print(f"⚡ Executing {len(tasks)} functions in parallel...")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle errors
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  ❌ Function {functions[idx]['function']} failed: {result}")
        else:
            print(f"  ✅ Function {functions[idx]['function']} completed")

    return results
```

---

## Testing Parallel Execution

### Test Case 1: Independent Queries
```python
query = "Get PRs for repo1, repo2, and repo3"

# Expected plan:
{
  "step": 1,
  "execution_mode": "parallel",
  "functions": [
    {"function": "get_prs", "parameters": {"repo": "repo1"}},
    {"function": "get_prs", "parameters": {"repo": "repo2"}},
    {"function": "get_prs", "parameters": {"repo": "repo3"}}
  ]
}

# Expected timing: ~1× API call time (not 3×)
```

### Test Case 2: Mixed Dependencies
```python
query = "Show me my repos and get PRs for each"

# Expected plan:
[
  {
    "step": 1,
    "execution_mode": "sequential",
    "functions": [{"function": "get_repos"}]
  },
  {
    "step": 2,
    "execution_mode": "parallel",
    "depends_on_step": 1,
    "functions": [
      {"function": "get_prs", "parameters": {"repo": "{from_step_1}"}},
      {"function": "get_prs", "parameters": {"repo": "{from_step_1}"}},
    ]
  }
]
```

---

## Performance Metrics

### Key Metrics to Track

1. **Parallelization Ratio**
   ```
   parallel_calls / total_calls

   Example: 8 parallel / 10 total = 80% parallelization
   ```

2. **Time Savings**
   ```
   sequential_time - parallel_time / sequential_time × 100%

   Example: (4000ms - 500ms) / 4000ms = 87.5% faster
   ```

3. **Efficiency Score**
   ```
   operations_per_second = total_calls / execution_time

   Sequential: 10 calls / 5s = 2 ops/sec
   Parallel: 10 calls / 1s = 10 ops/sec (5× better)
   ```

---

## Summary

### Current State
- ✅ Sequential execution with dependency resolution **WORKING**
- ✅ Parameter injection from previous results **WORKING**
- ❌ Parallel execution for independent calls **NOT IMPLEMENTED**

### Benefits of Adding Parallel Execution
- 🚀 **50-90% faster** for multi-repo queries
- ⚡ **Better resource utilization** (concurrent API calls)
- 🎯 **Scales better** as query complexity grows
- 💰 **Lower token costs** (fewer LLM retries due to timeouts)

### Implementation Effort
- **AI Planning:** 2-3 hours (group functions by dependencies)
- **Execution Engine:** 2-3 hours (add asyncio.gather support)
- **Testing:** 1-2 hours (parallel vs sequential benchmarks)

**Total Estimate:** 5-8 hours of development

---

## Next Steps

1. ✅ Document current state (this file)
2. ⬜ Implement parallel execution in AI planner
3. ⬜ Add asyncio.gather to github_service
4. ⬜ Create benchmark tests
5. ⬜ Add execution mode to API response
6. ⬜ Update frontend to show parallel execution
