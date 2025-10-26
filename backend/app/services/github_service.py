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
            
            if "error" in execution_plan and not execution_plan.get("function_calls"):
                return execution_plan
            
            # Execute all planned function calls
            final_results = []
            
            print(f"\n📋 Executing {len(execution_plan.get('function_calls', []))} function call(s)")
            
            for idx, call_info in enumerate(execution_plan.get("function_calls", []), 1):
                function_name = call_info.get("function")
                parameters = call_info.get("parameters", {})
                
                if not function_name:
                    print(f"⚠️  Step {idx}: No function specified, skipping")
                    continue
                
                print(f"\n{'─'*60}")
                print(f"🔧 Executing [{idx}/{len(execution_plan['function_calls'])}]: {function_name}")
                print(f"   Parameters: {parameters}")
                
                # Execute the function
                if hasattr(self.integration, function_name):
                    try:
                        method = getattr(self.integration, function_name)
                        result = await method(**parameters)
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
