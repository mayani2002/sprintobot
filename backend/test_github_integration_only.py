"""
Direct GitHub Integration Test (No AI/Gemini calls)
Tests GitHub API connectivity and authentication
Run: python test_github_integration_only.py
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
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value
        print(f"✓ Loaded environment from {env_path}")
    else:
        print(f"⚠️  Environment file not found at {env_path}")

load_env_file()

async def test_github_auth():
    """Test GitHub authentication"""
    from app.integrations.github_integration import GitHubIntegration
    
    github_token = os.getenv('GITHUB_TOKEN')
    print(f"\n🔑 GitHub Token Info:")
    print(f"   Length: {len(github_token)} chars")
    print(f"   Prefix: {github_token[:10]}...")
    
    integration = GitHubIntegration(token=github_token)
    
    # Test 1: Get authenticated user info
    print(f"\n📝 Test 1: Get Authenticated User")
    try:
        user = integration.github.get_user()
        print(f"   ✅ Authenticated as: {user.login}")
        print(f"   → Name: {user.name}")
        print(f"   → Public Repos: {user.public_repos}")
        print(f"   → URL: {user.html_url}")
        return user
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        return None

async def test_list_repositories():
    """Test listing user repositories"""
    from app.integrations.github_integration import GitHubIntegration
    
    github_token = os.getenv('GITHUB_TOKEN')
    integration = GitHubIntegration(token=github_token)
    
    print(f"\n📝 Test 2: List Your Repositories")
    try:
        result = await integration.get_authenticated_user_repositories(per_page=5)
        print(f"   ✅ Found {len(result)} repositories")
        for repo in result:
            print(f"   → {repo['full_name']} ({'private' if repo['private'] else 'public'})")
        return result
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        return []

async def test_get_prs_from_repo(owner: str, repo: str):
    """Test getting PRs from a specific repository"""
    from app.integrations.github_integration import GitHubIntegration
    
    github_token = os.getenv('GITHUB_TOKEN')
    integration = GitHubIntegration(token=github_token)
    
    print(f"\n📝 Test 3: Get PRs from {owner}/{repo}")
    try:
        # Test get_prs (list all PRs)
        result = await integration.get_prs(state='all', repo=repo, owner=owner)
        print(f"   ✅ Found {len(result)} PRs")
        for pr in result[:5]:
            print(f"   → PR #{pr['number']}: {pr['title']} ({pr['state']})")
        return result
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        return []

async def test_merged_prs(owner: str, repo: str, days: int = 30):
    """Test getting merged PRs from a specific repository"""
    from app.integrations.github_integration import GitHubIntegration
    
    github_token = os.getenv('GITHUB_TOKEN')
    integration = GitHubIntegration(token=github_token)
    
    print(f"\n📝 Test 4: Get PRs merged in last {days} days from {owner}/{repo}")
    try:
        result = await integration.get_merged_prs_last_n_days(n=days, repo=repo, owner=owner)
        print(f"   ✅ Found {len(result)} merged PRs")
        for pr in result[:5]:
            print(f"   → PR #{pr['number']}: {pr['title']}")
            print(f"      Merged: {pr['merged_at']}")
            print(f"      Approvers: {', '.join(pr['approvers']) if pr['approvers'] else 'None'}")
        return result
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        return []

async def test_repository_info(owner: str, repo: str):
    """Test getting repository details"""
    from app.integrations.github_integration import GitHubIntegration
    
    github_token = os.getenv('GITHUB_TOKEN')
    integration = GitHubIntegration(token=github_token)
    
    print(f"\n📝 Test 5: Get Repository Info for {owner}/{repo}")
    try:
        result = await integration.get_repository(owner=owner, repo=repo)
        print(f"   ✅ Repository found")
        print(f"   → Name: {result.get('name')}")
        print(f"   → Description: {result.get('description')}")
        print(f"   → Language: {result.get('language')}")
        print(f"   → Stars: {result.get('stargazers_count')}")
        print(f"   → Forks: {result.get('forks_count')}")
        print(f"   → Open Issues: {result.get('open_issues_count')}")
        return result
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        return {}

async def run_all_tests():
    """Run all GitHub integration tests"""
    print("=" * 70)
    print("GitHub Integration Test Suite (No AI calls)")
    print("=" * 70)
    
    # Test 1: Authentication
    user = await test_github_auth()
    if not user:
        print("\n❌ Authentication failed. Check your GITHUB_TOKEN")
        return False
    
    # Test 2: List repositories
    repos = await test_list_repositories()
    if not repos:
        print("\n⚠️  No repositories found or access denied")
        return False
    
    # Use the first repository for further tests
    first_repo = repos[0]
    owner, repo_name = first_repo['full_name'].split('/')
    
    print(f"\n🎯 Using repository: {owner}/{repo_name} for detailed tests")
    
    # Test 3: List PRs
    await test_get_prs_from_repo(owner, repo_name)
    
    # Test 4: Merged PRs
    await test_merged_prs(owner, repo_name, days=90)
    
    # Test 5: Repository details
    await test_repository_info(owner, repo_name)
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    
    print("\n" + "=" * 70)
    if success:
        print("✅ All GitHub integration tests passed!")
        print("\n💡 Your GitHub token is working correctly")
        print("💡 You can now use the full service with AI queries")
    else:
        print("❌ Some tests failed")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your GITHUB_TOKEN in config/.env")
        print("   2. Ensure token has 'repo' and 'read:org' permissions")
        print("   3. Verify you have access to at least one repository")
    print("=" * 70)
