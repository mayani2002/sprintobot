# Sequential Function Calling for LLM Calls - Complete Guide

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Implementation Patterns](#implementation-patterns)
- [Current Implementation Analysis](#current-implementation-analysis)
- [Improvements & Best Practices](#improvements--best-practices)
- [Code Examples](#code-examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

Sequential function calling is a technique where an LLM makes multiple function calls in sequence, where later calls may depend on the results of earlier calls. This is essential for complex queries that require multi-step data gathering.

### Use Cases in Sprintobot

1. **Parameter Discovery**: Query lacks owner/repo → discover via `get_authenticated_user_repositories()` → use in subsequent calls
2. **Data Enrichment**: Get PR list → fetch details for each PR → aggregate results
3. **Conditional Execution**: Check if feature enabled → execute feature-specific functions

---

## Architecture

### Two-Phase Approach (Current Implementation)

```
┌─────────────────────────────────────────────────────────────┐
│                      USER QUERY                              │
│            "Show me PRs merged in last 7 days"              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: PLANNING                         │
│                    (ai_service.py)                           │
│                                                              │
│  1. Analyze query complexity                                │
│  2. Detect missing parameters (owner, repo)                 │
│  3. Determine execution strategy:                           │
│     - Single-pass (all params available)                    │
│     - Iterative (needs discovery)                           │
│  4. Create execution plan with function calls               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   PHASE 2: EXECUTION                         │
│                  (github_service.py)                         │
│                                                              │
│  1. Execute function calls in sequence                      │
│  2. Inject discovered parameters from previous results      │
│  3. Collect results                                         │
│  4. Return aggregated data                                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | File | Responsibility |
|-----------|------|----------------|
| AIService | `ai_service.py` | Query analysis, plan creation |
| GitHubService | `github_service.py` | Plan execution, function calls |
| GitHubIntegration | `github_integration.py` | Low-level GitHub API calls |
| Function Declarations | `github_function_declarations.py` | Schema definitions for LLM |

---

## Implementation Patterns

### Pattern 1: Single-Pass Execution

**When to use:** All required parameters are provided in the query

```
Query: "Get merged PRs for owner/repo in last 7 days"
       ↓
LLM Analysis: All params available
       ↓
Single Function Call: get_merged_prs_last_n_days(owner="owner", repo="repo", n=7)
       ↓
Results
```

**Code Location:** `ai_service.py:489-548` (`_plan_single_pass`)

**Characteristics:**
- ✅ Fast (1 LLM call)
- ✅ Low token usage
- ✅ Predictable
- ❌ Requires complete information upfront

---

### Pattern 2: Multi-Step Sequential Execution

**When to use:** Missing parameters need to be discovered

```
Query: "Show me PRs merged in last 7 days" (no repo specified)
       ↓
LLM Analysis: Missing owner/repo, has n=7
       ↓
Step 1: get_authenticated_user_repositories()
       ↓
Extract: owner="myuser", repo="myrepo"
       ↓
Step 2: get_merged_prs_last_n_days(owner="myuser", repo="myrepo", n=7)
       ↓
Results
```

**Code Location:** `ai_service.py:550-611` (`_plan_iterative`)

**Characteristics:**
- ✅ Handles incomplete queries
- ✅ Auto-discovers parameters
- ⚠️ Needs parameter injection (currently missing)
- ❌ Slightly higher latency

---

### Pattern 3: LLM-Orchestrated Sequential Execution

**When to use:** Complex queries requiring adaptive decision-making

```
Query: "Find PRs that need attention"
       ↓
LLM Turn 1: Call get_prs_waiting_for_review(hours=24)
       ↓
LLM sees results: 5 PRs found
       ↓
LLM Turn 2: For each PR, call get_pr_reviews(pr_number=X)
       ↓
LLM sees reviews: Some have no reviews
       ↓
LLM Turn 3: Call get_pr_details() for PRs with no reviews
       ↓
Final Analysis & Results
```

**Code Location:** Not yet implemented (see Improvements section)

**Characteristics:**
- ✅ Highly adaptive
- ✅ Handles complex workflows
- ❌ High token usage (multiple LLM calls)
- ❌ Less predictable
- ❌ Requires careful iteration limits

---

## Current Implementation Analysis

### Parameter Dependency System

Your `ai_service.py` defines which parameters can be auto-discovered:

```python
parameter_dependencies = {
    "owner": {
        "can_discover": True,
        "discovery_function": "get_authenticated_user_repositories",
        "extract_from": "owner.login",
        "description": "Repository owner username"
    },
    "repo": {
        "can_discover": True,
        "discovery_function": "get_authenticated_user_repositories",
        "extract_from": "name",
        "description": "Repository name"
    },
    "pr_number": {
        "can_discover": False,
        "requires_user_input": True,
        "description": "Specific PR number"
    },
    "n": {
        "can_discover": False,
        "has_default": True,
        "default_value": 7,
        "description": "Number of days"
    }
}
```

**✅ Strengths:**
- Clear mapping of discoverable vs user-input parameters
- Default values for common parameters
- Explicit discovery functions

**⚠️ Current Limitations:**
1. **No parameter injection**: Discovered values aren't injected into subsequent calls
2. **Single repository assumption**: Always uses first repo from discovery
3. **No user confirmation**: Doesn't ask user which repo to use

---

### Execution Flow Issues

**Current code in `github_service.py:40-80`:**

```python
for idx, call_info in enumerate(execution_plan.get("function_calls", []), 1):
    function_name = call_info.get("function")
    parameters = call_info.get("parameters", {})

    # ⚠️ ISSUE: No parameter resolution from previous results
    method = getattr(self.integration, function_name)
    result = await method(**parameters)  # ← May fail if params are None
    final_results.append(result)
```

**Problem:** If Step 1 is `get_authenticated_user_repositories()` and Step 2 needs `owner` and `repo`, those parameters are `None` or placeholders.

---

### Gemini Response Parsing Issues

Lines 252-294 in `ai_service.py` show extensive debugging for Gemini's response format:

```python
# Current approach - fragile
result_text = response.text.strip()
try:
    analysis = json.loads(result_text)
except json.JSONDecodeError:
    print(f"⚠️  JSON parse failed, raw text: {result_text[:200]}")
    return self._analyze_query_complexity_fallback(query)
```

**Issues:**
- Gemini may return markdown-wrapped JSON (```json ... ```)
- Response may be structured function call instead of text
- No explicit JSON format enforcement

---

## Improvements & Best Practices

### 1. Parameter Injection Between Steps

**Add to `github_service.py`:**

```python
class GitHubService:
    def _resolve_placeholders(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
        purpose: str = ""
    ) -> Dict[str, Any]:
        """
        Resolve placeholder parameters using data from previous function calls.

        Args:
            parameters: Current function parameters (may contain None/placeholders)
            context: Results from previous function executions
            purpose: Description of what this function does (for smart selection)

        Returns:
            Parameters with placeholders resolved

        Example:
            Step 1: get_authenticated_user_repositories() → returns repos
            Step 2: get_merged_prs_last_n_days(owner=None, repo=None, n=7)
            After resolution: get_merged_prs_last_n_days(owner="foo", repo="bar", n=7)
        """
        resolved = dict(parameters)

        # If owner/repo are missing, extract from repository discovery
        if "get_authenticated_user_repositories" in context:
            repos = context["get_authenticated_user_repositories"]

            if isinstance(repos, list) and len(repos) > 0:
                # Strategy 1: Use first repo (simple)
                selected_repo = repos[0]

                # Strategy 2: Use most recently updated (smarter)
                # selected_repo = max(repos, key=lambda r: r.get('updated_at', ''))

                # Strategy 3: Ask user (best UX)
                # if len(repos) > 1:
                #     return self._ask_user_to_select_repo(repos, parameters)

                # Extract owner
                if ("owner" not in resolved or resolved["owner"] is None):
                    owner_info = selected_repo.get("owner", {})
                    if isinstance(owner_info, dict):
                        resolved["owner"] = owner_info.get("login")
                    else:
                        resolved["owner"] = str(owner_info)

                # Extract repo name
                if ("repo" not in resolved or resolved["repo"] is None):
                    resolved["repo"] = selected_repo.get("name")

                print(f"   🔍 Resolved: owner={resolved.get('owner')}, repo={resolved.get('repo')}")

        # Extract organization from repo list if needed
        if "organization" not in resolved or resolved["organization"] is None:
            if "get_authenticated_user_repositories" in context:
                repos = context["get_authenticated_user_repositories"]
                if isinstance(repos, list) and len(repos) > 0:
                    org_login = repos[0].get("owner", {}).get("login")
                    resolved["organization"] = org_login

        return resolved

    async def process_natural_query(self, query: str) -> Dict[str, Any]:
        """Enhanced version with parameter injection."""
        try:
            print(f"\n{'='*70}")
            print(f"🎯 Processing Natural Query")
            print(f"{'='*70}")

            # Get execution plan from AI service
            execution_plan = await self.ai_service.handle_natural_query(query)

            if "error" in execution_plan and not execution_plan.get("function_calls"):
                return execution_plan

            # Execute all planned function calls with context
            final_results = []
            accumulated_context = {}  # ← NEW: Store results for parameter injection

            print(f"\n📋 Executing {len(execution_plan.get('function_calls', []))} function call(s)")

            for idx, call_info in enumerate(execution_plan.get("function_calls", []), 1):
                function_name = call_info.get("function")
                parameters = call_info.get("parameters", {})

                if not function_name:
                    print(f"⚠️  Step {idx}: No function specified, skipping")
                    continue

                # ✨ NEW: Resolve placeholders using previous results
                if call_info.get("placeholder") and accumulated_context:
                    parameters = self._resolve_placeholders(
                        parameters,
                        accumulated_context,
                        call_info.get("purpose", "")
                    )

                print(f"\n{'─'*60}")
                print(f"🔧 Executing [{idx}/{len(execution_plan['function_calls'])}]: {function_name}")
                print(f"   Parameters: {parameters}")

                # Execute the function
                if hasattr(self.integration, function_name):
                    try:
                        method = getattr(self.integration, function_name)
                        result = await method(**parameters)

                        # ✨ NEW: Store result in context for next iteration
                        accumulated_context[function_name] = result

                        final_results.append(result)
                        call_info["result"] = result
                        call_info["placeholder"] = False

                        # Show result summary
                        if isinstance(result, list):
                            result_summary = f"{len(result)} items"
                        elif isinstance(result, dict) and "error" in result:
                            result_summary = f"Error: {result.get('error', 'Unknown')}"
                        else:
                            result_summary = "completed"

                        print(f"   ✅ Result: {result_summary}")

                    except Exception as e:
                        print(f"   ❌ Execution failed: {str(e)}")
                        call_info["error"] = str(e)
                        call_info["result"] = {"error": str(e)}
                        final_results.append({"error": str(e)})
                else:
                    print(f"   ⚠️  Unknown function: {function_name}")
                    error_msg = f"Function {function_name} not found in integration"
                    call_info["error"] = error_msg
                    call_info["result"] = {"error": error_msg}

            # Calculate token efficiency metric
            token_calls = execution_plan.get("iterations", 1)
            efficiency = "excellent" if token_calls == 1 else "good" if token_calls == 2 else "acceptable"

            print(f"\n{'='*70}")
            print(f"📊 Execution Summary:")
            print(f"   Method: {execution_plan.get('method', 'unknown')}")
            print(f"   Gemini calls: {token_calls}")
            print(f"   Function executions: {len(final_results)}")
            print(f"   Efficiency: {efficiency}")
            print(f"   Completed: {execution_plan.get('completed', False)}")
            print(f"{'='*70}\n")

            return {
                "query": query,
                "execution_plan": execution_plan,
                "results": final_results,
                "method": execution_plan.get("method"),
                "iterations": token_calls,
                "completed": execution_plan.get("completed"),
                "efficiency": efficiency,
                "assumptions": execution_plan.get("assumptions"),
                "success": len([r for r in final_results if not isinstance(r, dict) or "error" not in r]) > 0
            }

        except Exception as e:
            print(f"❌ Service failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "query": query,
                "success": False
            }
```

---

### 2. Fix Gemini JSON Parsing

**Update `ai_service.py` `_analyze_query_complexity` method:**

```python
async def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
    """Analyzes query complexity and parameter availability."""
    retries = 2
    backoff = 0.5
    last_error = None

    for attempt in range(retries + 1):
        try:
            functions_schema = self._get_functions_parameter_schema()

            # Improved prompt with strict JSON instructions
            analysis_prompt = f"""
Analyze this GitHub query and determine execution strategy.
Return ONLY valid JSON (no markdown, no code blocks).

Query: "{query}"

Available Functions: {json.dumps(functions_schema, indent=2)}

Return this exact JSON structure:
{{
    "complexity": "simple|moderate|complex",
    "single_pass": true or false,
    "confidence": 0.95,
    "reasoning": "brief explanation",
    "suggested_function": "exact_function_name",
    "required_parameters": ["list", "of", "params"],
    "provided_parameters": {{"param": "value"}},
    "missing_parameters": {{
        "discoverable": ["owner", "repo"],
        "has_default": ["n"],
        "needs_user_input": []
    }},
    "needs_discovery": true or false,
    "discovery_steps": [
        {{"step": 1, "action": "function_name", "purpose": "description"}}
    ],
    "estimated_steps": 1
}}
"""

            # ✨ NEW: Force JSON response format
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=analysis_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"  # ← Enforce JSON
                )
            )

            # Extract and clean response text
            result_text = response.text.strip() if response.text else ""

            # ✨ NEW: Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = re.sub(
                    r'^```json?\s*|\s*```$',
                    '',
                    result_text,
                    flags=re.MULTILINE | re.DOTALL
                )
                result_text = result_text.strip()

            # Parse JSON
            try:
                analysis = json.loads(result_text)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse failed: {e}")
                print(f"Raw text (first 500 chars): {result_text[:500]}")
                return self._analyze_query_complexity_fallback(query)

            # Validate discovery steps
            discovery_steps = []
            raw_steps = analysis.get("discovery_steps", [])
            if isinstance(raw_steps, list):
                for step in raw_steps:
                    if isinstance(step, dict):
                        action = step.get("action")
                        if action == "ask_user":
                            analysis["needs_user_input"] = True
                            analysis["clarifying_questions"] = analysis.get("clarifying_questions", [])
                            analysis["clarifying_questions"].append(
                                step.get("purpose", "Please specify the repository (owner/repo)")
                            )
                            continue
                        elif action in [f["name"] for f in self.github_functions]:
                            discovery_steps.append(step)

            analysis["discovery_steps"] = discovery_steps
            return analysis

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._analyze_query_complexity_fallback(query)

    print(f"❌ All retries failed: {str(last_error)}")
    return self._analyze_query_complexity_fallback(query)
```

---

### 3. Add User Confirmation for Discovered Parameters

**Add to `github_service.py`:**

```python
def _create_repo_selection_prompt(self, repos: List[Dict], query: str) -> Dict:
    """
    Create a user prompt to select which repository to use.

    Returns a response that the API should send back to frontend.
    """
    repo_options = []
    for repo in repos[:10]:  # Limit to 10 most recent
        owner = repo.get("owner", {}).get("login", "unknown")
        name = repo.get("name", "unknown")
        description = repo.get("description", "No description")
        updated = repo.get("updated_at", "")

        repo_options.append({
            "value": f"{owner}/{name}",
            "label": f"{owner}/{name}",
            "description": f"{description[:100]} (Updated: {updated[:10]})"
        })

    return {
        "needs_user_selection": True,
        "selection_type": "repository",
        "message": f"I found {len(repos)} repositories. Which one should I query for: '{query}'?",
        "options": repo_options,
        "original_query": query
    }
```

---

### 4. LLM Orchestration Mode (Advanced)

**Add new method to `ai_service.py`:**

```python
async def handle_query_with_orchestration(
    self,
    query: str,
    max_iterations: int = 5
) -> Dict[str, Any]:
    """
    LLM-orchestrated sequential function calling.

    The LLM sees function results and decides next steps in real-time.
    More flexible but uses more tokens than planning approach.

    Args:
        query: Natural language query
        max_iterations: Maximum number of LLM turns (safety limit)

    Returns:
        Execution results with conversation history
    """
    if not self.enabled:
        return {"error": "AI service not enabled"}

    conversation_history = []
    results = []
    iteration = 0

    # Initial user message
    conversation_history.append({
        "role": "user",
        "parts": [{"text": query}]
    })

    while iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 LLM Orchestration - Iteration {iteration}/{max_iterations}")

        try:
            # Configure with function calling
            tools = types.Tool(function_declarations=self.github_functions)
            config = types.GenerateContentConfig(
                tools=[tools],
                temperature=0.0
            )

            # Call LLM with conversation history
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=conversation_history,
                config=config
            )

            # Extract function calls
            function_calls = self._extract_function_calls(response)

            if not function_calls:
                # LLM returned final text answer
                final_text = response.text if hasattr(response, 'text') else str(response)
                conversation_history.append({
                    "role": "model",
                    "parts": [{"text": final_text}]
                })

                print(f"✅ LLM provided final answer (no more function calls)")
                break

            print(f"📞 LLM requested {len(function_calls)} function call(s)")

            # Execute all function calls from this turn
            function_responses = []

            for fc in function_calls:
                func_name = fc.get("name")
                func_args = fc.get("args", {})

                print(f"   🔧 Calling: {func_name}({func_args})")

                # Execute actual function via github_integration
                # TODO: Integrate with actual execution
                result = {"placeholder": "Implement actual execution"}

                function_responses.append({
                    "name": func_name,
                    "response": result
                })

                results.append({
                    "iteration": iteration,
                    "function": func_name,
                    "args": func_args,
                    "result": result
                })

            # Add function calls and responses to conversation
            conversation_history.append({
                "role": "model",
                "parts": [
                    {"function_call": fc}
                    for fc in function_calls
                ]
            })

            conversation_history.append({
                "role": "function",
                "parts": [
                    {
                        "function_response": {
                            "name": fr["name"],
                            "response": fr["response"]
                        }
                    }
                    for fr in function_responses
                ]
            })

        except Exception as e:
            print(f"❌ Iteration {iteration} failed: {str(e)}")
            import traceback
            traceback.print_exc()
            break

    return {
        "query": query,
        "method": "orchestration",
        "iterations": iteration,
        "results": results,
        "conversation_history": conversation_history,
        "completed": iteration < max_iterations
    }
