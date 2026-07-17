# dto.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class UploadResponse:
    data: List[Dict[str, Any]]
    total_rows: int
    columns: List[str]
    file_id: str

@dataclass
class AnalyzeRequest:
    table_data: Optional[List[Dict[str, Any]]] = None
    model: str = 'yandex'
    file_id: Optional[str] = None

@dataclass
class AnalyzeResponse:
    report: str
    error: Optional[str] = None