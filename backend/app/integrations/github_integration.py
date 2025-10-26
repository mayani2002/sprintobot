from typing import List, Dict, Any
import requests
from github import Github
from datetime import datetime, timedelta, timezone

class GitHubIntegration:
    def __init__(self, token: str):
        self.token = token
        self.github = Github(token)
    
    # PR Methods
    async def get_merged_prs_last_n_days(self, n: int = 7, repo: str = None, owner: str = None) -> List[Dict[str, Any]]:
        """Get pull requests merged in the last N days."""
        try:
            # If no repo/owner specified, try to get from authenticated user's first repo
            if not owner or not repo:
                print("⚠️  No repo/owner specified, using authenticated user's first repository")
                user = self.github.get_user()
                repos = list(user.get_repos())
                if not repos:
                    print("❌ No repositories found for authenticated user")
                    return []
                repository = repos[0]
                print(f"ℹ️  Using repository: {repository.full_name}")
            else:
                repository = self.github.get_repo(f"{owner}/{repo}")
            
            since = datetime.now(timezone.utc) - timedelta(days=n)
            pulls = repository.get_pulls(state='closed', sort='updated', direction='desc')
            
            merged_prs = []
            for pr in pulls:
                if pr.merged_at and pr.merged_at >= since:
                    reviews = pr.get_reviews()
                    approvers = set(r.user.login for r in reviews if r.state == 'APPROVED')
                    
                    merged_prs.append({
                        'number': pr.number,
                        'title': pr.title,
                        'merged_at': pr.merged_at.isoformat(),
                        'author': pr.user.login,
                        'approvers': list(approvers),
                        'url': pr.html_url
                    })
            
            return merged_prs
        except Exception as e:
            print(f"Error fetching merged PRs: {str(e)}")
            return []
    
    async def get_prs_waiting_for_review(self, hours: int = 24, repo: str = None, owner: str = None) -> List[Dict[str, Any]]:
        """Get PRs waiting for review for more than specified hours."""
        try:
            if not owner or not repo:
                user = self.github.get_user()
                repos = list(user.get_repos())
                if not repos:
                    return []
                repository = repos[0]
            else:
                repository = self.github.get_repo(f"{owner}/{repo}")
            
            threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
            pulls = repository.get_pulls(state='open', sort='created')
            
            waiting_prs = []
            for pr in pulls:
                if pr.created_at <= threshold:
                    reviews = list(pr.get_reviews())
                    if not reviews:
                        waiting_prs.append({
                            'number': pr.number,
                            'title': pr.title,
                            'created_at': pr.created_at.isoformat(),
                            'author': pr.user.login,
                            'url': pr.html_url
                        })
            
            return waiting_prs
        except Exception as e:
            print(f"Error fetching waiting PRs: {str(e)}")
            return []
    
    async def get_pr_details(self, pr_number: int, repo: str = None, owner: str = None) -> Dict[str, Any]:
        """Get details of a specific PR."""
        try:
            if not owner or not repo:
                user = self.github.get_user()
                repos = list(user.get_repos())
                if not repos:
                    return {"error": "No repository specified"}
                repository = repos[0]
            else:
                repository = self.github.get_repo(f"{owner}/{repo}")
            
            pr = repository.get_pull(pr_number)
            
            return {
                'number': pr.number,
                'title': pr.title,
                'state': pr.state,
                'author': pr.user.login,
                'created_at': pr.created_at.isoformat(),
                'updated_at': pr.updated_at.isoformat(),
                'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                'merged_by': pr.merged_by.login if pr.merged_by else None,
                'body': pr.body,
                'url': pr.html_url,
                'commits': pr.commits,
                'additions': pr.additions,
                'deletions': pr.deletions,
                'changed_files': pr.changed_files
            }
        except Exception as e:
            print(f"Error fetching PR details: {str(e)}")
            return {"error": str(e)}
    
    async def get_pr_reviews(self, pr_number: int, repo: str = None, owner: str = None) -> List[Dict[str, Any]]:
        """Get reviews for a specific PR."""
        try:
            if not owner or not repo:
                user = self.github.get_user()
                repos = list(user.get_repos())
                if not repos:
                    return []
                repository = repos[0]
            else:
                repository = self.github.get_repo(f"{owner}/{repo}")
            
            pr = repository.get_pull(pr_number)
            reviews = pr.get_reviews()
            
            result = []
            for review in reviews:
                result.append({
                    'id': review.id,
                    'user': review.user.login,
                    'state': review.state,
                    'body': review.body,
                    'submitted_at': review.submitted_at.isoformat() if review.submitted_at else None
                })
            
            return result
        except Exception as e:
            print(f"Error fetching PR reviews: {str(e)}")
            return []
    
    async def get_prs(self, state: str = 'open', repo: str = None, owner: str = None) -> List[Dict[str, Any]]:
        """Get list of PRs filtered by state."""
        try:
            if not owner or not repo:
                user = self.github.get_user()
                repos = list(user.get_repos())
                if not repos:
                    return []
                repository = repos[0]
            else:
                repository = self.github.get_repo(f"{owner}/{repo}")
            
            pulls = repository.get_pulls(state=state, sort='updated', direction='desc')
            
            result = []
            for pr in pulls[:30]:  # Limit to 30
                result.append({
                    'number': pr.number,
                    'title': pr.title,
                    'state': pr.state,
                    'author': pr.user.login,
                    'created_at': pr.created_at.isoformat(),
                    'updated_at': pr.updated_at.isoformat(),
                    'url': pr.html_url
                })
            
            return result
        except Exception as e:
            print(f"Error fetching PRs: {str(e)}")
            return []
    
    # Repository Methods
    async def get_user_repositories(self, username: str, type: str = "owner", sort: str = "updated", per_page: int = 30) -> List[Dict[str, Any]]:
        """Get list of repositories for a specific user."""
        try:
            user = self.github.get_user(username)
            repos = user.get_repos(type=type, sort=sort)
            
            result = []
            count = 0
            for repo in repos:
                if count >= per_page:
                    break
                result.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "url": repo.html_url,
                    "language": repo.language,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count
                })
                count += 1
            return result
        except Exception as e:
            print(f"Error fetching user repositories: {str(e)}")
            return []
    
    async def get_authenticated_user_repositories(self, visibility: str = "all", sort: str = "updated", per_page: int = 30) -> List[Dict[str, Any]]:
        """Get list of repositories for the authenticated user."""
        try:
            user = self.github.get_user()
            repos = user.get_repos(visibility=visibility, sort=sort)
            
            result = []
            count = 0
            for repo in repos:
                if count >= per_page:
                    break
                result.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "private": repo.private,
                    "url": repo.html_url
                })
                count += 1
            return result
        except Exception as e:
            print(f"Error: {str(e)}")
            return []
    
    async def get_organization_repositories(self, org: str, type: str = "all", sort: str = "updated", per_page: int = 30) -> List[Dict[str, Any]]:
        """List repositories for an organization."""
        try:
            organization = self.github.get_organization(org)
            repos = organization.get_repos(type=type, sort=sort)
            
            result = []
            count = 0
            for repo in repos:
                if count >= per_page:
                    break
                result.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "url": repo.html_url
                })
                count += 1
            return result
        except Exception as e:
            print(f"Error: {str(e)}")
            return []
    
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get detailed information about a specific repository."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            return {
                "name": repository.name,
                "full_name": repository.full_name,
                "description": repository.description,
                "private": repository.private,
                "url": repository.html_url,
                "language": repository.language,
                "stargazers_count": repository.stargazers_count,
                "forks_count": repository.forks_count,
                "open_issues_count": repository.open_issues_count
            }
        except Exception as e:
            print(f"Error: {str(e)}")
            return {"error": str(e)}
    
    # Security & Compliance Methods
    async def check_vulnerability_alerts_enabled(self, owner: str, repo: str) -> Dict[str, Any]:
        """Check if vulnerability alerts are enabled."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/vulnerability-alerts"
            headers = {"Authorization": f"token {self.token}"}
            response = requests.get(url, headers=headers)
            return {
                "repository": f"{owner}/{repo}",
                "enabled": response.status_code == 204
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_repository_topics(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository topics."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            return {
                "repository": f"{owner}/{repo}",
                "topics": repository.get_topics()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_repository_languages(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository languages."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            languages = repository.get_languages()
            total = sum(languages.values())
            return {
                "repository": f"{owner}/{repo}",
                "languages": {lang: {"bytes": bytes_count, "percentage": round((bytes_count/total)*100, 2)} 
                             for lang, bytes_count in languages.items()}
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_repository_contributors(self, owner: str, repo: str, per_page: int = 30) -> List[Dict[str, Any]]:
        """List repository contributors."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            contributors = repository.get_contributors()
            result = []
            count = 0
            for contributor in contributors:
                if count >= per_page:
                    break
                result.append({
                    "login": contributor.login,
                    "contributions": contributor.contributions
                })
                count += 1
            return result
        except Exception as e:
            print(f"Error: {str(e)}")
            return []
    
    async def check_private_vulnerability_reporting(self, owner: str, repo: str) -> Dict[str, Any]:
        """Check if private vulnerability reporting is enabled."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/private-vulnerability-reporting"
            headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github+json"}
            response = requests.get(url, headers=headers)
            
            return {
                "repository": f"{owner}/{repo}",
                "private_vulnerability_reporting_enabled": response.status_code == 204,
                "status_code": response.status_code
            }
        except Exception as e:
            print(f"Error checking private vulnerability reporting: {str(e)}")
            return {"error": str(e)}