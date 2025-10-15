# FILE: app/services/hybrid_search.py
from app.config import settings
from app.models.faiss_manager import FaissManager
from app.services.encoder import encode_query
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    def __init__(self, faiss_manager: FaissManager, items: List[Dict[str, Any]]):
        self.fm = faiss_manager
        self.items = items
        self.item_map = {item['_id']: item for item in items}

    def update_item_in_map(self, item: Dict[str, Any]):
        self.item_map[item['_id']] = item
        self.items = list(self.item_map.values())

    def remove_item_from_map(self, item_id: str):
        if item_id in self.item_map:
            del self.item_map[item_id]
            self.items = list(self.item_map.values())

    def get_autocomplete_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        prefix_lower = prefix.lower()
        suggestions = {item.get("name") for item in self.items if item.get(
            "name", "").lower().startswith(prefix_lower)}
        return sorted(list(suggestions))[:limit]

    async def search(self, query: str) -> Dict[str, Any]:
        if not self.items:
            return {"categories": [], "services": []}

        query_embedding = encode_query(query)

        num_candidates = min(len(self.items), 200)
        distances, indices = self.fm.search(query_embedding, k=num_candidates)

        ranked_results = self._compute_scores(
            indices[0].tolist(), distances[0].tolist())
        top_categories, top_services = self._separate_results(ranked_results)

        return {"categories": top_categories, "services": top_services}

    def _separate_results(self, final_ranked_list):
        top_categories, top_services, seen_ids = [], [], set()
        for result in final_ranked_list:
            if len(top_categories) >= 5 and len(top_services) >= 50:
                break
            item = result['item']
            item_id = item.get('_id')
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            if item.get('isCategory') and len(top_categories) < 5:
                top_categories.append(result)
            elif not item.get('isCategory') and len(top_services) < 50:
                top_services.append(result)
        return top_categories, top_services

    def _compute_scores(self, indices: List[int], distances: List[float]) -> List[Dict[str, Any]]:
        results = []
        for score, idx in zip(distances, indices):
            if idx == -1 or idx >= len(self.items):
                continue

            item_object = self.items[idx]
            final_score = float(score)

            if item_object.get("isCategory"):
                final_score += settings.CATEGORY_BOOST

            results.append({"item": item_object, "score": final_score})

        results.sort(key=lambda x: x['score'], reverse=True)
        return results
