# FILE: tests/test_search.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import MagicMock


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_search_when_engine_not_ready(client, mocker):
    mocker.patch("app.main.hybrid_engine", None)

    response = client.get("/search?q=test")

    assert response.status_code == 503
    assert "Search engine is not ready" in response.json()["detail"]


def test_search_with_empty_query(client, mocker):
    mocker.patch("app.main.hybrid_engine", MagicMock())

    response = client.get("/search?q=")

    assert response.status_code == 400
    assert "Query parameter 'q' cannot be empty" in response.json()["detail"]
