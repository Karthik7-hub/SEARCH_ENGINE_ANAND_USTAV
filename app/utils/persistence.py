# FILE: app/utils/persistence.py
import json
import numpy as np
import os
import faiss
from typing import List, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

os.makedirs(os.path.dirname(settings.EMBEDDINGS_PATH), exist_ok=True)


def save_items(items: List[Dict[str, Any]], path: str = settings.ITEMS_PATH):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Failed to save items to {path}: {e}")


def load_items(path: str = settings.ITEMS_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load items from {path}: {e}")
        return []


def save_embeddings(embeddings: np.ndarray,
                    path: str = settings.EMBEDDINGS_PATH):
    try:
        np.save(path, embeddings)
    except IOError as e:
        logger.error(f"Failed to save embeddings to {path}: {e}")


def load_embeddings(path: str = settings.EMBEDDINGS_PATH) -> np.ndarray | None:
    if not os.path.exists(path):
        return None
    try:
        return np.load(path)
    except (ValueError, IOError) as e:
        logger.error(f"Error loading embeddings from {path}: {e}")
        return None


def save_faiss_index(index: faiss.Index,
                     path: str = settings.FAISS_INDEX_PATH):
    try:
        faiss.write_index(index, path)
    except (RuntimeError, faiss.FaissException) as e:
        logger.error(f"Failed to save FAISS index to {path}: {e}")


def load_faiss_index(
    path: str = settings.FAISS_INDEX_PATH
) -> faiss.Index | None:
    if not os.path.exists(path):
        return None
    try:
        return faiss.read_index(path)
    except (RuntimeError, faiss.FaissException) as e:
        logger.error(f"Error loading FAISS index from {path}: {e}")
        return None
