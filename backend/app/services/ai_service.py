from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import re
import json
import asyncio
from google import genai
from google.genai import types
from google.genai.errors import ServerError

class AIService:
    def __init__(self):
        # Try Gemini first
        use_gemini = os.getenv("USE_GEMINI", "true").lower() == "true"
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        if use_gemini and gemini_key:
            try:
                self.client = genai.Client(api_key=gemini_key)
                self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
                self.provider = "gemini"
                self.enabled = True
                print(f"✅ Gemini AI initialized with model: {self.model_name}")
            except Exception as e:
                print(f"❌ Gemini initialization failed: {str(e)}")
                self.enabled = False
                self.provider = None
        else:
            print("⚠️  Gemini API key not configured. AI features will be disabled.")
            self.enabled = False
            self.provider = None
        
        self.max_iterations = 3
        self.prefer_single_pass = True
    
        # Lazy load function declarations to avoid circular import
        self._github_functions = None
    
        # Define parameter dependencies
        self.parameter_dependencies = {
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
            "organization": {
                "can_discover": True,
                "discovery_function": "get_authenticated_user_repositories",
                "extract_from": "owner.login",
                "description": "Organization name"
            },
            "pr_number": {
                "can_discover": False,
                "requires_user_input": True,
                "description": "Specific PR number"
            },
            "username": {
                "can_discover": True,
                "discovery_function": "get_authenticated_user_repositories",
                "extract_from": "owner.login",
                "description": "GitHub username"
            },
            "n": {
                "can_discover": False,
                "has_default": True,
                "default_value": 7,
                "description": "Number of days"
            },
            "hours": {
                "can_discover": False,
                "has_default": True,
                "default_value": 24,
                "description": "Number of hours"
            },
            "state": {
                "can_discover": False,
                "has_default": True,
                "default_value": "all",
                "description": "PR state filter"
            }
        }
    
    @property
    def github_functions(self):
        """Lazy load GitHub function declarations"""
        if self._github_functions is None:
            try:
                from .github_function_declarations import ALL_GITHUB_FUNCTIONS
                self._github_functions = ALL_GITHUB_FUNCTIONS
            except ImportError as e:
                print(f"⚠️  Could not load GitHub functions: {str(e)}")
                self._github_functions = []
        return self._github_functions
    
    # ===================================================================
    # MAIN ENTRY POINT
    # ===================================================================
    
    async def handle_natural_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        🎯 MAIN ENTRY POINT - Use this for all GitHub natural language queries.
        
        This is the NEW intelligent query handler that:
        1. Analyzes query complexity (via _analyze_query_complexity)
        2. Detects missing discoverable parameters (owner, repo, etc.)
        3. Creates execution plan (single-pass or iterative)
        4. Returns plan for github_service.py to execute
        
        DOES NOT execute functions - only plans!
        
        Flow:
        User Query → analyze complexity → plan execution → return plan
        
        Args:
            query: Natural language query (e.g., "Get PRs merged last 7 days")
            context: Optional context from previous queries
            
        Returns:
            Execution plan with function_calls array
        """
        if not self.enabled:
            print("⚠️  AI disabled, using direct fallback")
            fallback_result = self._process_query_github_fallback(query)
            return {
                "query": query,
                "function_calls": [{
                    "function": fallback_result.get("function"),
                    "parameters": fallback_result.get("parameters", {}),
                    "placeholder": True,
                    "step": 1
                }],
                "completed": True,
                "method": "fallback",
                "iterations": 1
            }
        
        print(f"\n{'='*70}")
        print(f"🎯 Processing Query: {query}")
        print(f"{'='*70}")
        
        # Initialize execution state
        execution_state = {
            "query": query,
            "iterations": 0,
            "function_calls": [],
            "intermediate_data": context or {},
            "completed": False,
            "method": "unknown"
        }
        
        try:
            # STEP 1: Analyze query complexity
            complexity_analysis = await self._analyze_query_complexity(query)
            execution_state["complexity"] = complexity_analysis.get("complexity", "unknown")
            execution_state["complexity_analysis"] = complexity_analysis
            
            print(f"📊 Query Complexity: {execution_state['complexity']}")
            
            # STEP 2: Decide execution strategy and BUILD PLAN
            if complexity_analysis.get("single_pass", False):
                print("🚀 Using Single-Pass Execution")
                return await self._plan_single_pass(query, execution_state)
            else:
                print("🔄 Using Iterative Execution")
                return await self._plan_iterative(query, execution_state)
                
        except Exception as e:
            print(f"❌ Query processing failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "query": query,
                "execution_state": execution_state
            }
    
    # ===================================================================
    # COMPLEXITY ANALYSIS
    # ===================================================================
    
    async def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analyzes query complexity and parameter availability."""
        retries = 2
        backoff = 0.5
        last_error = None

        for attempt in range(retries + 1):
            try:
                functions_schema = self._get_functions_parameter_schema()
                
                # MORE EXPLICIT prompt with strict JSON schema
                analysis_prompt = f"""
                Analyze this GitHub query and determine execution strategy:
                Query: "{query}"
                
                Available Functions: {json.dumps(functions_schema, indent=2)}
                
                CRITICAL RULES:
                1. If repo IS specified (e.g., "owner/repo"): single_pass=true
                2. If repo NOT specified but needed: single_pass=false, needs_discovery=true
                3. "Show me my repositories": single_pass=true (no params needed)
                
                Parameter Detection Rules:
                - "X days" → extract as "n": X (NOT pr_number!)
                - "X hours" → extract as "hours": X (NOT pr_number!)
                - "#123" or "PR 123" → extract as "pr_number": 123
                - "owner/repo" → extract as "owner": "owner", "repo": "repo"
                - "open/closed" → extract as "state": "open"/"closed"
                
                Return STRICT JSON (no markdown, no extra text):
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
                
                IMPORTANT: Return ONLY valid JSON, no markdown formatting!
                """
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=analysis_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )

                # Extract and parse response
                result_text = response.text.strip() if response.text else ""

                # Remove markdown code blocks if present (fallback safety)
                if result_text.startswith("```"):
                    result_text = re.sub(r'^```json?\s*|\s*```$', '', result_text, flags=re.MULTILINE).strip()
                
                # ---------- DEBUG: inspect Gemini response ----------
                try:
                    print("🔍 GEMINI RAW RESPONSE OBJECT:", type(response))
                    # response.text may be present
                    raw_text = getattr(response, "text", None)
                    if raw_text is not None:
                        print("🔍 GEMINI response.text (first 1000 chars):")
                        print(raw_text[:1000])
                    # response.candidates may be present (structured function-calling)
                    candidates = getattr(response, "candidates", None)
                    print(f"🔍 GEMINI response.candidates type: {type(candidates)}")
                    if candidates:
                        print(f"🔍 Number of candidates: {len(candidates)}")
                        for ci, cand in enumerate(candidates, 1):
                            try:
                                print(f"  - Candidate #{ci}: type={type(cand)}")
                                # attempt to inspect content.parts if available
                                content = getattr(cand, "content", None)
                                if content and getattr(content, "parts", None):
                                    parts = content.parts
                                    print(f"    parts count: {len(parts)}")
                                    for pi, part in enumerate(parts, 1):
                                        print(f"      * part #{pi}: type={type(part)}")
                                        # function_call info (if present)
                                        fc = getattr(part, "function_call", None)
                                        if fc:
                                            try:
                                                args = dict(fc.args) if getattr(fc, "args", None) else {}
                                            except Exception:
                                                args = getattr(fc, "args", None)
                                            print(f"        function_call.name: {getattr(fc, 'name', None)}")
                                            print(f"        function_call.args: {args}")
                                        # raw part text if exists
                                        part_text = getattr(part, "text", None) or getattr(part, "content", None)
                                        if part_text:
                                            snippet = part_text if isinstance(part_text, str) else str(part_text)
                                            print(f"        part text (snippet): {snippet[:300]}")
                            except Exception as e:
                                print(f"    ⚠️ Error inspecting candidate #{ci}: {e}")
                    else:
                        print("🔍 No candidates field or empty candidates")
                except Exception as e:
                    print(f"⚠️ Error while debugging Gemini response: {e}")
                # ---------- end DEBUG ----------

                # Extract JSON more carefully
                try:
                    analysis = json.loads(result_text)
                except json.JSONDecodeError:
                    print(f"⚠️  JSON parse failed, raw text: {result_text[:200]}")
                    return self._analyze_query_complexity_fallback(query)

                # Validate and clean discovery steps
                discovery_steps = []
                raw_steps = analysis.get("discovery_steps", [])
                if isinstance(raw_steps, list):
                    for step in raw_steps:
                        if isinstance(step, dict):
                            action = step.get("action")
                            if action == "ask_user":
                                # Convert to clarifying question
                                analysis["needs_user_input"] = True
                                analysis["clarifying_questions"] = analysis.get("clarifying_questions", [])
                                analysis["clarifying_questions"].append(
                                    step.get("purpose", "Please specify the repository (owner/repo)")
                                )
                                continue
                            elif action in [f["name"] for f in self.github_functions]:
                                discovery_steps.append(step)

                analysis["discovery_steps"] = discovery_steps

                # Only force iterative if missing discoverable AND not provided
                provided = analysis.get("provided_parameters", {})
                missing = analysis.get("missing_parameters", {}).get("discoverable", [])
                
                # Check if owner/repo are truly missing
                has_repo_params = all(k in provided for k in ["owner", "repo"])
                needs_repo = any(k in missing for k in ["owner", "repo"])
                
                if needs_repo and not has_repo_params:
                    print("   ⚠️  Repo params needed but not provided")
                    analysis["single_pass"] = False
                    analysis["needs_discovery"] = True
                    analysis["complexity"] = "moderate"
                
                return analysis

            except ServerError as e:
                print(f"⚠️  Attempt {attempt + 1}/{retries + 1} failed: {str(e)}")
                last_error = e
                if attempt < retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                continue
            
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                import traceback
                traceback.print_exc()
                return self._analyze_query_complexity_fallback(query)

        print(f"❌ All retries failed: {str(last_error)}")
        return self._analyze_query_complexity_fallback(query)
    
    def _get_functions_parameter_schema(self) -> Dict[str, Any]:
        """Extracts parameter schema from function declarations."""
        schema = {}
        
        for func in self.github_functions:
            func_name = func.get('name', 'unknown')
            params = func.get('parameters', {}).get('properties', {})
            required = func.get('parameters', {}).get('required', [])
            
            schema[func_name] = {
                "description": func.get('description', ''),
                "parameters": {
                    param_name: {
                        "type": param_info.get('type', 'string'),
                        "required": param_name in required,
                        "discoverable": param_name in self.parameter_dependencies and 
                                      self.parameter_dependencies[param_name].get("can_discover", False),
                        "has_default": param_name in self.parameter_dependencies and 
                                      self.parameter_dependencies[param_name].get("has_default", False)
                    }
                    for param_name, param_info in params.items()
                }
            }
        
        return schema
    
    def _analyze_query_complexity_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback complexity analysis using regex - ENHANCED."""
        query_lower = query.lower()
        
        has_repo = bool(re.search(r'(\w+)/(\w+)', query))
        has_pr_number = bool(re.search(r'#(\d+)|pr\s+(\d+)', query_lower))
        days_match = re.search(r'(\d+)\s+days?', query_lower)
        hours_match = re.search(r'(\d+)\s+hours?', query_lower)
        
        suggested_function = None
        missing_discoverable = []
        provided_params = {}
        
        # DETECT FUNCTION AND PARAMS
        if "repository" in query_lower or "repos" in query_lower and not "pr" in query_lower:
            suggested_function = "get_authenticated_user_repositories"
            # No params, no discovery needed
            
        elif "merged" in query_lower and ("pr" in query_lower or "pull request" in query_lower):
            suggested_function = "get_merged_prs_last_n_days"
            
            # Extract days parameter
            if days_match:
                provided_params["n"] = int(days_match.group(1))
            else:
                provided_params["n"] = 7  # Default
            
            # Check if repo specified
            if not has_repo:
                missing_discoverable.extend(["owner", "repo"])
        
        elif "waiting" in query_lower and "review" in query_lower:
            suggested_function = "get_prs_waiting_for_review"
            
            # Extract hours parameter
            if hours_match:
                provided_params["hours"] = int(hours_match.group(1))
            else:
                provided_params["hours"] = 24  # Default
            
            if not has_repo:
                missing_discoverable.extend(["owner", "repo"])
        
        elif has_pr_number:
            suggested_function = "get_pr_details"
            
            # Extract PR number
            pr_match = re.search(r'#(\d+)|pr\s+(\d+)', query_lower)
            if pr_match:
                pr_num = pr_match.group(1) or pr_match.group(2)
                provided_params["pr_number"] = int(pr_num)
            
            if not has_repo:
                missing_discoverable.extend(["owner", "repo"])
        
        elif "pr" in query_lower or "pull request" in query_lower:
            suggested_function = "get_prs"
            
            # Extract state if specified
            if "open" in query_lower:
                provided_params["state"] = "open"
            elif "closed" in query_lower:
                provided_params["state"] = "closed"
            
            if not has_repo:
                missing_discoverable.extend(["owner", "repo"])
        
        # Extract repo if specified
        if has_repo:
            repo_match = re.search(r'(\w+)/(\w+)', query)
            if repo_match:
                provided_params["owner"] = repo_match.group(1)
                provided_params["repo"] = repo_match.group(2)
        
        needs_discovery = len(missing_discoverable) > 0
        discovery_steps = []
        
        if needs_discovery:
            discovery_steps.append({
                "step": 1,
                "action": "get_authenticated_user_repositories",
                "purpose": f"Discover {', '.join(missing_discoverable)}"
            })
        
        return {
            "complexity": "moderate" if needs_discovery else "simple",
            "single_pass": not needs_discovery,
            "confidence": 0.75,
            "reasoning": f"Fallback: {suggested_function}, missing: {missing_discoverable}",
            "suggested_function": suggested_function,
            "required_parameters": list(provided_params.keys()) + missing_discoverable,
            "provided_parameters": provided_params,
            "missing_parameters": {
                "discoverable": missing_discoverable,
                "has_default": [],
                "needs_user_input": []
            },
            "needs_discovery": needs_discovery,
            "discovery_steps": discovery_steps,
            "estimated_steps": len(discovery_steps) + 1
        }
    
    # ===================================================================
    # PLANNING METHODS
    # ===================================================================
    
    async def _plan_single_pass(self, query: str, execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """Creates single-pass execution plan."""
        try:
            complexity_analysis = execution_state.get("complexity_analysis", {})
            suggested_function = complexity_analysis.get("suggested_function")
            confidence = complexity_analysis.get("confidence", 0)
            
            if suggested_function and confidence >= 0.9:
                params = await self._extract_parameters_for_function(
                    query, 
                    suggested_function,
                    complexity_analysis.get("provided_parameters", {})
                )
                
                execution_state["function_calls"] = [{
                    "function": suggested_function,
                    "parameters": params,
                    "placeholder": True,
                    "step": 1
                }]

                # De-duplicate function calls before grouping
                execution_state["function_calls"] = self._deduplicate_function_calls(
                    execution_state["function_calls"]
                )

                # Group function calls
                execution_state["execution_groups"] = self._group_by_dependencies(
                    execution_state["function_calls"]
                )

                execution_state["completed"] = True
                execution_state["method"] = "single_pass_direct"
                execution_state["iterations"] = 1

                return execution_state
            
            if not self.github_functions:
                return self._create_fallback_plan(query, execution_state)
            
            tools = types.Tool(function_declarations=self.github_functions)
            config = types.GenerateContentConfig(tools=[tools], temperature=0.0)
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f'Call function for: "{query}"',
                config=config
            )
            
            function_calls = self._extract_function_calls(response)
            
            if not function_calls and suggested_function:
                params = await self._extract_parameters_for_function(query, suggested_function, {})
                function_calls = [{"name": suggested_function, "args": params}]
            
            for idx, func_call in enumerate(function_calls, 1):
                execution_state["function_calls"].append({
                    "function": func_call['name'],
                    "parameters": func_call['args'],
                    "placeholder": True,
                    "step": idx
                })

            # De-duplicate function calls before grouping
            execution_state["function_calls"] = self._deduplicate_function_calls(
                execution_state["function_calls"]
            )

            # Group function calls by dependencies
            execution_state["execution_groups"] = self._group_by_dependencies(
                execution_state["function_calls"]
            )

            execution_state["completed"] = True
            execution_state["method"] = "single_pass"
            execution_state["iterations"] = 1

            return execution_state
            
        except Exception as e:
            return self._create_fallback_plan(query, execution_state)
    
    async def _plan_iterative(self, query: str, execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """Creates multi-step execution plan."""
        if not self.github_functions:
            return self._create_fallback_plan(query, execution_state)
        
        complexity_analysis = execution_state.get("complexity_analysis", {})
        
        # Check for clarifying questions first
        if complexity_analysis.get("needs_user_input"):
            execution_state["needs_clarification"] = True
            execution_state["clarifying_questions"] = complexity_analysis.get("clarifying_questions", [
                "Please specify which repository you want to query (owner/repo format)"
            ])
            return execution_state

        discovery_steps = complexity_analysis.get("discovery_steps", [])

        # VALIDATION: Ensure discovery_steps is a list
        if not isinstance(discovery_steps, list):
            print(f"⚠️  discovery_steps is not a list: {type(discovery_steps)}")
            discovery_steps = []

        # FILTER: Separate actual discovery functions from execution functions
        # Discovery functions are those that find repositories/parameters
        DISCOVERY_FUNCTIONS = {
            "get_authenticated_user_repositories",
            "get_user_repositories",
            "get_organization_repositories"
        }

        filtered_discovery_steps = []
        misplaced_execution_functions = []

        for step in discovery_steps:
            if not isinstance(step, dict):
                continue

            action = step.get("action", "")
            if action in DISCOVERY_FUNCTIONS:
                filtered_discovery_steps.append(step)
            else:
                # This is an execution function, not discovery
                print(f"   ⚠️  '{action}' is not a discovery function, will be handled separately")
                misplaced_execution_functions.append(step)

        # Use filtered discovery steps
        discovery_steps = filtered_discovery_steps

        if discovery_steps:
            for step in discovery_steps:
                # VALIDATION: Ensure step is a dict
                if not isinstance(step, dict):
                    print(f"⚠️  Step is not dict: {type(step)}, skipping")
                    continue

                # Extract parameters for this discovery step
                step_function = step.get("action", "get_authenticated_user_repositories")
                provided_params = complexity_analysis.get("provided_parameters", {})

                print(f"   🔍 Discovery step function: {step_function}")
                print(f"   📦 Provided parameters from Gemini: {provided_params}")

                step_params = await self._extract_parameters_for_function(
                    query,
                    step_function,
                    provided_params
                )

                print(f"   ✅ Extracted parameters: {step_params}")

                execution_state["function_calls"].append({
                    "function": step_function,
                    "parameters": step_params,
                    "placeholder": True,
                    "step": step.get("step", 1),
                    "purpose": step.get("purpose", "Discovery")
                })
            
            suggested_function = complexity_analysis.get("suggested_function")
            if suggested_function:
                params = await self._extract_parameters_for_function(
                    query,
                    suggested_function,
                    complexity_analysis.get("provided_parameters", {})
                )

                # Check if query asks for "top N" repositories
                top_n_match = re.search(r'top\s+(\d+)', query.lower())
                if top_n_match:
                    top_n = int(top_n_match.group(1))
                    print(f"   🔍 Detected 'top {top_n}' query - will create {top_n} parallel calls after discovery")
                    params["_top_n"] = top_n  # Mark for expansion during execution

                execution_state["function_calls"].append({
                    "function": suggested_function,
                    "parameters": params,
                    "placeholder": True,
                    "step": len(execution_state["function_calls"]) + 1,
                    "purpose": "Execute main query"
                })
        else:
            # No discovery steps - create fallback plan
            print("⚠️  No discovery steps, using fallback")
            return self._create_fallback_plan(query, execution_state)

        # De-duplicate function calls before grouping
        execution_state["function_calls"] = self._deduplicate_function_calls(
            execution_state["function_calls"]
        )

        # Group function calls by dependencies for parallel/sequential execution
        execution_state["execution_groups"] = self._group_by_dependencies(
            execution_state["function_calls"]
        )

        execution_state["completed"] = True
        execution_state["method"] = "iterative"
        execution_state["iterations"] = len(execution_state["function_calls"])

        return execution_state
    
    def _create_fallback_plan(self, query: str, execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """Creates fallback plan using regex."""
        fallback_result = self._process_query_github_fallback(query)
        execution_state["function_calls"] = [{
            "function": fallback_result.get("function"),
            "parameters": fallback_result.get("parameters", {}),
            "placeholder": True,
            "step": 1
        }]
        execution_state["completed"] = True
        execution_state["method"] = "fallback"
        execution_state["iterations"] = 0
        
        return execution_state

    # ===================================================================
    # PARALLEL EXECUTION GROUPING
    # ===================================================================

    def _group_by_dependencies(self, function_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group function calls into parallel and sequential execution batches.

        This enables parallel execution of independent calls for better performance.

        Rules:
        1. Functions with placeholder=True need discovery data (sequential)
        2. Functions with placeholder=False are independent (can parallelize)
        3. Discovery calls always run first (sequential)
        4. Multiple independent calls are grouped for parallel execution

        Args:
            function_calls: List of function call dictionaries

        Returns:
            List of execution groups with mode (parallel/sequential)
        """
        if not function_calls:
            return []

        groups = []

        # Separate discovery calls from execution calls
        discovery_calls = [c for c in function_calls if c.get("purpose") == "Discovery"]
        execution_calls = [c for c in function_calls if c.get("purpose") != "Discovery"]

        # Group 1: Discovery (always sequential)
        if discovery_calls:
            groups.append({
                "step": 1,
                "mode": "sequential",
                "calls": discovery_calls,
                "description": "Parameter discovery"
            })

        # Group 2: Execution calls
        if execution_calls:
            # Check if calls have placeholders (need sequential for dependency resolution)
            has_placeholders = any(c.get("placeholder") for c in execution_calls)

            # Determine execution mode
            if not has_placeholders and len(execution_calls) > 1:
                # Multiple independent calls - PARALLELIZE!
                mode = "parallel"
                description = f"Parallel execution of {len(execution_calls)} independent calls"
                print(f"   ⚡ Detected {len(execution_calls)} independent calls - will execute in parallel")
            else:
                # Has dependencies or single call - sequential
                mode = "sequential"
                if has_placeholders:
                    description = "Sequential execution (parameter injection needed)"
                else:
                    description = "Sequential execution (single call)"

            groups.append({
                "step": len(groups) + 1,
                "mode": mode,
                "calls": execution_calls,
                "depends_on": len(groups) if groups else None,
                "description": description
            })

        return groups

    def _deduplicate_function_calls(self, function_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate function calls with the same function name and parameters.
        
        Args:
            function_calls: List of function call dictionaries
            
        Returns:
            De-duplicated list of function calls
        """
        seen = set()
        unique_calls = []
        duplicates_removed = 0
        
        for call in function_calls:
            function_name = call.get("function", "")
            parameters = call.get("parameters", {})
            
            # Filter out internal metadata parameters that start with _
            clean_params = {k: v for k, v in parameters.items() if not k.startswith('_')}
            
            # Create a hashable key from function name and parameters
            try:
                # Convert dict to sorted tuple of items for hashing
                param_items = tuple(sorted(clean_params.items()))
                key = (function_name, param_items)
            except TypeError:
                # If parameters contain unhashable types (lists, dicts), 
                # skip deduplication for this call to be safe
                unique_calls.append(call)
                continue
            
            if key not in seen:
                seen.add(key)
                unique_calls.append(call)
            else:
                duplicates_removed += 1
                print(f"   ⚠️  Skipped duplicate: {function_name}({clean_params})")
        
        if duplicates_removed > 0:
            print(f"   ✅ Removed {duplicates_removed} duplicate function call(s)")
        
        return unique_calls

    # ===================================================================
    # PARAMETER EXTRACTION
    # ===================================================================
    
    async def _extract_parameters_for_function(self, query: str, function_name: str,
                                               provided_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts parameters from query text."""
        params = dict(provided_params)

        # Parameter mapping for semantic equivalents
        param_mappings = {
            "get_user_repositories": {
                "owner": "username",  # Gemini might use "owner" but function expects "username"
                "user": "username"
            }
        }

        # Apply parameter mappings if applicable
        if function_name in param_mappings:
            mappings = param_mappings[function_name]
            for old_name, new_name in mappings.items():
                if old_name in params and new_name not in params:
                    params[new_name] = params.pop(old_name)

        fallback_params = self._extract_parameters_fallback(query, function_name)

        for key, value in fallback_params.items():
            if key not in params:
                params[key] = value

        # Filter out invalid parameters for repository discovery functions
        repository_functions = {
            "get_authenticated_user_repositories",
            "get_user_repositories",
            "get_organization_repositories"
        }

        if function_name in repository_functions:
            # These functions don't accept 'state' or 'pr_number' parameters
            params.pop("state", None)
            params.pop("pr_number", None)

        return params
    
    def _extract_parameters_fallback(self, query: str, function_name: str) -> Dict[str, Any]:
        """Regex-based parameter extraction (improved)."""
        query_lower = query.lower()
        params = {}

        # Extract days/hours first (so numbers aren't mistaken for PR)
        days_match = re.search(r'(\d+)\s+days?', query_lower)
        if days_match:
            params['n'] = int(days_match.group(1))

        hours_match = re.search(r'(\d+)\s+hours?', query_lower)
        if hours_match:
            params['hours'] = int(hours_match.group(1))

        # Extract owner/repo if present
        repo_match = re.search(r'([A-Za-z0-9_.-]+)/([A-ZaZ0-9_.-]+)', query)
        if repo_match:
            params['owner'] = repo_match.group(1)
            params['repo'] = repo_match.group(2)

        # Strict PR number extraction: only when query explicitly references PR or function_name is get_pr_details
        pr_explicit = bool(re.search(r'\bpr\b|\bpull request\b|#\d+', query_lower))
        if pr_explicit and (function_name == 'get_pr_details' or re.search(r'\bpr\b|\bpull request\b', query_lower)):
            pr_match = re.search(r'#(\d+)|\bpr\s*#?(\d+)\b', query_lower)
            if pr_match:
                pr_num = pr_match.group(1) or pr_match.group(2)
                if pr_num:
                    params['pr_number'] = int(pr_num)

        # Extract state
        if 'open' in query_lower:
            params['state'] = 'open'
        elif 'closed' in query_lower:
            params['state'] = 'closed'

        # Extract username for get_user_repositories
        # Patterns: "user yt-dlp", "from yt-dlp", "by yt-dlp", "for yt-dlp"
        if function_name == 'get_user_repositories':
            username_patterns = [
                r'user\s+([A-Za-z0-9_-]+)',
                r'from\s+(?:the\s+)?user\s+([A-Za-z0-9_-]+)',
                r'by\s+([A-Za-z0-9_-]+)',
                r'for\s+(?:user\s+)?([A-Za-z0-9_-]+)',
                r'owned\s+by\s+([A-Za-z0-9_-]+)',
                r'from\s+([A-Za-z0-9_-]+)(?:\'s|\s+repos|\s+repositories)',
            ]

            for pattern in username_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    # Avoid matching common words
                    if username.lower() not in ['the', 'my', 'our', 'your', 'their', 'all', 'any']:
                        params['username'] = username
                        break

        return params
    
    def _extract_function_calls(self, response) -> List[Dict[str, Any]]:
        """Extracts function calls from Gemini response."""
        function_calls = []
        
        try:
            if response.candidates and len(response.candidates) > 0:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append({
                            "name": part.function_call.name,
                            "args": dict(part.function_call.args) if hasattr(part.function_call, 'args') else {}
                        })
        except Exception as e:
            print(f"⚠️  Error extracting function calls: {str(e)}")
        
        return function_calls
    
    # ===================================================================
    # LEGACY & UTILITY METHODS (KEEP ONLY ONE COPY)
    # ===================================================================
    
    def _process_query_github_fallback(self, query: str) -> Dict[str, Any]:
        """Simple keyword-based GitHub function selector."""
        query_lower = query.lower()
        
        if "merged" in query_lower and "days" in query_lower:
            days = 7
            match = re.search(r'last (\d+) days', query_lower)
            if match:
                days = int(match.group(1))
            return {"function": "get_merged_prs_last_n_days", "parameters": {"n": days}}
        elif "pr" in query_lower and "#" in query_lower:
            pr_number = None
            match = re.search(r'pr\s*#?(\d+)', query_lower)
            if match:
                pr_number = int(match.group(1))
            return {"function": "get_pr_details", "parameters": {"pr_number": pr_number}}
        else:
            return {"function": "get_prs", "parameters": {}}
