from typing import Dict, Any, List, Optional
import json
import csv
import os
from datetime import datetime
from pathlib import Path

class EvidenceService:
    def __init__(self):
        self.storage_dir = "storage"
        os.makedirs(self.storage_dir, exist_ok=True)
        self.results_file = os.path.join(self.storage_dir, "query_results.json")
    
    async def store_query_result(self, query_id: str, query: str, evidence: List[Dict[str, Any]], summary: str) -> Dict[str, Any]:
        """Store query results to local storage."""
        result = {
            "query_id": query_id,
            "query": query,
            "evidence": evidence,
            "summary": summary,
            "created_at": datetime.now().isoformat(),
            "evidence_count": len(evidence)
        }
        
        # Load existing results
        results = self._load_results()
        results[query_id] = result
        
        # Save updated results
        self._save_results(results)
        
        return result
    
    async def get_query_result(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve query results from storage."""
        results = self._load_results()
        return results.get(query_id)
    
    async def export_evidence(self, query_id: str, evidence: List[Dict[str, Any]], format: str) -> str:
        """Export evidence to specified format."""
        export_dir = os.path.join(self.storage_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_{query_id}_{timestamp}.{format}"
        file_path = os.path.join(export_dir, filename)
        
        if format.lower() == "json":
            await self._export_json(evidence, file_path)
        elif format.lower() == "csv":
            await self._export_csv(evidence, file_path)
        elif format.lower() in ["xlsx", "xls"]:
            await self._export_excel(evidence, file_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return file_path
    
    def _load_results(self) -> Dict[str, Any]:
        """Load results from storage file."""
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_results(self, results: Dict[str, Any]):
        """Save results to storage file."""
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    async def _export_json(self, evidence: List[Dict[str, Any]], file_path: str):
        """Export evidence to JSON format."""
        with open(file_path, 'w') as f:
            json.dump(evidence, f, indent=2, default=str)
    
    async def _export_csv(self, evidence: List[Dict[str, Any]], file_path: str):
        """Export evidence to CSV format."""
        if not evidence:
            return
        
        # Flatten evidence items for CSV
        flattened_data = []
        for item in evidence:
            flat_item = {
                "source": item.get("source"),
                "source_type": item.get("source_type"),
                "title": item.get("title"),
                "description": item.get("description"),
                "confidence_score": item.get("confidence_score"),
                "timestamp": item.get("timestamp")
            }
            
            # Add key data fields
            data = item.get("data", {})
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    flat_item[f"data_{key}"] = value
                else:
                    flat_item[f"data_{key}"] = str(value)
            
            flattened_data.append(flat_item)
        
        # Write to CSV
        if flattened_data:
            fieldnames = set()
            for item in flattened_data:
                fieldnames.update(item.keys())
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                writer.writeheader()
                writer.writerows(flattened_data)
    
    async def _export_excel(self, evidence: List[Dict[str, Any]], file_path: str):
        """Export evidence to Excel format."""
        try:
            import pandas as pd
            
            # Convert evidence to DataFrame
            df_data = []
            for item in evidence:
                row = {
                    "Source": item.get("source"),
                    "Source Type": item.get("source_type"),
                    "Title": item.get("title"),
                    "Description": item.get("description"),
                    "Confidence Score": item.get("confidence_score"),
                    "Timestamp": item.get("timestamp")
                }
                
                # Add data fields
                data = item.get("data", {})
                for key, value in data.items():
                    if isinstance(value, (str, int, float, bool)):
                        row[f"Data: {key}"] = value
                    else:
                        row[f"Data: {key}"] = str(value)
                
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            df.to_excel(file_path, index=False)
            
        except ImportError:
            # Fallback to CSV if pandas not available
            csv_path = file_path.replace('.xlsx', '.csv').replace('.xls', '.csv')
            await self._export_csv(evidence, csv_path)
            return csv_path
    