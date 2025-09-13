from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import openai
import os
import re

class AIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "sk-your-openai-api-key-here":
            self.client = openai.OpenAI(api_key=api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            print("Warning: OpenAI API key not configured. AI features will be disabled.")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query and extract intent and parameters."""
        if not self.enabled:
            # Return a basic analysis without AI
            return {
                "query_type": "mixed",
                "intent": f"Find evidence related to: {query}",
                "parameters": {},
                "confidence": 0.5,
                "clarifying_questions": []
            }
        
        try:
            system_prompt = """
            You are an AI assistant for an evidence-on-demand bot. Analyze the user's query and extract:
            1. Query type (github, jira, document, or mixed)
            2. Specific parameters or entities mentioned
            3. Intent (what evidence they're looking for)
            4. Suggested clarifying questions if the query is vague
            
            Return a JSON response with these fields:
            - query_type: string
            - intent: string
            - parameters: object
            - confidence: number (0-1)
            - clarifying_questions: array of strings (if needed)
            """
            
            # Try GPT-4 first, fallback to GPT-3.5-turbo
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    temperature=0.3
                )
            except Exception as gpt4_error:
                print(f"GPT-4 not available, trying GPT-3.5-turbo: {str(gpt4_error)}")
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    temperature=0.3
                )
            
            # Parse the response
            import json
            result = json.loads(response.choices[0].message.content)
            print(f"AI query processing result: {result}")
            return result
            
        except Exception as e:
            print(f"AI query processing failed, using fallback: {str(e)}")
            # Fallback to basic analysis when AI fails
            return self._process_query_fallback(query)
    
    async def process_query_github(self, natural_query: str) -> Dict[str, Any]:
        """
        Analyze the natural query and determine which GitHubIntegration function to call,
        along with the required parameters.
        """
        # Use AI if enabled, otherwise fallback
        if not self.enabled:
            result = self._process_query_fallback(natural_query)
        else:
            try:
                system_prompt = """
                You are an AI assistant for GitHub evidence queries.
                Analyze the user's query and determine which function to call:
                - get_merged_prs_last_n_days
                - get_prs_waiting_for_review
                - get_prs
                - get_pr_details
                - get_pr_reviews

                Extract the function name and parameters needed.
                Return a JSON object:
                {
                  "function": "<function_name>",
                  "parameters": { ... }
                }
                """
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": natural_query}
                    ],
                    temperature=0.2
                )
                import json
                result = json.loads(response.choices[0].message.content)
                print(f"AI GitHub function selection: {result}")
            except Exception as e:
                print(f"AI GitHub function selection failed, using fallback: {str(e)}")
                result = self._process_query_github_fallback(natural_query)

        # Ensure function and parameters are present
        function = result.get("function")
        parameters = result.get("parameters", {})
        return {
            "function": function,
            "parameters": parameters,
            "intent": f"GitHub query: {natural_query}"
        }

    async def format_evidence(self, evidence_items: List[Dict[str, Any]], query: str) -> str:
        """Format evidence items into a human-readable summary."""
        if not self.enabled:
            # Return a basic summary without AI
            summary = f"Evidence Summary for: {query}\n\n"
            for i, item in enumerate(evidence_items, 1):
                summary += f"{i}. {item.get('title', 'Untitled')}\n"
                summary += f"   Source: {item.get('source', 'Unknown')}\n"
                summary += f"   Description: {item.get('description', 'No description')}\n\n"
            return summary
        
        try:
            context = f"Query: {query}\n\nEvidence Found:\n"
            for item in evidence_items:
                context += f"- {item.get('title', 'Untitled')}: {item.get('description', 'No description')}\n"
            
            system_prompt = """
            You are formatting evidence for an auditor. Create a clear, professional summary that:
            1. Directly answers the original query
            2. Presents evidence in a logical order
            3. Highlights key findings
            4. Notes any gaps or limitations
            
            Use a formal, audit-friendly tone.
            """
            
            # Try GPT-4 first, fallback to GPT-3.5-turbo
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": context}
                    ],
                    temperature=0.2
                )
            except Exception as gpt4_error:
                print(f"GPT-4 not available for formatting, trying GPT-3.5-turbo: {str(gpt4_error)}")
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": context}
                    ],
                    temperature=0.2
                )
            
            return response.choices[0].message.content or "Unable to format evidence"
            
        except Exception as e:
            print(f"AI formatting failed, using fallback: {str(e)}")
            # Fallback to basic formatting when AI fails
            return self._format_evidence_fallback(evidence_items, query)
    
    def _format_evidence_fallback(self, evidence_items: List[Dict[str, Any]], query: str) -> str:
        """Fallback evidence formatting when AI is not available."""
        summary = f"Evidence Summary for: {query}\n"
        summary += "=" * 50 + "\n\n"
        
        if not evidence_items:
            summary += "No evidence found matching your query.\n"
            return summary
        
        # Group by source type
        by_source = {}
        for item in evidence_items:
            source_type = item.get('source_type', 'unknown')
            if source_type not in by_source:
                by_source[source_type] = []
            by_source[source_type].append(item)
        
        # Format by source
        for source_type, items in by_source.items():
            summary += f"\n{source_type.upper()} EVIDENCE ({len(items)} items):\n"
            summary += "-" * 30 + "\n"
            
            for i, item in enumerate(items, 1):
                summary += f"{i}. {item.get('title', 'Untitled')}\n"
                summary += f"   Source: {item.get('source', 'Unknown')}\n"
                summary += f"   Description: {item.get('description', 'No description')}\n"
                
                # Add confidence score if available
                confidence = item.get('confidence_score', 0)
                if confidence > 0:
                    summary += f"   Confidence: {confidence:.2f}\n"
                
                # Add key data if available
                data = item.get('data', {})
                if data and isinstance(data, dict):
                    # Show relevant data fields
                    relevant_fields = ['filename', 'total_matches', 'avg_relevance']
                    for field in relevant_fields:
                        if field in data:
                            summary += f"   {field.replace('_', ' ').title()}: {data[field]}\n"
                
                summary += "\n"
        
        summary += f"\nTotal Evidence Items: {len(evidence_items)}\n"
        summary += f"Query: {query}\n"
        
        return summary
    
    def _process_query_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback query processing when AI is not available."""
        query_lower = query.lower()
        
        # Basic keyword-based analysis
        query_type = "mixed"
        if any(word in query_lower for word in ["github", "pull request", "pr", "commit", "repository"]):
            query_type = "github"
        elif any(word in query_lower for word in ["jira", "ticket", "issue", "bug", "task"]):
            query_type = "jira"
        elif any(word in query_lower for word in ["document", "file", "upload", "csv", "excel", "pdf"]):
            query_type = "document"
        
        # Extract basic parameters
        parameters = {}
        
        # Look for names (capitalized words)
        words = query.split()
        names = [word for word in words if word[0].isupper() and len(word) > 2]
        if names:
            parameters["person"] = " ".join(names)
        
        # Look for numbers (could be PR numbers, ticket numbers, etc.)
        numbers = [word for word in words if word.isdigit()]
        if numbers:
            if query_type == "github":
                parameters["pr_number"] = numbers[0]
            elif query_type == "jira":
                parameters["ticket_key"] = f"PROJ-{numbers[0]}"
        
        # Look for specific terms
        if "assigned" in query_lower:
            parameters["assigned"] = True
        if "count" in query_lower:
            parameters["count"] = True
        if "list" in query_lower:
            parameters["list"] = True
        
        return {
            "query_type": query_type,
            "intent": f"Find evidence related to: {query}",
            "parameters": parameters,
            "confidence": 0.6,  # Higher confidence for fallback
            "fallback": True
        }
    
    def _process_query_github_fallback(self, query: str) -> Dict[str, Any]:
        """
        Fallback logic to select GitHubIntegration function based on keywords.
        """
        query_lower = query.lower()
        if "merged" in query_lower and "days" in query_lower:
            # Example: "Which PRs were merged in the last 7 days, and who approved them?"
            
            days = 7
            match = re.search(r'last (\d+) days', query_lower)
            if match:
                days = int(match.group(1))
            return {"function": "get_merged_prs_last_n_days", "parameters": {"n": days}}
        elif "waiting for review" in query_lower or "waiting review" in query_lower:
            hours = 24
            match = re.search(r'(\d+)\s*hours', query_lower)
            if match:
                hours = int(match.group(1))
            return {"function": "get_prs_waiting_for_review", "parameters": {"hours": hours}}
        elif "pr" in query_lower and "#" in query_lower:
            pr_number = None
            match = re.search(r'pr\s*#?(\d+)', query_lower)
            if match:
                pr_number = int(match.group(1))
            return {"function": "get_pr_details", "parameters": {"pr_number": pr_number}}
        elif "show me pull requests" in query_lower or "list prs" in query_lower:
            return {"function": "get_prs", "parameters": {}}
        else:
            return {"function": "get_prs", "parameters": {}}
