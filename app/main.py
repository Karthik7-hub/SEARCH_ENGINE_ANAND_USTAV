# FILE: app/main.py
from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
import asyncio
import logging
from cachetools import TTLCache
from typing import Optional

from app.config import settings
from app.models.pydantic_models import (
    SearchResponse, StatusResponse, HealthResponse, RefreshResponse, AutocompleteResponse
)
from app.services.data_loader import fetch_and_extract_items, fetch_one_service
from app.services.encoder import create_blended_embeddings, get_model
from app.models.faiss_manager import FaissManager
from app.services.hybrid_search import HybridSearchEngine
from app.utils.persistence import load_items, save_items
from app.utils.database import connect_to_mongo, close_mongo_connection, get_database
from app.utils.locks import data_lock

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global State ---
faiss_manager: FaissManager | None = None
hybrid_engine: HybridSearchEngine | None = None
search_cache = TTLCache(maxsize=500, ttl=300)

# --- Real-Time Update Logic ---


async def _update_single_item(service_id: str):
    logger.info(f"Real-time update triggered for service ID: {service_id}")
    async with data_lock:
        item = await fetch_one_service(service_id)
        if item:
            embedding = create_blended_embeddings([item])
            faiss_manager.update_items([item], embedding)
            hybrid_engine.update_item_in_map(item)
            logger.info(
                f"Successfully updated item {service_id} in real-time.")
        else:
            faiss_manager.remove_items([service_id])
            hybrid_engine.remove_item_from_map(service_id)
            logger.info(f"Removed item {service_id} in real-time.")
        save_items(hybrid_engine.items)
        faiss_manager.save()


async def watch_mongodb_changes():
    db = get_database()
    if db is None:
        logger.error("Cannot start MongoDB watcher: No database connection.")
        return

    try:
        change_stream = db[settings.COLLECTION_NAME].watch()
        logger.info("MongoDB Change Stream watcher started...")
        async for change in change_stream:
            doc_id = str(change['documentKey']['_id'])
            if change['operationType'] in ['insert', 'update', 'replace', 'delete']:
                asyncio.create_task(_update_single_item(doc_id))
    except Exception as e:
        logger.error(
            f"MongoDB Change Stream watcher failed: {e}. Real-time updates are disabled.")

# --- Core Engine Management ---


async def _rebuild_search_engine_full():
    logger.info("Starting full engine rebuild...")
    global faiss_manager, hybrid_engine

    items = await fetch_and_extract_items()
    model_dim = get_model().get_sentence_embedding_dimension()

    async with data_lock:
        faiss_manager = FaissManager(dim=model_dim)
        if not items:
            faiss_manager.build_index([], None)
            hybrid_engine = HybridSearchEngine(faiss_manager, [])
        else:
            embeddings = create_blended_embeddings(items)
            faiss_manager.build_index(items, embeddings)
            hybrid_engine = HybridSearchEngine(faiss_manager, items)
            save_items(items)
            faiss_manager.save()
        logger.info(f"Full engine rebuild complete with {len(items)} items.")

# --- FastAPI Lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    await connect_to_mongo()

    items = load_items()
    if items:
        logger.info("Loading persisted engine from disk...")
        model_dim = get_model().get_sentence_embedding_dimension()
        global faiss_manager, hybrid_engine
        faiss_manager = FaissManager(dim=model_dim)
        if faiss_manager.load():
            hybrid_engine = HybridSearchEngine(faiss_manager, items)
            logger.info("Successfully loaded persisted search engine.")
        else:
            asyncio.create_task(_rebuild_search_engine_full())
    else:
        asyncio.create_task(_rebuild_search_engine_full())

    asyncio.create_task(watch_mongodb_changes())

    yield

    await close_mongo_connection()
    logger.info("Application shutdown.")

app = FastAPI(title="Smart Search API", version="3.0.0", lifespan=lifespan)

# --- API Endpoints ---


@app.get("/", response_model=StatusResponse, tags=["Health"])
def read_root():
    return StatusResponse(message="Smart Search API is running.")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    if hybrid_engine is None or faiss_manager is None or faiss_manager.index is None:
        return HealthResponse(status="initializing")
    try:
        asyncio.run(hybrid_engine.search("test"))
        return HealthResponse(status="ok")
    except Exception as e:
        logger.error(f"Health check failed during test search: {e}")
        return HealthResponse(status="unhealthy")


@app.post("/refresh", response_model=RefreshResponse, tags=["Admin"])
async def trigger_refresh():
    await _rebuild_search_engine_full()
    return RefreshResponse(
        message="Full data refresh and index rebuild complete.",
        n_items=len(hybrid_engine.items) if hybrid_engine else 0
    )


@app.get("/autocomplete", response_model=AutocompleteResponse, tags=["Search"])
def autocomplete(prefix: str):
    if hybrid_engine is None:
        raise HTTPException(
            status_code=503, detail="Search engine is not ready.")
    suggestions = hybrid_engine.get_autocomplete_suggestions(prefix)
    return AutocompleteResponse(suggestions=suggestions)


@app.get("/search", response_model=SearchResponse, tags=["Search"])
async def search(
    q: str,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_price: Optional[int] = Query(None, ge=0)
):
    if hybrid_engine is None:
        raise HTTPException(
            status_code=503, detail="Search engine is not ready.")

    cache_key = f"{q}:{min_rating}:{max_price}"
    if cache_key in search_cache:
        return search_cache[cache_key]

    results_dict = await hybrid_engine.search(q, min_rating=min_rating, max_price=max_price)
    response = SearchResponse(query=q, **results_dict)

    search_cache[cache_key] = response
    return response
