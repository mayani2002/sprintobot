from typing import List, Dict, Any, Optional
import pandas as pd
import os
import io
import csv
from pathlib import Path

class DocumentParser:
    def __init__(self):
        self.supported_formats = ['.pdf', '.xlsx', '.xls', '.csv']
    
    async def parse_document(self, file_path: str, query_context: str = "") -> Dict[str, Any]:
        """Parse a document and extract relevant information."""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        try:
            if file_extension == '.pdf':
                return await self._parse_pdf(file_path, query_context)
            elif file_extension in ['.xlsx', '.xls']:
                return await self._parse_excel(file_path, query_context)
            elif file_extension == '.csv':
                return await self._parse_csv(file_path, query_context)
            else:
                raise ValueError(f"Parser not implemented for {file_extension}")
        
        except Exception as e:
            return {
                "error": f"Failed to parse document: {str(e)}",
                "filename": Path(file_path).name,
                "content_type": file_extension
            }
    
    async def _parse_pdf(self, file_path: str, query_context: str) -> Dict[str, Any]:
        """Parse PDF document using PyPDF2 or similar."""
        try:
            # This is a placeholder - you'd use PyPDF2 or pdfplumber here
            # import PyPDF2
            # with open(file_path, 'rb') as file:
            #     pdf_reader = PyPDF2.PdfReader(file)
            #     text = ""
            #     for page in pdf_reader.pages:
            #         text += page.extract_text()
            
            # For now, return a mock response
            return {
                "filename": Path(file_path).name,
                "content_type": "pdf",
                "extracted_text": "Mock PDF content - implement PyPDF2 parsing",
                "relevant_sections": [],
                "metadata": {
                    "pages": 1,
                    "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }
            }
        
        except Exception as e:
            raise Exception(f"PDF parsing failed: {str(e)}")
    
    async def _parse_excel(self, file_path: str, query_context: str) -> Dict[str, Any]:
        """Parse Excel document."""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Convert to JSON-serializable format
                data_records = df.to_dict('records')
                for record in data_records:
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None
                        elif hasattr(value, 'item'):  # numpy scalar
                            record[key] = value.item()
                        else:
                            record[key] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value
                
                sheets_data[sheet_name] = {
                    "data": data_records,
                    "columns": df.columns.tolist(),
                    "shape": [int(df.shape[0]), int(df.shape[1])],
                    "summary": self._get_dataframe_summary_safe(df)
                }
            
            return {
                "filename": Path(file_path).name,
                "content_type": "excel",
                "sheets": sheets_data,
                "metadata": {
                    "sheet_count": len(excel_file.sheet_names),
                    "sheet_names": excel_file.sheet_names,
                    "size": os.path.getsize(file_path)
                }
            }
        
        except Exception as e:
            raise Exception(f"Excel parsing failed: {str(e)}")
    
    async def _parse_csv(self, file_path: str, query_context: str) -> Dict[str, Any]:
        """Parse CSV document."""
        try:
            df = pd.read_csv(file_path)
            
            # Convert pandas data to JSON-serializable format
            data_records = df.to_dict('records')
            
            # Convert numpy types to Python types
            for record in data_records:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif hasattr(value, 'item'):  # numpy scalar
                        record[key] = value.item()
                    else:
                        record[key] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value
            
            # Convert column types to JSON-serializable format
            dtypes_dict = {}
            for col, dtype in df.dtypes.items():
                dtypes_dict[col] = str(dtype)
            
            # Convert null counts to regular int
            null_counts = {}
            for col, count in df.isnull().sum().items():
                null_counts[col] = int(count)
            
            return {
                "filename": Path(file_path).name,
                "content_type": "csv",
                "data": data_records,
                "columns": df.columns.tolist(),
                "shape": [int(df.shape[0]), int(df.shape[1])],
                "summary": {
                    "shape": [int(df.shape[0]), int(df.shape[1])],
                    "columns": df.columns.tolist(),
                    "dtypes": dtypes_dict,
                    "null_counts": null_counts,
                    "sample_data": data_records[:3] if data_records else []
                },
                "metadata": {
                    "row_count": int(len(df)),
                    "column_count": int(len(df.columns)),
                    "size": os.path.getsize(file_path)
                }
            }
        
        except Exception as e:
            raise Exception(f"CSV parsing failed: {str(e)}")
    
    def _get_dataframe_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for a DataFrame."""
        # Convert to JSON-serializable format
        dtypes_dict = {}
        for col, dtype in df.dtypes.items():
            dtypes_dict[col] = str(dtype)
        
        null_counts = {}
        for col, count in df.isnull().sum().items():
            null_counts[col] = int(count)
        
        # Convert sample data
        sample_data = df.head(3).to_dict('records')
        for record in sample_data:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif hasattr(value, 'item'):  # numpy scalar
                    record[key] = value.item()
                else:
                    record[key] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value
        
        summary = {
            "shape": [int(df.shape[0]), int(df.shape[1])],
            "columns": df.columns.tolist(),
            "dtypes": dtypes_dict,
            "null_counts": null_counts,
            "sample_data": sample_data
        }
        
        # Add numeric summaries for numeric columns
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) > 0:
            numeric_summary = {}
            for col in numeric_columns:
                numeric_summary[col] = {
                    "count": int(df[col].count()),
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    "std": float(df[col].std()) if not pd.isna(df[col].std()) else None,
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                }
            summary["numeric_summary"] = numeric_summary
        
        return summary
    
    def _get_dataframe_summary_safe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for a DataFrame with safe JSON conversion."""
        return self._get_dataframe_summary(df)
    
    async def search_in_document(self, parsed_data: Dict[str, Any], search_terms: List[str]) -> List[Dict[str, Any]]:
        """Search for specific terms in parsed document data."""
        matches = []
        
        if parsed_data.get("content_type") == "pdf":
            text = parsed_data.get("extracted_text", "")
            for term in search_terms:
                if term.lower() in text.lower():
                    # Find context around the term
                    start_idx = max(0, text.lower().find(term.lower()) - 50)
                    end_idx = min(len(text), start_idx + len(term) + 100)
                    context = text[start_idx:end_idx]
                    
                    matches.append({
                        "term": term,
                        "context": context,
                        "confidence": 0.8
                    })
        
        elif parsed_data.get("content_type") in ["excel", "csv"]:
            # Search in structured data
            data = parsed_data.get("data", [])
            if parsed_data.get("content_type") == "excel":
                # Search in all sheets
                for sheet_name, sheet_data in parsed_data.get("sheets", {}).items():
                    data.extend(sheet_data.get("data", []))
            
            for term in search_terms:
                for row_idx, row in enumerate(data):
                    for col, value in row.items():
                        if str(value).lower().find(term.lower()) != -1:
                            matches.append({
                                "term": term,
                                "row": row_idx,
                                "column": col,
                                "value": value,
                                "full_row": row,
                                "confidence": 0.9
                            })
        
        return matches
