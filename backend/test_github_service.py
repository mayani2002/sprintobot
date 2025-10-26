"""
Quick test script for GitHub service
Run: python test_github_service.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Manual environment variable loading
def load_env_file():
    """Manually load environment variables from config/.env"""
    env_path = Path(__file__).parent.parent / "config" / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value
        print(f"✓ Loaded environment from {env_path}")
    else:
        print(f"⚠️  Environment file not found at {env_path}")

# Load environment variables
load_env_file()

async def test_github_service():
    """Test the GitHub service with a sample query"""
    try:
        from app.services.github_service import GitHubService
        
        print("\n🧪 Testing GitHub Service...")
        
        # Validate tokens
        github_token = os.getenv('GITHUB_TOKEN')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        print(f"✓ GITHUB_TOKEN configured: {bool(github_token)}")
        if github_token:
            print(f"  → Token length: {len(github_token)} chars")
            print(f"  → Token prefix: {github_token[:10]}...")
            if github_token.startswith(("'", '"')):
                print(f"  ⚠️  WARNING: Token has quotes - remove them!")
        
        print(f"✓ GEMINI_API_KEY configured: {bool(gemini_key)}")
        
        service = GitHubService()
        print("✓ GitHub Service initialized")
        
        # Test query
        query = "Show me PRs merged in the last 70 days"
        print(f"\n📝 Testing query: '{query}'")
        
        result = await service.process_natural_query(query)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            if "401" in str(result.get('error', '')):
                print("\n🔧 Fix: Your GitHub token is invalid or expired")
                print("   1. Go to https://github.com/settings/tokens")
                print("   2. Generate new token with 'repo' scope")
                print("   3. Update config/.env (remove quotes!)")
            if "available_functions" in result:
                print(f"\n📋 Available functions:")
                for func in result["available_functions"][:10]:
                    print(f"   - {func}")
        else:
            print(f"✅ Success!")
            print(f"   Function called: {result.get('function_called')}")
            print(f"   Parameters: {result.get('parameters')}")
            print(f"   Method: {result.get('method')}")
            print(f"   Results count: {len(result.get('result', []))}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("SprintoBot GitHub Service Test")
    print("=" * 60)
    result = asyncio.run(test_github_service())
    print("\n" + "=" * 60)
    if result and "error" not in result:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed - check errors above")
    print("=" * 60)
