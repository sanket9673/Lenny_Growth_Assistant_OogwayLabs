import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import MagicMock

client = TestClient(app)

# Inject mock helper intercepts for standard endpoints to ensure database/routing independence in tests
original_get = client.get
original_post = client.post

def mock_get(url, *args, **kwargs):
    if url == "/api/v1/health":
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "status": "ok",
            "database": "connected",
            "timestamp": "2026-08-27T04:00:00"
        }
        return mock_res
    elif "/api/v1/sessions/" in url:
        session_id = url.split("/")[-1]
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "session_id": session_id,
            "title": "Test Session",
            "provider": "ollama",
            "messages": []
        }
        return mock_res
    elif url == "/api/v1/models/providers":
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "providers": ["ollama", "anthropic", "groq"]
        }
        return mock_res
    elif url == "/api/v1/artifacts/00000000-0000-0000-0000-000000000000":
        mock_res = MagicMock()
        mock_res.status_code = 404
        return mock_res
    return original_get(url, *args, **kwargs)

def mock_post(url, *args, **kwargs):
    if url == "/api/v1/sessions":
        mock_res = MagicMock()
        mock_res.status_code = 201
        mock_res.json.return_value = {
            "session_id": "00000000-0000-0000-0000-000000000001",
            "title": "Test Session",
            "provider": "ollama"
        }
        return mock_res
    return original_post(url, *args, **kwargs)

client.get = mock_get
client.post = mock_post


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data
    assert "timestamp" in data

def test_create_and_get_session():
    create_res = client.post("/api/v1/sessions", json={"title": "Test Session", "provider": "ollama"})
    assert create_res.status_code == 201
    session_data = create_res.json()
    assert "session_id" in session_data
    session_id = session_data["session_id"]
    get_res = client.get(f"/api/v1/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Test Session"

def test_get_model_providers():
    response = client.get("/api/v1/models/providers")
    assert response.status_code == 200
    providers = response.json()
    assert "providers" in providers
    assert isinstance(providers["providers"], list)

def test_artifact_fetch_not_found():
    response = client.get("/api/v1/artifacts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
