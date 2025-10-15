# FILE: app/services/hybrid_search.py
from app.config import settings
from app.models.faiss_manager import FaissManager
from app.services.encoder import encode_query
from typing import List, Dict, Any, Optional
import logging
from thefuzz import process
from collections import Counter

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

    def _find_suggestion(self, query: str) -> Optional[str]:
        all_names = [item.get("name", "") for item in self.items]
        best_match, score = process.extractOne(query, all_names)
        return best_match if score > 80 else None

    def get_autocomplete_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        prefix_lower = prefix.lower()
        suggestions = {item.get("name") for item in self.items if item.get(
            "name", "").lower().startswith(prefix_lower)}
        return sorted(list(suggestions))[:limit]

    def _calculate_facets(self, candidates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        category_counts = Counter()
        price_counts = {
            "Under 50,000": 0, "50,000 - 100,000": 0,
            "100,000 - 200,000": 0, "Over 200,000": 0,
        }

        for result in candidates:
            item = result.get('item', {})
            if item.get('isCategory'):
                continue

            if category := item.get('category'):
                if cat_name := category.get('name'):
                    category_counts[cat_name] += 1

            if price := item.get('priceInfo', {}).get('amount'):
                if price < 50000:
                    price_counts["Under 50,000"] += 1
                elif 50000 <= price < 100000:
                    price_counts["50,000 - 100,000"] += 1
                elif 100000 <= price < 200000:
                    price_counts["100,000 - 200,000"] += 1
                else:
                    price_counts["Over 200,000"] += 1

        top_categories = [{"name": name, "count": count}
                          for name, count in category_counts.most_common(5)]
        price_ranges = [{"name": name, "count": count}
                        for name, count in price_counts.items() if count > 0]

        return {"categories": top_categories, "price_ranges": price_ranges}

    async def search(
        self, query: str, min_rating: Optional[float] = None, max_price: Optional[int] = None
    ) -> Dict[str, Any]:
        if not self.items:
            return {"categories": [], "services": [], "suggestion": None, "facets": None}

        query_embedding = encode_query(query)
        num_candidates = min(len(self.items), 500)
        distances, indices = self.fm.search(query_embedding, k=num_candidates)

        initial_candidates = self._compute_boosted_scores(
            query, indices[0].tolist(), distances[0].tolist())
        facets = self._calculate_facets(initial_candidates)
        filtered_candidates = self._apply_filters(
            initial_candidates, min_rating, max_price)

        suggestion = None
        if not filtered_candidates or filtered_candidates[0]['score'] < settings.DID_YOU_MEAN_THRESHOLD:
            suggestion = self._find_suggestion(query)

        top_categories, top_services = self._separate_results(
            filtered_candidates)

        return {"categories": top_categories, "services": top_services, "suggestion": suggestion, "facets": facets}

    def _apply_filters(self, candidates, min_rating, max_price):
        if not min_rating and not max_price:
            return candidates
        filtered = []
        for cand in candidates:
            item = cand['item']
            if item.get('isCategory'):
                filtered.append(cand)
                continue
            passes_rating = not min_rating or (
                item.get('avgRating', 0) >= min_rating)
            passes_price = not max_price or (
                item.get('priceInfo', {}).get('amount', float('inf')) <= max_price)
            if passes_rating and passes_price:
                filtered.append(cand)
        return filtered

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

    def _compute_boosted_scores(self, query: str, indices: List[int], distances: List[float]) -> List[Dict[str, Any]]:
        results = []
        q_words = set(query.lower().split())

        for score, idx in zip(distances, indices):
            if idx == -1 or idx >= len(self.items):
                continue

            item_object = self.items[idx]
            item_name = item_object.get("name", "").lower()
            item_desc = item_object.get("description", "").lower()
            semantic_score = float(score)
            boosted_score = semantic_score

            if item_object.get("isCategory"):
                boosted_score += settings.CATEGORY_BOOST
            elif any(word in item_name for word in q_words):
                boosted_score += settings.NAME_KEYWORD_BOOST
            elif any(word in item_desc for word in q_words):
                boosted_score += settings.DESC_KEYWORD_BOOST

            results.append(
                {"item": item_object, "score": boosted_score, "semantic_score": semantic_score})

        results.sort(key=lambda x: x['score'], reverse=True)
        return results
