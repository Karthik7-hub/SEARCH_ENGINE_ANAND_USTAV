# FILE: app/models/pydantic_models.py
from pydantic import BaseModel
from typing import List, Dict, Any


class SearchResultItem(BaseModel):
    item: Dict[str, Any]
    score: float


class SearchResponse(BaseModel):
    query: str
    categories: List[SearchResultItem]
    services: List[SearchResultItem]


class AutocompleteResponse(BaseModel):
    suggestions: List[str]


class RefreshResponse(BaseModel):
    message: str
    n_items: int


class StatusResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
