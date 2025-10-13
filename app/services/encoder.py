# FILE: app/services/encoder.py
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache
import logging
from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_model(name: str = None) -> SentenceTransformer:
    model_name = name or settings.MODEL_NAME
    logger.info(f"Loading SentenceTransformer model: {model_name}")
    model = SentenceTransformer(model_name)
    return model


def normalize_embeddings(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return vectors / norms


def encode_texts(texts: list[str], batch_size: int = 64) -> np.ndarray:
    model = get_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        batch_size=batch_size,
        show_progress_bar=False
    )
    return normalize_embeddings(embeddings).astype("float32")


def encode_query(text: str) -> np.ndarray:
    model = get_model()
    embedding = model.encode([text], convert_to_numpy=True)
    return normalize_embeddings(embedding).astype("float32")
