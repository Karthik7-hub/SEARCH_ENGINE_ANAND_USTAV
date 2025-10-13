# FILE: app/main.py
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import asyncio
import logging
from app.config import settings
from app.models.pydantic_models import (
    SearchResponse, StatusResponse, HealthResponse, RefreshResponse)
from app.services.data_loader import fetch_and_extract_items
from app.services.encoder import encode_texts, get_model
from app.models.faiss_manager import FaissManager
from app.services.hybrid_search import HybridSearchEngine
from app.utils.persistence import load_items, save_items, save_embeddings
from app.utils.database import connect_to_mongo, close_mongo_connection
from app.utils.locks import data_lock
from fastapi.middleware.cors import CORSMiddleware

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Global State ---
faiss_manager: FaissManager | None = None
hybrid_engine: HybridSearchEngine | None = None

# --- Core Logic ---


async def _update_search_engine(items: list[dict]):
    global faiss_manager, hybrid_engine

    if not items:
        logger.warning("Update skipped: no items provided.")
        return

    logger.info(f"Starting engine update with {len(items)} items.")

    item_names = [item.get("name", "") for item in items]
    embeddings = encode_texts(item_names)
    dim = embeddings.shape[1]

    async with data_lock:
        new_fm = FaissManager(dim)
        if len(items) < 10000:
            new_fm.build_index_flat_ip(embeddings)
        else:
            new_fm.build_hnsw(embeddings)

        new_fm.save()
        save_items(items, settings.ITEMS_PATH)
        save_embeddings(embeddings, settings.EMBEDDINGS_PATH)

        faiss_manager = new_fm
        hybrid_engine = HybridSearchEngine(faiss_manager, indexed_items=items)
        logger.info(f"Successfully updated engine with {len(items)} items.")


async def refresh_data_task():
    logger.info("Executing data refresh task...")
    try:
        new_items = await fetch_and_extract_items()
        await _update_search_engine(new_items)
    except Exception:
        logger.exception("Data refresh task failed.")


async def periodic_refresh_scheduler():
    while True:
        await asyncio.sleep(settings.REFRESH_SCHEDULE_SECONDS)
        await refresh_data_task()

# --- FastAPI Lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    await connect_to_mongo()

    items = load_items()
    if items:
        logger.info(f"Found {len(items)} items on disk.")
        model_dim = get_model().get_sentence_embedding_dimension()
        fm = FaissManager(dim=model_dim)
        if fm.load():
            global faiss_manager, hybrid_engine
            faiss_manager = fm
            hybrid_engine = HybridSearchEngine(
                faiss_manager, indexed_items=items)
            logger.info("Successfully loaded persisted search engine.")
        else:
            logger.warning("Items found but failed to load index. Refreshing.")
            await refresh_data_task()
    else:
        logger.info("No data found. Triggering initial data fetch.")
        await refresh_data_task()

    asyncio.create_task(periodic_refresh_scheduler())

    yield

    await close_mongo_connection()
    logger.info("Application shutdown.")


app = FastAPI(title="Smart Search API", lifespan=lifespan)

# --- API Endpoints ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/", response_model=StatusResponse)
def read_root():
    return StatusResponse(message="Smart Search API is running.")


@app.get("/health", response_model=HealthResponse)
def health_check():
    is_ready = all([hybrid_engine, faiss_manager, faiss_manager.index])
    return HealthResponse(status="ready" if is_ready else "initializing")


@app.post("/refresh", response_model=RefreshResponse)
async def trigger_refresh():
    async with data_lock:
        new_items = await fetch_and_extract_items()
        if not new_items:
            raise HTTPException(
                status_code=502,
                detail="Failed to fetch new items from the data source."
            )

        await _update_search_engine(new_items)
        return RefreshResponse(
            message="Successfully refreshed data and rebuilt index.",
            n_items=len(new_items)
        )


@app.get("/search", response_model=SearchResponse)
async def search(q: str, k: int = 25):
    if hybrid_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Search engine is not ready. Please wait for initialization"
        )

    if not q:
        raise HTTPException(
            status_code=400,
            detail="Query parameter 'q' cannot be empty."
        )

    results = await hybrid_engine.search(q, k=k)
    return SearchResponse(query=q, results=results)
