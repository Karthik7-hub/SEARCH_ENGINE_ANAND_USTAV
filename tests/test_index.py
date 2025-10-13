# FILE: tests/test_index.py
import numpy as np
import pytest
from app.models.faiss_manager import FaissManager


def test_faiss_flat_ip_build_and_search():
    dim = 8
    num_vectors = 100
    fm = FaissManager(dim)

    vectors = np.random.randn(num_vectors, dim).astype('float32')
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

    fm.build_index_flat_ip(vectors)

    assert fm.index is not None
    assert fm.index.ntotal == num_vectors

    query_vector = vectors[:1]
    distances, indices = fm.search(query_vector, k=3)

    assert indices.shape == (1, 3)
    assert indices[0][0] == 0
    assert pytest.approx(distances[0][0], 1e-6) == 1.0


def test_search_before_build_raises_error():
    fm = FaissManager(dim=4)
    query = np.random.rand(1, 4).astype('float32')

    with pytest.raises(RuntimeError, match="Index not built"):
        fm.search(query)
