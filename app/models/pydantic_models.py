# FILE: app/models/pydantic_models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class SearchResultItem(BaseModel):
    item: Dict[str, Any]
    score: float
    semantic_score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    message: Optional[str] = None


class RefreshResponse(BaseModel):
    message: str
    n_items: int


class StatusResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
