"""
Interactive Live Query Testing for Sprintobot
Run: python -X utf8 interactive_test.py
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
        print(f"✓ Environment loaded\n")

load_env_file()

from app.services.github_service import GitHubService

async def run_interactive_session():
    """Interactive query session with live APIs"""

    print("="*80)
    print("🤖 Sprintobot - Interactive Live Query Testing")
    print("="*80)
    print("\nInitializing services...")

    try:
        service = GitHubService()
        print("✅ GitHub Service initialized")
        print("✅ AI Service ready")
    except Exception as e:
        print(f"❌ Initialization failed: {str(e)}")
        return

    print("\n" + "="*80)
    print("📝 INSTRUCTIONS")
    print("="*80)
    print("• Enter your natural language query about GitHub")
    print("• Type 'examples' to see sample queries")
    print("• Type 'quit' or 'exit' to stop")
    print("• Press Ctrl+C to interrupt")
    print("="*80)

    query_count = 0

    while True:
        try:
            print("\n" + "-"*80)
            query = input("\n🔍 Your query: ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            if query.lower() == 'examples':
                show_examples()
                continue

            query_count += 1
            print(f"\n{'='*80}")
            print(f"Query #{query_count}: {query}")
            print(f"{'='*80}")

            # Execute the query
            result = await service.process_natural_query(query)

            # Display results
            print("\n" + "="*80)
            print("📊 RESULTS")
            print("="*80)

            # Show execution details
            print(f"\n🔧 Execution Details:")
            print(f"   Method: {result.get('method', 'unknown')}")
            print(f"   Iterations: {result.get('iterations', 0)}")
            print(f"   Efficiency: {result.get('efficiency', 'unknown')}")
            print(f"   Success: {result.get('success', False)}")

            # Show function calls
            execution_plan = result.get('execution_plan', {})
            function_calls = execution_plan.get('function_calls', [])

            if function_calls:
                print(f"\n📋 Function Calls:")
                for idx, call in enumerate(function_calls, 1):
                    func_name = call.get('function')
                    params = call.get('parameters', {})
                    # Filter out metadata
                    clean_params = {k: v for k, v in params.items() if not k.startswith('_')}
                    print(f"   {idx}. {func_name}({clean_params})")

            # Show results
            results_data = result.get('results', [])
            print(f"\n📈 Data Retrieved:")

            if not results_data:
                print("   No data returned")
            else:
                for idx, res in enumerate(results_data, 1):
                    if isinstance(res, list):
                        print(f"   Result {idx}: {len(res)} items")
                        if len(res) > 0 and len(res) <= 5:
                            # Show first few items
                            for i, item in enumerate(res[:3], 1):
                                if isinstance(item, dict):
                                    name = item.get('name') or item.get('title') or item.get('number') or 'Item'
                                    print(f"      - {name}")
                            if len(res) > 3:
                                print(f"      ... and {len(res) - 3} more")
                    elif isinstance(res, dict):
                        if 'error' in res:
                            print(f"   Result {idx}: Error - {res.get('error')}")
                        else:
                            print(f"   Result {idx}: {res}")
                    else:
                        print(f"   Result {idx}: {res}")

            # Show any assumptions or warnings
            if result.get('assumptions'):
                print(f"\n💭 Assumptions:")
                for assumption in result.get('assumptions', []):
                    print(f"   • {assumption}")

            print("\n" + "="*80)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted. Type 'quit' to exit or continue with another query.")
            continue

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            print("\nFull traceback:")
            traceback.print_exc()
            continue

def show_examples():
    """Show example queries"""
    print("\n" + "="*80)
    print("💡 EXAMPLE QUERIES")
    print("="*80)

    examples = {
        "Simple Queries": [
            "Show me my repositories",
            "List my repos",
            "What repos do I have access to?"
        ],
        "PR Queries (with discovery)": [
            "Show me PRs merged in the last 7 days",
            "Get all open PRs",
            "Show PRs waiting for review",
            "List closed PRs"
        ],
        "Time-based Queries": [
            "PRs merged in last 14 days",
            "PRs waiting for review for 48 hours",
            "Recent pull requests"
        ],
        "Specific Repository": [
            "Get PRs from owner/repo",
            "Show merged PRs from microsoft/vscode in last 5 days",
            "List open PRs in owner/repo"
        ],
        "Repository Details": [
            "Get details of repository owner/repo",
            "Show info about owner/repo",
            "Describe repository owner/repo"
        ]
    }

    for category, queries in examples.items():
        print(f"\n📂 {category}:")
        for query in queries:
            print(f"   • {query}")

    print("\n" + "="*80)

def main():
    """Main entry point"""
    try:
        asyncio.run(run_interactive_session())
    except KeyboardInterrupt:
        print("\n\n👋 Session ended by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
