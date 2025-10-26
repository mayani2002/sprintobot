"""
GitHub API Function Declarations for Gemini Function Calling (Latest API)
"""

# Repository List Functions
get_user_repositories = {
    "name": "get_user_repositories",
    "description": "Get list of public repositories for a specific GitHub user. Useful for auditing what repositories a user owns or contributes to.",
    "parameters": {
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "description": "The GitHub username to fetch repositories for"
            },
            "type": {
                "type": "string",
                "description": "Type of repositories to list (all, owner, or member)",
                "enum": ["all", "owner", "member"]
            },
            "sort": {
                "type": "string",
                "description": "Sort order for repositories",
                "enum": ["created", "updated", "pushed", "full_name"]
            },
            "per_page": {
                "type": "integer",
                "description": "Number of results per page (max 100)"
            }
        },
        "required": ["username"]
    }
}

get_authenticated_user_repositories = {
    "name": "get_authenticated_user_repositories",
    "description": "Get repositories for the authenticated user including private repos. Shows repos the user owns, collaborates on, or is a member of through an organization.",
    "parameters": {
        "type": "object",
        "properties": {
            "visibility": {
                "type": "string",
                "description": "Filter by visibility (all, public, or private)",
                "enum": ["all", "public", "private"]
            },
            "affiliation": {
                "type": "string",
                "description": "Comma-separated list of affiliation types"
            },
            "sort": {
                "type": "string",
                "description": "Sort order",
                "enum": ["created", "updated", "pushed", "full_name"]
            },
            "per_page": {
                "type": "integer",
                "description": "Results per page"
            }
        }
    }
}

get_organization_repositories = {
    "name": "get_organization_repositories",
    "description": "List all repositories for an organization. Essential for org-wide audits and compliance checks.",
    "parameters": {
        "type": "object",
        "properties": {
            "org": {
                "type": "string",
                "description": "The organization name"
            },
            "type": {
                "type": "string",
                "description": "Type of repositories",
                "enum": ["all", "public", "private", "forks", "sources", "member"]
            },
            "sort": {
                "type": "string",
                "description": "Sort order",
                "enum": ["created", "updated", "pushed", "full_name"]
            },
            "per_page": {
                "type": "integer",
                "description": "Results per page"
            }
        },
        "required": ["org"]
    }
}

get_repository = {
    "name": "get_repository",
    "description": "Get comprehensive details about a specific repository including metadata, permissions, security settings, and statistics. Use this for detailed repository audits.",
    "parameters": {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Repository owner (username or organization)"
            },
            "repo": {
                "type": "string",
                "description": "Repository name"
            }
        },
        "required": ["owner", "repo"]
    }
}

# Security & Compliance Functions
check_vulnerability_alerts_enabled = {
    "name": "check_vulnerability_alerts_enabled",
    "description": "Check if Dependabot vulnerability alerts are enabled for a repository. Critical for security compliance audits.",
    "parameters": {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Repository owner"
            },
            "repo": {
                "type": "string",
                "description": "Repository name"
            }
        },
        "required": ["owner", "repo"]
    }
}

check_private_vulnerability_reporting = {
    "name": "check_private_vulnerability_reporting",
    "description": "Check if private vulnerability reporting is enabled, allowing security researchers to privately report vulnerabilities.",
    "parameters": {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Repository owner"
            },
            "repo": {
                "type": "string",
                "description": "Repository name"
            }
        },
        "required": ["owner", "repo"]
    }
}

get_repository_topics = {
    "name": "get_repository_topics",
    "description": "Get all topics/tags associated with a repository. Useful for categorization and discovery.",
    "parameters": {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Repository owner"
            },
            "repo": {
                "type": "string",
                "description": "Repository name"
            }
        },
        "required": ["owner", "repo"]
    }
}

