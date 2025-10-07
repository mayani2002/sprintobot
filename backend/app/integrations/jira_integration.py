from typing import List, Dict, Any, Optional
import requests
import os
from datetime import datetime
import base64

class JiraIntegration:
    def __init__(self):
        self.url = os.getenv("JIRA_URL")
        self.username = os.getenv("JIRA_USERNAME")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        
        if self.username and self.api_token:
            credentials = base64.b64encode(f"{self.username}:{self.api_token}".encode()).decode()
            self.headers = {
                "Authorization": f"Basic {credentials}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
    
    async def get_ticket(self, ticket_key: str) -> Dict[str, Any]:
        """Get details of a specific JIRA ticket."""
        if not all([self.url, self.username, self.api_token]):
            raise ValueError("JIRA credentials not configured")
        
        url = f"{self.url}/rest/api/3/issue/{ticket_key}"
        params = {
            "expand": "changelog,transitions,comments"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            ticket_data = response.json()
            
            return {
                "key": ticket_data["key"],
                "summary": ticket_data["fields"]["summary"],
                "description": ticket_data["fields"].get("description", ""),
                "status": ticket_data["fields"]["status"]["name"],
                "assignee": ticket_data["fields"]["assignee"]["displayName"] if ticket_data["fields"]["assignee"] else None,
                "reporter": ticket_data["fields"]["reporter"]["displayName"],
                "created": ticket_data["fields"]["created"],
                "updated": ticket_data["fields"]["updated"],
                "priority": ticket_data["fields"]["priority"]["name"] if ticket_data["fields"]["priority"] else "None",
                "workflow_history": self._extract_workflow_history(ticket_data.get("changelog", {})),
                "comments": self._extract_comments(ticket_data["fields"].get("comment", {})),
                "url": f"{self.url}/browse/{ticket_key}"
            }
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch JIRA ticket: {str(e)}")
    
    async def search_tickets(self, jql_query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for JIRA tickets using JQL."""
        if not all([self.url, self.username, self.api_token]):
            raise ValueError("JIRA credentials not configured")
        
        url = f"{self.url}/rest/api/3/search"
        payload = {
            "jql": jql_query,
            "maxResults": max_results,
            "fields": ["summary", "status", "assignee", "reporter", "created", "updated", "priority"]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for issue in data.get("issues", []):
                results.append({
                    "key": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "status": issue["fields"]["status"]["name"],
                    "assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else None,
                    "reporter": issue["fields"]["reporter"]["displayName"],
                    "created": issue["fields"]["created"],
                    "updated": issue["fields"]["updated"],
                    "priority": issue["fields"]["priority"]["name"] if issue["fields"]["priority"] else "None",
                    "url": f"{self.url}/browse/{issue['key']}"
                })
            
            return results
            
        except requests.RequestException as e:
            raise Exception(f"Failed to search JIRA tickets: {str(e)}")
    
    async def get_user_permissions(self, username: str, project_key: str = None) -> Dict[str, Any]:
        """Get user permissions for a project or globally."""
        if not all([self.url, self.username, self.api_token]):
            raise ValueError("JIRA credentials not configured")
        
        try:
            # Get user details
            user_url = f"{self.url}/rest/api/3/user"
            user_params = {"accountId": username}
            user_response = requests.get(user_url, headers=self.headers, params=user_params)
            
            if user_response.status_code != 200:
                # Try with username instead of accountId
                user_params = {"username": username}
                user_response = requests.get(user_url, headers=self.headers, params=user_params)
            
            user_data = user_response.json() if user_response.status_code == 200 else {}
            
            # Get user permissions
            permissions_url = f"{self.url}/rest/api/3/mypermissions"
            permissions_params = {}
            if project_key:
                permissions_params["projectKey"] = project_key
            
            permissions_response = requests.get(permissions_url, headers=self.headers, params=permissions_params)
            permissions_data = permissions_response.json() if permissions_response.status_code == 200 else {}
            
            return {
                "user": user_data,
                "permissions": permissions_data.get("permissions", {}),
                "project_key": project_key
            }
            
        except requests.RequestException as e:
            raise Exception(f"Failed to get user permissions: {str(e)}")
    
    def _extract_workflow_history(self, changelog: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract workflow transitions from changelog."""
        history = []
        
        for history_item in changelog.get("histories", []):
            for item in history_item.get("items", []):
                if item.get("field") == "status":
                    history.append({
                        "from_status": item.get("fromString"),
                        "to_status": item.get("toString"),
                        "changed_by": history_item["author"]["displayName"],
                        "changed_at": history_item["created"]
                    })
        
        return sorted(history, key=lambda x: x["changed_at"])
    
    def _extract_comments(self, comments_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract comments from ticket data."""
        comments = []
        
        for comment in comments_data.get("comments", []):
            comments.append({
                "id": comment["id"],
                "author": comment["author"]["displayName"],
                "body": comment["body"],
                "created": comment["created"],
                "updated": comment["updated"]
            })
        
        return sorted(comments, key=lambda x: x["created"])
