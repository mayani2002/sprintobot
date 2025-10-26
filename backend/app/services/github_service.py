"""
GitHub Service Layer
Handles business logic for GitHub operations
"""
from typing import Dict, Any, List
import os
from app.integrations.github_integration import GitHubIntegration
from app.services.ai_service import AIService

class GitHubService:
    def __init__(self):
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        
        self.integration = GitHubIntegration(token=github_token)
        self.ai_service = AIService()
    
    async def process_natural_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query about GitHub and return results.
        Now uses intelligent single-pass or iterative execution.
        """
        try:
            print(f"\n{'='*70}")
            print(f"🎯 Processing Natural Query")
            print(f"{'='*70}")
            
            # Use the new intelligent handler
            execution_plan = await self.ai_service.handle_natural_query(query)

            # Handle clarification requests
            if execution_plan.get("needs_clarification"):
                print(f"\n❓ Clarification needed")
                return {
                    "query": query,
                    "needs_clarification": True,
                    "clarifying_questions": execution_plan.get("clarifying_questions", []),
                    "partial_plan": execution_plan.get("function_calls", []),
                    "success": False,
                    "message": "Please provide additional information to complete this query."
                }

            if "error" in execution_plan and not execution_plan.get("function_calls"):
                return execution_plan
            
            # Execute all planned function calls with parameter injection
            final_results = []
            accumulated_context = {}

            # Check if we have grouped execution plan (new) or flat list (old)
            execution_groups = execution_plan.get("execution_groups")

            if execution_groups:
                # NEW: Group-based execution (supports parallel + sequential)
                print(f"\n📋 Executing {len(execution_groups)} execution group(s)")

                for group in execution_groups:
                    step = group.get("step")
                    mode = group.get("mode")
                    calls = group.get("calls", [])
                    description = group.get("description", "")

                    # EXPAND "top N" calls into multiple parallel calls
                    expanded_calls = self._expand_top_n_calls(calls, accumulated_context)
                    if len(expanded_calls) != len(calls):
                        print(f"   ⚡ Expanded {len(calls)} call(s) into {len(expanded_calls)} call(s) for 'top N' query")
                        calls = expanded_calls
                        # If we expanded, it should be parallel
                        if len(calls) > 1 and mode == "sequential":
                            mode = "parallel"
                            print(f"   ⚡ Switched to parallel mode for {len(calls)} expanded calls")

                    print(f"\n{'='*70}")
                    print(f"Step {step}: {mode.upper()} - {len(calls)} function(s)")
                    if description:
                        print(f"  {description}")
                    print(f"{'='*70}")

                    if mode == "parallel":
                        # Execute concurrently
                        batch_results = await self._execute_parallel_batch(calls, accumulated_context)
                    else:  # sequential
                        # Execute one by one
                        batch_results = await self._execute_sequential_batch(calls, accumulated_context)

                    final_results.extend(batch_results)
            else:
                # FALLBACK: Old-style flat execution (backwards compatible)
                print(f"\n📋 Executing {len(execution_plan.get('function_calls', []))} function call(s) (legacy mode)")
                batch_results = await self._execute_sequential_batch(
                    execution_plan.get("function_calls", []),
                    accumulated_context
                )
                final_results.extend(batch_results)
            
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

    def _resolve_placeholders(self, parameters: Dict[str, Any],
                              context: Dict[str, Any],
                              purpose: str = "") -> Dict[str, Any]:
        """
        Resolve placeholder parameters using data from previous function calls.

        This enables sequential function calling where Step 1 discovers parameters
        that Step 2 needs.

        Example:
            Step 1: get_authenticated_user_repositories()
                    Returns: [{"owner": {"login": "john"}, "name": "myproject"}]

            Step 2: get_merged_prs_last_n_days(owner=?, repo=?, n=7)
                    Inject: owner="john", repo="myproject"

        Args:
            parameters: Original parameters (may have None/missing values)
            context: Results from previous function calls
            purpose: Description of what this call is trying to do

        Returns:
            Parameters with placeholders resolved
        """
        resolved = dict(parameters)

        # Check if we have repository discovery results
        if "get_authenticated_user_repositories" in context:
            repos = context["get_authenticated_user_repositories"]

            if isinstance(repos, list) and len(repos) > 0:
                # If multiple repos found, use most recently updated (assumption)
                # Sort by updated_at if available
                sorted_repos = sorted(
                    repos,
                    key=lambda r: r.get("updated_at", ""),
                    reverse=True
                )
                selected_repo = sorted_repos[0]

                # If more than 3 repos, add metadata for potential user confirmation
                if len(repos) > 3:
                    print(f"      ⚠️  Found {len(repos)} repositories, using most recent: {selected_repo.get('name')}")
                    resolved["_discovered_repo_count"] = len(repos)
                    resolved["_repo_options"] = [
                        f"{r.get('owner', {}).get('login')}/{r.get('name')}"
                        for r in sorted_repos[:5]
                    ]

                # Inject owner if missing
                if "owner" not in resolved or resolved["owner"] is None:
                    owner_login = selected_repo.get("owner", {}).get("login")
                    if owner_login:
                        resolved["owner"] = owner_login
                        print(f"      ↳ Discovered owner: {owner_login}")

                # Inject repo if missing
                if "repo" not in resolved or resolved["repo"] is None:
                    repo_name = selected_repo.get("name")
                    if repo_name:
                        resolved["repo"] = repo_name
                        print(f"      ↳ Discovered repo: {repo_name}")

                # Inject organization if missing (from owner)
                if "organization" not in resolved or resolved["organization"] is None:
                    owner_login = selected_repo.get("owner", {}).get("login")
                    if owner_login:
                        resolved["organization"] = owner_login
                        print(f"      ↳ Discovered organization: {owner_login}")

        # Check if we have user repository results (different structure)
        if "get_user_repositories" in context:
            repos = context["get_user_repositories"]

            if isinstance(repos, list) and len(repos) > 0:
                # Sort by most recently updated
                sorted_repos = sorted(
                    repos,
                    key=lambda r: r.get("updated_at", ""),
                    reverse=True
                )
                first_repo = sorted_repos[0]

                if len(repos) > 3:
                    print(f"      ⚠️  Found {len(repos)} repositories, using most recent: {first_repo.get('name')}")

                # Extract owner and repo from full_name (format: "owner/repo")
                full_name = first_repo.get("full_name", "")
                print(f"      🔍 Repo data: full_name={full_name}")

                if "owner" not in resolved or resolved["owner"] is None:
                    if "/" in full_name:
                        owner_login = full_name.split("/", 1)[0]
                    else:
                        # Fallback: try to get from owner field (might not exist)
                        owner_login = first_repo.get("owner", {}).get("login")

                    print(f"      🔍 Extracted owner_login: {owner_login}")
                    if owner_login:
                        resolved["owner"] = owner_login
                        print(f"      ↳ Discovered owner: {owner_login}")

                if "repo" not in resolved or resolved["repo"] is None:
                    if "/" in full_name:
                        repo_name = full_name.split("/", 1)[1]
                    else:
                        # Fallback: try to get from name field
                        repo_name = first_repo.get("name")

                    if repo_name:
                        resolved["repo"] = repo_name
                        print(f"      ↳ Discovered repo: {repo_name}")

        # Check if we have organization repositories
        if "get_organization_repositories" in context:
            repos = context["get_organization_repositories"]

            if isinstance(repos, list) and len(repos) > 0:
                first_repo = repos[0]

                if "owner" not in resolved or resolved["owner"] is None:
                    resolved["owner"] = first_repo.get("owner", {}).get("login")

                if "repo" not in resolved or resolved["repo"] is None:
                    resolved["repo"] = first_repo.get("name")

        return resolved

    def _expand_top_n_calls(self, calls: List[Dict[str, Any]],
                           accumulated_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Expand calls with _top_n parameter into multiple parallel calls.

        When a query asks for "top N repositories", this expands 1 placeholder call
        into N concrete calls with actual repo parameters.

        Args:
            calls: Original function calls
            accumulated_context: Context with discovered repositories

        Returns:
            Expanded list of calls (may be same as input if no expansion needed)
        """
        expanded = []

        for call_info in calls:
            parameters = call_info.get("parameters", {})
            top_n = parameters.get("_top_n")

            if top_n and call_info.get("placeholder"):
                # This call needs to be expanded into N calls
                print(f"\n   🔍 Expanding call for top {top_n} repositories...")

                # Get discovered repositories
                repos = None
                for repo_func in ["get_authenticated_user_repositories", "get_user_repositories", "get_organization_repositories"]:
                    if repo_func in accumulated_context:
                        repos = accumulated_context[repo_func]
                        break

                if repos and isinstance(repos, list) and len(repos) > 0:
                    # Sort by most recent (updated_at)
                    sorted_repos = sorted(
                        repos,
                        key=lambda r: r.get("updated_at", r.get("pushed_at", "")),
                        reverse=True
                    )

                    # Take top N
                    top_repos = sorted_repos[:min(top_n, len(sorted_repos))]
                    print(f"      Found {len(repos)} repos, using top {len(top_repos)}")

                    # Create N calls, one for each repo
                    for idx, repo in enumerate(top_repos, 1):
                        # Extract owner from full_name (format: "owner/repo")
                        full_name = repo.get("full_name", "")
                        if "/" in full_name:
                            owner_login, repo_name = full_name.split("/", 1)
                        else:
                            # Fallback: try to get from owner field (might not exist)
                            owner_login = repo.get("owner", {}).get("login")
                            repo_name = repo.get("name")

                        if owner_login and repo_name:
                            # Clone the call but with concrete parameters
                            expanded_call = dict(call_info)
                            expanded_params = dict(parameters)

                            # Remove the _top_n marker
                            expanded_params.pop("_top_n", None)

                            # Add concrete owner/repo
                            expanded_params["owner"] = owner_login
                            expanded_params["repo"] = repo_name

                            expanded_call["parameters"] = expanded_params
                            expanded_call["placeholder"] = False  # No longer a placeholder!
                            expanded_call["step"] = call_info.get("step", 0) + idx - 1

                            expanded.append(expanded_call)
                            print(f"      [{idx}] {owner_login}/{repo_name}")

                    if not expanded:
                        print(f"      ⚠️  Could not extract owner/repo from discovered repos")
                        expanded.append(call_info)
                else:
                    print(f"      ⚠️  No repos found in context for expansion")
                    # Keep original call
                    expanded.append(call_info)
            else:
                # No expansion needed
                expanded.append(call_info)

        return expanded

    async def _execute_parallel_batch(self, calls: List[Dict[str, Any]],
                                      accumulated_context: Dict[str, Any]) -> List[Any]:
        """
        Execute multiple independent function calls concurrently using asyncio.gather.

        This dramatically improves performance for independent operations by running
        them simultaneously instead of sequentially.

        Args:
            calls: List of function call dictionaries
            accumulated_context: Shared context from previous steps

        Returns:
            List of results (same order as input calls)
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
                original_params = dict(parameters)
                parameters = self._resolve_placeholders(
                    parameters,
                    accumulated_context,
                    call_info.get("purpose", "")
                )
                if parameters != original_params:
                    print(f"  [{idx}] Injected params for {function_name}: {parameters}")

            print(f"  [{idx}] Queuing: {function_name}({parameters})")

            # Create async task
            if hasattr(self.integration, function_name):
                # Filter out metadata fields before calling API
                clean_params = {
                    k: v for k, v in parameters.items()
                    if not k.startswith('_')
                }
                method = getattr(self.integration, function_name)
                tasks.append(method(**clean_params))
                call_info_list.append(call_info)
            else:
                print(f"      ⚠️  Unknown function: {function_name}")
                # Add dummy task that returns error
                async def error_task():
                    return {"error": f"Function {function_name} not found"}
                tasks.append(error_task())
                call_info_list.append(call_info)

        # Execute ALL tasks concurrently
        print(f"\n  ⚡ Executing all {len(tasks)} functions simultaneously...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        final_results = []
        for idx, (result, call_info) in enumerate(zip(results, call_info_list), 1):
            if isinstance(result, Exception):
                print(f"    ❌ [{idx}] {call_info['function']} failed: {str(result)}")
                call_info["error"] = str(result)
                call_info["result"] = {"error": str(result)}
                final_results.append({"error": str(result)})
            else:
                if isinstance(result, list):
                    result_summary = f"{len(result)} items"
                elif isinstance(result, dict) and "error" in result:
                    result_summary = f"Error: {result.get('error')}"
                else:
                    result_summary = "completed"

                print(f"    ✅ [{idx}] {call_info['function']}: {result_summary}")
                call_info["result"] = result
                call_info["placeholder"] = False
                final_results.append(result)

                # Store in context for potential next steps
                accumulated_context[call_info["function"]] = result

        return final_results

    async def _execute_sequential_batch(self, calls: List[Dict[str, Any]],
                                        accumulated_context: Dict[str, Any]) -> List[Any]:
        """
        Execute function calls sequentially (one after another).

        Used when functions have dependencies or when there's only a single call.

        Args:
            calls: List of function call dictionaries
            accumulated_context: Shared context from previous steps

        Returns:
            List of results (same order as input calls)
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
                    # Filter out metadata fields before calling API
                    clean_params = {
                        k: v for k, v in parameters.items()
                        if not k.startswith('_')
                    }
                    method = getattr(self.integration, function_name)
                    result = await method(**clean_params)
                    results.append(result)
                    call_info["result"] = result
                    call_info["placeholder"] = False
                    accumulated_context[function_name] = result

                    if isinstance(result, list):
                        result_summary = f"{len(result)} items"
                    elif isinstance(result, dict) and "error" in result:
                        result_summary = f"Error: {result.get('error')}"
                    else:
                        result_summary = "completed"

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
                call_info["result"] = {"error": error_msg}
                results.append({"error": error_msg})

        return results