get_repository_languages = {
    "name": "get_repository_languages",
    "description": "Get programming languages used in a repository with byte counts and percentages. Essential for tech stack audits.",
    "parameters": {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Repository owner"
            },
            "repo": {
                "type": "string",
                "description": "Repository name"
            }
        },
        "required": ["owner", "repo"]
    }
}

get_repository_contributors = {
    "name": "get_repository_contributors",
    "description": "List all contributors to a repository with their contribution counts. Useful for identifying key maintainers.",
    "parameters": {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Repository owner"
            },
            "repo": {
                "type": "string",
                "description": "Repository name"
            },
            "per_page": {
                "type": "integer",
                "description": "Results per page"
            }
        },
        "required": ["owner", "repo"]
    }
}

# PR Functions
get_merged_prs_last_n_days = {
    "name": "get_merged_prs_last_n_days",
    "description": "Get pull requests that were merged in the last N days with their approvers.",
    "parameters": {
        "type": "object",
        "properties": {
            "n": {
                "type": "integer",
                "description": "Number of days to look back (1-365). Discoverable: No, Has Default: Yes (7)"
            },
            "repo": {
                "type": "string",
                "description": "Repository name. Discoverable: Yes (via get_authenticated_user_repositories)"
            },
            "owner": {
                "type": "string",
                "description": "Repository owner. Discoverable: Yes (via get_authenticated_user_repositories)"
            }
        },
        "required": ["n"]  # Only n is truly required, others can be discovered
    }
}

get_prs_waiting_for_review = {
    "name": "get_prs_waiting_for_review",
    "description": "Get pull requests waiting for review for more than specified hours. Helps identify PRs that need attention.",
    "parameters": {
        "type": "object",
        "properties": {
            "hours": {
                "type": "integer",
                "description": "Number of hours the PR has been waiting for review"
            },
            "repo": {
                "type": "string",
                "description": "Repository name (optional)"
            }
        },
        "required": ["hours"]
    }
}

get_pr_details = {
    "name": "get_pr_details",
    "description": "Get detailed information about a specific pull request by number.",
    "parameters": {
        "type": "object",
        "properties": {
            "pr_number": {
                "type": "integer",
                "description": "The pull request number. Discoverable: No, Requires User Input: Yes"
            },
            "repo": {
                "type": "string",
                "description": "Repository name. Discoverable: Yes (via get_authenticated_user_repositories)"
            },
            "owner": {
                "type": "string",
                "description": "Repository owner. Discoverable: Yes (via get_authenticated_user_repositories)"
            }
        },
        "required": ["pr_number"]
    }
}

get_pr_reviews = {
    "name": "get_pr_reviews",
    "description": "Get all reviews and review comments for a specific pull request. Shows who reviewed, approval status, and feedback provided.",
    "parameters": {
        "type": "object",
        "properties": {
            "pr_number": {
                "type": "integer",
                "description": "The pull request number to get reviews for"
            },
            "repo": {
                "type": "string",
                "description": "Repository name (optional)"
            }
        },
        "required": ["pr_number"]
    }
}

get_prs = {
    "name": "get_prs",
    "description": "Get a list of all pull requests, optionally filtered by state. Use this for general queries about PRs or when no specific PR number is mentioned.",
    "parameters": {
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "description": "Filter PRs by their state",
                "enum": ["open", "closed", "all"]
            },
            "repo": {
                "type": "string",
                "description": "Repository name (optional)"
            }
        }
    }
}

# Export all function declarations as a list
ALL_GITHUB_FUNCTIONS = [
    # Repository Lists
    get_user_repositories,
    get_authenticated_user_repositories,
    get_organization_repositories,
    
    # Repository Details
    get_repository,
    
    # Security & Compliance
    check_vulnerability_alerts_enabled,
    check_private_vulnerability_reporting,
    
    # Metadata
    get_repository_topics,
    get_repository_languages,
    
    # Contributors
    get_repository_contributors,
    
    # Pull Requests
    get_merged_prs_last_n_days,
    get_prs_waiting_for_review,
    get_pr_details,
    get_pr_reviews,
    get_prs
]