```

---

## Code Examples

### Example 1: Simple Query (Single-Pass)

```python
# Query with all parameters
query = "Get merged PRs for anthropics/claude in last 7 days"

# Result flow:
# 1. AI analyzes → detects owner="anthropics", repo="claude", n=7
# 2. Creates single-pass plan
# 3. Executes: get_merged_prs_last_n_days(owner="anthropics", repo="claude", n=7)
# 4. Returns results

# Execution plan:
{
    "complexity": "simple",
    "single_pass": True,
    "function_calls": [
        {
            "function": "get_merged_prs_last_n_days",
            "parameters": {"owner": "anthropics", "repo": "claude", "n": 7},
            "step": 1
        }
    ],
    "iterations": 1,
    "method": "single_pass"
}
```

---

### Example 2: Multi-Step Query (Iterative)

```python
# Query without repository specified
query = "Show me PRs merged in last 7 days"

# Result flow:
# 1. AI analyzes → missing owner/repo, has n=7
# 2. Creates iterative plan with discovery
# 3. Step 1: get_authenticated_user_repositories()
#    Result: [{"owner": {"login": "myuser"}, "name": "myrepo"}, ...]
# 4. Inject parameters: owner="myuser", repo="myrepo"
# 5. Step 2: get_merged_prs_last_n_days(owner="myuser", repo="myrepo", n=7)
# 6. Returns results

