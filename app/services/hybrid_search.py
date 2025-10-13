# FILE: app/services/hybrid_search.py (Corrected)

from app.config import settings
from app.models.faiss_manager import FaissManager
from app.services.encoder import encode_query
from app.utils.database import get_database, ObjectId
# --- FIX: Import the serialization function ---
from app.services.data_loader import deep_serialize_mongo_types
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    def __init__(self, faiss_manager: FaissManager, indexed_items: List[Dict[str, Any]]):
        self.fm = faiss_manager
        self.indexed_items = indexed_items
        self.db = get_database()

    async def _populate_results(self, service_ids: List[str]) -> Dict[str, Dict]:
        if not service_ids or self.db is None:
            return {}

        object_ids = [ObjectId(id_str) for id_str in service_ids]

        pipeline = [
            {'$match': {'_id': {'$in': object_ids}}},
            {
                '$lookup': {
                    'from': 'serviceproviders',
                    'localField': 'providers',
                    'foreignField': '_id',
                    'as': 'provider_details'
                }
            },
            {
                '$lookup': {
                    'from': 'categories',
                    'localField': 'categories',
                    'foreignField': '_id',
                    'as': 'category_details'
                }
            },
            {'$unwind': {'path': '$provider_details',
                         'preserveNullAndEmptyArrays': True}},
            {'$unwind': {'path': '$category_details',
                         'preserveNullAndEmptyArrays': True}},
            {
                '$project': {
                    'name': 1, 'description': 1, 'priceInfo': 1, 'images': 1,
                    'availability': 1, 'avgRating': 1, 'reviewCount': 1,
                    'currentBookingDates': 1, 'maxPeople': 1, 'minPeople': 1,
                    'mindaysprior': 1, 'createdAt': 1, 'updatedAt': 1,

                    'providers': '$provider_details',

                    'categories._id': '$category_details._id',
                    'categories.name': '$category_details.name',
                }
            }
        ]

        cursor = self.db[settings.COLLECTION_NAME].aggregate(pipeline)

        populated_docs = {}
        async for doc in cursor:
            # --- FIX: Apply the robust serialization to the entire document ---
            # This ensures ALL ObjectIds, datetimes, etc., are converted to strings.
            serialized_doc = deep_serialize_mongo_types(doc)
            doc_id = serialized_doc['_id']
            populated_docs[doc_id] = serialized_doc

        return populated_docs

    def _compute_boosted_scores(self, query: str, indices: List[int], distances: List[float]) -> List[Dict[str, Any]]:
        results = []
        q_words = set(query.lower().split())

        for score, idx in zip(distances, indices):
            if idx == -1:
                continue

            item_object = self.indexed_items[idx]
            item_name = item_object.get("name", "")

            semantic_score = float(score)
            boosted_score = semantic_score

            if item_object.get("isCategory"):
                boosted_score += settings.CATEGORY_BOOST
            elif any(word in item_name.lower() for word in q_words):
                boosted_score += settings.KEYWORD_BOOST

            final_result = {
                "item": item_object,
                "score": max(-1.0, min(1.0, boosted_score)),
                "semantic_score": semantic_score
            }
            results.append(final_result)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.indexed_items:
            return []

        query_embedding = encode_query(query)
        search_k = min(len(self.indexed_items), 50)
        distances, indices = self.fm.search(query_embedding, k=search_k)

        scored_results = self._compute_boosted_scores(
            query, indices[0].tolist(), distances[0].tolist())

        service_ids_to_fetch = [
            r['item']['_id'] for r in scored_results
            if not r['item'].get('isCategory') and '_id' in r['item']
        ]

        if service_ids_to_fetch:
            populated_services = await self._populate_results(service_ids_to_fetch)

            for result in scored_results:
                item_id = result['item'].get('_id')
                if item_id in populated_services:
                    result['item'] = populated_services[item_id]

        return scored_results[:k]
