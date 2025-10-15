# FILE: app/models/pydantic_models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class SearchResultItem(BaseModel):
    item: Dict[str, Any]
    score: float
    semantic_score: Optional[float] = None


class FacetItem(BaseModel):
    name: str
    count: int


class Facets(BaseModel):
    categories: List[FacetItem]
    price_ranges: List[FacetItem]


class SearchResponse(BaseModel):
    query: str
    categories: List[SearchResultItem]
    services: List[SearchResultItem]
    suggestion: Optional[str] = None
    facets: Optional[Facets] = None
    message: Optional[str] = None


class AutocompleteResponse(BaseModel):
    suggestions: List[str]


class RefreshResponse(BaseModel):
    message: str
    n_items: int


class StatusResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
