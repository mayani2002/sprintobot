from typing import List, Dict, Any, Optional
import requests
import os
from datetime import datetime, timedelta, timezone

class GitHubIntegration:
    def __init__(self):
        self.mcp_url = os.getenv("GITHUB_MCP_URL", "http://localhost:3000")
        self.token = os.getenv("GITHUB_TOKEN")
        self.org = os.getenv("GITHUB_ORG", "mayani2002")  # <-- default to your GitHub username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.default_repo = "ecohabit"  # <-- set your actual repo name here
    
    def get_prs(self, repo=None, state='open', sort='created', direction='desc', per_page=100, page=1):
        if repo is None:
            repo = self.default_repo
        url = f"{self.base_url}/repos/{self.org}/{repo}/pulls"
        params = {
            'state': state,
            'sort': sort,
            'direction': direction,
            'per_page': per_page,
            'page': page
        }
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_pr_details(self, pr_number, repo=None):
        if repo is None:
            repo = self.default_repo
        url = f"{self.base_url}/repos/{self.org}/{repo}/pulls/{pr_number}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_pr_reviews(self, pr_number, repo=None):
        if repo is None:
            repo = self.default_repo
        url = f"{self.base_url}/repos/{self.org}/{repo}/pulls/{pr_number}/reviews"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_merged_prs_last_n_days(self, n=7, repo=None):
        if repo is None:
            repo = self.default_repo
        since = (datetime.utcnow() - timedelta(days=n)).isoformat() + "Z"
        merged_prs = []
        page = 1
        while True:
            prs = self.get_prs(repo=repo, state='closed', sort='updated', direction='desc', page=page)
            if not prs:
                break
            for pr in prs:
                merged_at = pr.get("merged_at")
                if merged_at and merged_at >= since:
                    reviews = self.get_pr_reviews(pr['number'], repo=repo)
                    approvers = set(r['user']['login'] for r in reviews if r['state'] == 'APPROVED')
                    merged_prs.append({
                        'number': pr['number'],
                        'title': pr['title'],
                        'merged_at': merged_at,
                        'approvers': list(approvers)
                    })
                elif merged_at and merged_at < since:
                    break
            else:
                page += 1
                continue
            break
        return merged_prs

    def get_prs_waiting_for_review(self, hours=24, repo=None):
        if repo is None:
            repo = self.default_repo
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        waiting_prs = []
        page = 1
        while True:
            prs = self.get_prs(repo=repo, state='open', sort='created', direction='asc', page=page)
            if not prs:
                break
            for pr in prs:
                created_at = datetime.fromisoformat(pr['created_at'].replace("Z", "+00:00"))
                if created_at <= threshold:
                    reviews = self.get_pr_reviews(pr['number'], repo=repo)
                    if not reviews:
                        waiting_prs.append({
                            'number': pr['number'],
                            'title': pr['title'],
                            'created_at': pr['created_at'],
                            'url': pr['html_url']
                        })
            page += 1
        print(f"Waiting PRs: {waiting_prs}")
        return waiting_prs