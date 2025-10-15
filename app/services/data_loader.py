# FILE: app/services/data_loader.py
from app.config import settings
from app.utils.database import get_database
import logging
from bson import ObjectId
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def serialize_mongo_doc(doc):
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    if "category" in doc and doc.get("category") and "_id" in doc["category"]:
        if isinstance(doc["category"]["_id"], ObjectId):
            doc["category"]["_id"] = str(doc["category"]["_id"])
    return doc


async def fetch_services_from_db() -> list:
    database = get_database()
    if database is None:
        return []

    services_collection = database[settings.COLLECTION_NAME]
    pipeline = [
        {"$lookup": {
            "from": "categories", "localField": "categories",
            "foreignField": "_id", "as": "category_info"
        }},
        {"$unwind": {"path": "$category_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 1, "name": 1, "description": 1, "priceInfo": 1, "avgRating": 1,
            "category": "$category_info", "updatedAt": 1
        }}
    ]
    cursor = services_collection.aggregate(pipeline)
    return [serialize_mongo_doc(doc) async for doc in cursor]


async def fetch_and_extract_items() -> list:
    try:
        services = await fetch_services_from_db()
        valid_services = [s for s in services if s.get("name")]
        category_objects = [
            {
                "name": cat,
                "isCategory": True,
                "_id": cat.lower().replace(" ", "-").replace("&", "and")
            } for cat in settings.PREDEFINED_CATEGORIES
        ]
        combined_items = valid_services + category_objects
        logger.info(
            f"Fetched {len(valid_services)} services from DB, combined with {len(category_objects)} categories.")
        return combined_items
    except Exception:
        logger.exception("Failed to fetch and process services from MongoDB.")
        return []


async def fetch_one_service(service_id: str) -> Dict[str, Any] | None:
    db = get_database()
    if db is None:
        return None
    pipeline = [
        {"$match": {"_id": ObjectId(service_id)}},
        {"$lookup": {"from": "categories", "localField": "categories",
                     "foreignField": "_id", "as": "category_info"}},
        {"$unwind": {"path": "$category_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {"_id": 1, "name": 1, "description": 1, "priceInfo": 1,
                      "avgRating": 1, "category": "$category_info", "updatedAt": 1}}
    ]
    result = await db[settings.COLLECTION_NAME].aggregate(pipeline).to_list(1)
    return serialize_mongo_doc(result[0]) if result else None
