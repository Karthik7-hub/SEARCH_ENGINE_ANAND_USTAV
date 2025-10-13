# FILE: app/services/data_loader.py
from app.config import settings
from app.utils.database import get_database
import logging
from bson import ObjectId
from datetime import datetime
from collections.abc import MutableMapping, MutableSequence

logger = logging.getLogger(__name__)


def deep_serialize_mongo_types(obj):
    """
    Recursively traverses a data structure and converts all
    ObjectId and datetime instances to their string representation.
    """
    if isinstance(obj, ObjectId):
        return str(obj)

    if isinstance(obj, datetime):
        return obj.isoformat()

    if isinstance(obj, MutableMapping):
        return {k: deep_serialize_mongo_types(v) for k, v in obj.items()}

    if (isinstance(obj, MutableSequence) and
            not isinstance(obj, str)):
        return [deep_serialize_mongo_types(item) for item in obj]

    return obj


async def fetch_services_from_db() -> list:
    database = get_database()
    if database is None:
        logger.error("Database connection not available.")
        return []

    collection = database[settings.COLLECTION_NAME]
    services_cursor = collection.find({})

    services = []
    async for doc in services_cursor:
        services.append(deep_serialize_mongo_types(doc))

    return services


async def fetch_and_extract_items() -> list:
    try:
        services = await fetch_services_from_db()
        valid_services = [s for s in services if isinstance(
            s, dict) and s.get("name")]

        category_objects = [
            {"name": cat,
             "isCategory": True} for cat in settings.PREDEFINED_CATEGORIES
        ]

        combined_items = valid_services + category_objects

        log_message = (
            f"Fetched {len(valid_services)} services from DB, "
            f"combined with {len(category_objects)} categories "
            f"into {len(combined_items)} total items."
        )
        logger.info(log_message)

        return combined_items
    except Exception:
        logger.exception("Failed to fetch and process services from MongoDB.")
        return []
