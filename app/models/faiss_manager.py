# FILE: app/models/faiss_manager.py
import faiss
import numpy as np
from app.config import settings
from app.utils.persistence import save_faiss_index, load_faiss_index
import logging

logger = logging.getLogger(__name__)


class FaissManager:
    def __init__(self, dim: int):
        self.dim = dim
        self.index: faiss.Index | None = None

    def build_index_flat_ip(self, embeddings: np.ndarray):
        logger.info(f"Building IndexFlatIP for {embeddings.shape[0]} vectors.")
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embeddings)

    def build_hnsw(self, embeddings: np.ndarray, M: int = 32):
        logger.info(f"Building HNSW index for {embeddings.shape[0]} vectors.")
        index = faiss.IndexHNSWFlat(self.dim, M, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = 200
        index.add(embeddings)
        self.index = index

    def search(
        self, query_embeddings: np.ndarray, k: int = 10
    ) -> tuple[np.ndarray, np.ndarray]:
        if self.index is None:
            logger.error("Search attempted before index was built.")
            raise RuntimeError("Index not built or loaded.")
        return self.index.search(query_embeddings, k)

    def save(self, path: str = settings.FAISS_INDEX_PATH):
        if self.index is None:
            raise RuntimeError("Save attempted before index was built.")
        save_faiss_index(self.index, path)
        logger.info(f"FAISS index saved to {path}")

    def load(self, path: str = settings.FAISS_INDEX_PATH) -> bool:
        index = load_faiss_index(path)
        if index is None:
            return False
        if index.d != self.dim:
            logger.warning(
                f"Loaded index dimension ({index.d}) mismatches manager "
                f"dimension ({self.dim})."
            )
            return False
        self.index = index
        logger.info(f"Successfully loaded FAISS index from {path}")
        return True
