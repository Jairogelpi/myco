import os
os.environ["DATABASE_URL"] = "sqlite:///./data/test_commons.db"

import pytest
from fastapi.testclient import TestClient
from commons_server.database import engine
from commons_server.models import Base


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    from commons_server.main import app
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_publish_skill(client):
    r = client.post("/skills", json={
        "name": "skill_ddg_search",
        "description": "Search using DuckDuckGo",
        "code": "def run(**kwargs): return 'results'",
        "agent_id": "agent_abc",
        "category": "research",
        "tags": ["search", "web"],
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "skill_ddg_search"
    assert data["total_downloads"] == 0
    assert data["total_uses"] == 0
    assert "id" in data
    assert "code" not in data


def test_search_returns_results(client):
    client.post("/skills", json={
        "name": "skill_ddg_search",
        "description": "Search using DuckDuckGo",
        "code": "def run(**kwargs): return 'results'",
        "agent_id": "agent_abc",
        "category": "research",
        "tags": [],
    })
    r = client.get("/skills?q=DuckDuckGo")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["name"] == "skill_ddg_search"
    assert "code" not in results[0]


def test_search_empty_returns_all(client):
    client.post("/skills", json={
        "name": "skill_a", "description": "A", "code": "def run(): pass",
        "agent_id": "x", "category": "other", "tags": []
    })
    r = client.get("/skills")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_skill_not_found(client):
    r = client.get("/skills/nonexistent-id")
    assert r.status_code == 404


def test_get_skill_code(client):
    publish = client.post("/skills", json={
        "name": "skill_x", "description": "X", "code": "def run(**kw): return 42",
        "agent_id": "agent_z", "category": "other", "tags": []
    })
    skill_id = publish.json()["id"]
    r = client.get(f"/skills/{skill_id}/code")
    assert r.status_code == 200
    assert r.json()["code"] == "def run(**kw): return 42"


def test_record_download_increments(client):
    publish = client.post("/skills", json={
        "name": "skill_x", "description": "X", "code": "def run(**kw): pass",
        "agent_id": "agent_z", "category": "other", "tags": []
    })
    skill_id = publish.json()["id"]
    r = client.post(f"/skills/{skill_id}/download")
    assert r.status_code == 200
    assert r.json()["total_downloads"] == 1
    r2 = client.post(f"/skills/{skill_id}/download")
    assert r2.json()["total_downloads"] == 2


def test_record_use_increments(client):
    publish = client.post("/skills", json={
        "name": "skill_y", "description": "Y", "code": "def run(**kw): pass",
        "agent_id": "agent_z", "category": "other", "tags": []
    })
    skill_id = publish.json()["id"]
    r = client.post(f"/skills/{skill_id}/use")
    assert r.status_code == 200
    assert r.json()["total_uses"] == 1


def test_search_by_category(client):
    client.post("/skills", json={
        "name": "skill_research", "description": "research skill", "code": "def run(**kw): pass",
        "agent_id": "a1", "category": "research", "tags": []
    })
    client.post("/skills", json={
        "name": "skill_write", "description": "writing skill", "code": "def run(**kw): pass",
        "agent_id": "a2", "category": "writing", "tags": []
    })
    r = client.get("/skills?category=research")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["name"] == "skill_research"
