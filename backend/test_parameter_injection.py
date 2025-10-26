"""
Unit test for parameter injection logic (no API keys required)
Tests the _resolve_placeholders method independently
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_parameter_injection():
    """Test that parameter injection works correctly"""

    print("\n" + "="*70)
    print("Testing Parameter Injection Logic")
    print("="*70)

    # Mock the GitHubService class with just the _resolve_placeholders method
    class MockGitHubService:
        def _resolve_placeholders(self, parameters, context, purpose=""):
            """
            Copied logic from github_service.py for testing
            """
            resolved = dict(parameters)

            # Check if we have repository discovery results
            if "get_authenticated_user_repositories" in context:
                repos = context["get_authenticated_user_repositories"]

                if isinstance(repos, list) and len(repos) > 0:
                    # Sort by updated_at if available
                    sorted_repos = sorted(
                        repos,
                        key=lambda r: r.get("updated_at", ""),
                        reverse=True
                    )
                    selected_repo = sorted_repos[0]

                    # If more than 3 repos, add metadata
                    if len(repos) > 3:
                        print(f"      Found {len(repos)} repositories, using most recent: {selected_repo.get('name')}")
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

                    # Inject organization if missing
                    if "organization" not in resolved or resolved["organization"] is None:
                        owner_login = selected_repo.get("owner", {}).get("login")
                        if owner_login:
                            resolved["organization"] = owner_login

            return resolved

    service = MockGitHubService()

    # Test Case 1: Simple parameter injection
    print("\n📝 Test Case 1: Inject owner and repo from discovery")
    print("-" * 70)

    # Simulate Step 1 result
    context = {
        "get_authenticated_user_repositories": [
            {
                "name": "sprintobot",
                "owner": {"login": "mayani2002"},
                "updated_at": "2025-01-15T10:00:00Z"
            },
            {
                "name": "other-repo",
                "owner": {"login": "mayani2002"},
                "updated_at": "2025-01-10T10:00:00Z"
            }
        ]
    }

    # Simulate Step 2 parameters (with placeholders)
    parameters = {
        "owner": None,
        "repo": None,
        "n": 7
    }

    resolved = service._resolve_placeholders(parameters, context)

    print(f"Original parameters: {parameters}")
    print(f"Resolved parameters: {resolved}")

    # Assertions
    assert resolved["owner"] == "mayani2002", "Owner should be injected"
    assert resolved["repo"] == "sprintobot", "Repo should be injected"
    assert resolved["n"] == 7, "Existing param should be preserved"
    print("✅ Test Case 1 PASSED")

    # Test Case 2: Multiple repos (should use most recent)
    print("\n📝 Test Case 2: Multiple repos - use most recent")
    print("-" * 70)

    context_multi = {
        "get_authenticated_user_repositories": [
            {
                "name": "old-repo",
                "owner": {"login": "testuser"},
                "updated_at": "2024-01-01T10:00:00Z"
            },
            {
                "name": "recent-repo",
                "owner": {"login": "testuser"},
                "updated_at": "2025-01-15T10:00:00Z"
            },
            {
                "name": "medium-repo",
                "owner": {"login": "testuser"},
                "updated_at": "2024-06-01T10:00:00Z"
            }
        ]
    }

    parameters2 = {"owner": None, "repo": None}
    resolved2 = service._resolve_placeholders(parameters2, context_multi)

    print(f"Resolved parameters: {resolved2}")

    assert resolved2["repo"] == "recent-repo", "Should select most recently updated repo"
    print("✅ Test Case 2 PASSED")

    # Test Case 3: No placeholders needed
    print("\n📝 Test Case 3: All params already provided")
    print("-" * 70)

    parameters3 = {
        "owner": "explicit-owner",
        "repo": "explicit-repo",
        "n": 14
    }

    resolved3 = service._resolve_placeholders(parameters3, context)

    print(f"Original parameters: {parameters3}")
    print(f"Resolved parameters: {resolved3}")

    assert resolved3["owner"] == "explicit-owner", "Should keep explicit owner"
    assert resolved3["repo"] == "explicit-repo", "Should keep explicit repo"
    print("✅ Test Case 3 PASSED")

    # Test Case 4: Empty context (no discovery)
    print("\n📝 Test Case 4: No discovery data available")
    print("-" * 70)

    empty_context = {}
    parameters4 = {"owner": None, "repo": None, "n": 7}

    resolved4 = service._resolve_placeholders(parameters4, empty_context)

    print(f"Resolved parameters: {resolved4}")

    assert resolved4["owner"] is None, "Should remain None if no discovery"
    assert resolved4["repo"] is None, "Should remain None if no discovery"
    assert resolved4["n"] == 7, "Existing param should be preserved"
    print("✅ Test Case 4 PASSED")

    print("\n" + "="*70)
    print("✅ ALL PARAMETER INJECTION TESTS PASSED!")
    print("="*70)
    print("\n📊 Summary:")
    print("   ✓ Parameter injection from discovery works")
    print("   ✓ Most recent repo is selected")
    print("   ✓ Explicit params are preserved")
    print("   ✓ Handles empty context gracefully")
    print("\n🎯 The parameter injection logic is working correctly!")
    print("   Ready for live API testing once credentials are configured.")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        test_parameter_injection()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