# Execution plan:
{
    "complexity": "moderate",
    "single_pass": False,
    "needs_discovery": True,
    "function_calls": [
        {
            "function": "get_authenticated_user_repositories",
            "parameters": {},
            "step": 1,
            "purpose": "Discover owner, repo"
        },
        {
            "function": "get_merged_prs_last_n_days",
            "parameters": {"owner": None, "repo": None, "n": 7},
            "placeholder": True,
            "step": 2,
            "purpose": "Execute main query"
        }
    ],
    "iterations": 2,
    "method": "iterative"
}
```

---

### Example 3: Complex Query (Orchestration)

```python
# Complex adaptive query
query = "Find all PRs that have been waiting for review for more than 48 hours and show their details"

# Result flow (orchestration mode):
# Turn 1:
#   LLM → Call: get_prs_waiting_for_review(hours=48)
#   Result: [{"number": 123}, {"number": 456}, {"number": 789}]
# Turn 2:
#   LLM sees 3 PRs → Calls: get_pr_details(pr_number=123), get_pr_details(pr_number=456), get_pr_details(pr_number=789)
#   Result: Full details for each PR
# Turn 3:
#   LLM → Returns formatted summary with analysis

# This adaptive flow is NOT possible with static planning!
```

---

## Troubleshooting

### Issue 1: "Parameter X is None"

**Symptom:**
```
❌ Execution failed: get_merged_prs_last_n_days() missing required argument: 'owner'
```

**Cause:** Parameter injection not implemented

**Solution:** Implement `_resolve_placeholders()` method (see Improvement #1)

---

### Issue 2: "JSON parse failed"

**Symptom:**
```
⚠️  JSON parse failed, raw text: ```json\n{"complexity": "simple"...
```

