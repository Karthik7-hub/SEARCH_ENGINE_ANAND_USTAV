# FILE: app/utils/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)


class DBMotor:
    client: AsyncIOMotorClient = None


db = DBMotor()


async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    await db.client.admin.command('ping')
    logger.info("Successfully connected to MongoDB.")


async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
    logger.info("MongoDB connection closed.")


def get_database():
    if db.client:
        return db.client[settings.DATABASE_NAME]
    return None