**Cause:** Gemini returning markdown-wrapped JSON

**Solutions:**
1. Use `response_mime_type="application/json"` in GenerateContentConfig
2. Strip markdown code blocks with regex
3. Implement fallback parser

---

### Issue 3: "Using wrong repository"

**Symptom:** Query executes against first repo, not the intended one

**Cause:** No user confirmation for discovered parameters

**Solution:**
1. Implement `_create_repo_selection_prompt()`
2. Return selection options to frontend
3. Allow user to choose repository
4. Re-execute with selected repo

---

### Issue 4: "Infinite loop in orchestration"

**Symptom:** LLM keeps calling functions without stopping

**Cause:** No clear termination signal or missing iteration limit

**Solutions:**
1. Enforce `max_iterations` limit (default: 5)
2. Add explicit "stop" function the LLM can call
3. Detect when LLM returns text instead of function calls
4. Track duplicate function calls and break

---

## Performance Optimization

### Token Usage Comparison

| Approach | LLM Calls | Avg Tokens | Use Case |
|----------|-----------|------------|----------|
| Single-Pass | 1 | 500 | Simple queries with all params |
| Iterative Planning | 1-2 | 800 | Queries needing discovery |
| Orchestration | 3-5 | 2000+ | Complex adaptive workflows |

### Best Practices

1. **Prefer Single-Pass** when possible
2. **Use Iterative** for parameter discovery
3. **Reserve Orchestration** for truly complex cases
4. **Cache** repository lists to avoid repeated discovery
5. **Batch** multiple queries for same repo
6. **Limit** orchestration iterations to 5 max

---

## Future Enhancements

### 1. Smart Repository Selection
- Use embeddings to match query intent to repo
- Consider repo activity, language, topics
- Learn from user's past selections

### 2. Parallel Function Execution
- Execute independent calls in parallel
- Reduce latency for multi-step queries

### 3. Caching Layer
- Cache repository lists per user
- Cache PR lists with TTL
- Invalidate on webhook events

### 4. Confidence Scoring
- Return confidence scores for parameter extraction
- Ask for confirmation on low-confidence values
- Learn from corrections

### 5. Multi-Source Integration
- Combine GitHub + JIRA in single query
- Cross-reference data across systems
- Unified result formatting

---

## References

- **Gemini Function Calling Docs**: https://ai.google.dev/gemini-api/docs/function-calling
- **OpenAI Function Calling**: https://platform.openai.com/docs/guides/function-calling
- **Anthropic Tool Use**: https://docs.anthropic.com/claude/docs/tool-use

### Code Locations

- Main Implementation: `backend/app/services/ai_service.py`
- Execution Layer: `backend/app/services/github_service.py`
- Function Declarations: `backend/app/services/github_function_declarations.py`
- API Endpoints: `backend/app/api/v1/evidence.py`

---

## Summary

Sequential function calling enables powerful multi-step workflows:

✅ **Current Implementation:**
- Planning-based approach (1-2 LLM calls)
- Parameter dependency mapping
- Single-pass and iterative execution

⚠️ **Needs Improvement:**
- Parameter injection between steps
- JSON parsing robustness
- User confirmation for discovered values

🚀 **Advanced Option:**
- LLM orchestration for complex adaptive workflows
- Higher token cost but more flexible

**Choose the right pattern based on query complexity and your token budget!**
