# Skill Commons v0.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a global public skill registry where Myco agents publish Karpathy-generated skills, operators discover and approve downloads, and the commons tracks reputation via download/use counters.

**Architecture:** Three layers: (1) a standalone FastAPI server in `commons_server/` with PostgreSQL that stores and serves skills; (2) a `CommonsClient` singleton in `myco/commons_client.py` that wraps all HTTP calls; (3) four new `/commons/` endpoints in `main.py` plus a discovery hook in `improvement.py`. The commons is always optional — if `COMMONS_URL` is empty, everything degrades gracefully.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, httpx, pytest, SQLite (tests) / PostgreSQL (production)

---

## Files Created / Modified

| File | Action | Purpose |
|------|--------|---------|
| `myco/config.py` | Modify | Add `COMMONS_URL` setting |
| `.env.example` | Modify | Document `COMMONS_URL` |
| `myco/commons_client.py` | Create | HTTP wrapper for commons server — all methods, never raises |
| `commons_server/__init__.py` | Create | Empty, makes it a package |
| `commons_server/database.py` | Create | SQLAlchemy engine + session + `get_db` dependency |
| `commons_server/models.py` | Create | `CommonsSkill` ORM model |
| `commons_server/main.py` | Create | FastAPI app with all 7 endpoints |
| `commons_server/requirements.txt` | Create | Dependencies for the commons server |
| `main.py` | Modify | Add 4 `/commons/` endpoints |
| `myco/improvement.py` | Modify | Add commons suggestions to `execute_with_skills` |
| `tests/__init__.py` | Create | Empty, makes tests a package |
| `tests/test_commons_client.py` | Create | Unit tests for CommonsClient |
| `tests/test_commons_server.py` | Create | Integration tests for commons server endpoints |

---

## Task 1: Add COMMONS_URL to config

**Files:**
- Modify: `myco/config.py`
- Modify: `.env.example`

- [ ] **Step 1: Add `COMMONS_URL` to Settings**

Edit `myco/config.py` — add one line inside the `Settings` class, after `KERNEL_TAX_RATE`:

```python
COMMONS_URL: str = ""  # e.g. https://myco-commons.onrender.com — empty disables commons
```

Full updated class:

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/myco.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    KERNEL_TAX_RATE: float = 0.15
    AGENT_BUDGET_DEFAULT: float = 100.0
    MAX_ACTIVE_AGENTS: int = 20
    AGENT_LIFESPAN_HOURS: int = 72

    COMMONS_URL: str = ""  # e.g. https://myco-commons.onrender.com

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 2: Document in `.env.example`**

Append to the end of `.env.example`:

```bash
# Skill Commons (optional — leave empty to disable)
COMMONS_URL=
```

- [ ] **Step 3: Verify**

```bash
python -c "from myco.config import settings; print('COMMONS_URL:', repr(settings.COMMONS_URL))"
```

Expected output: `COMMONS_URL: ''`

- [ ] **Step 4: Commit**

```bash
git add myco/config.py .env.example
git commit -m "feat(commons): add COMMONS_URL config setting"
```

---

## Task 2: CommonsClient

**Files:**
- Create: `myco/commons_client.py`
- Create: `tests/__init__.py`
- Create: `tests/test_commons_client.py`

- [ ] **Step 1: Create `tests/__init__.py`**

Create empty file `tests/__init__.py`.

- [ ] **Step 2: Write failing tests**

Create `tests/test_commons_client.py`:

```python
import json
from unittest.mock import patch, MagicMock
from myco.commons_client import CommonsClient


def test_is_available_false_when_no_url():
    client = CommonsClient("")
    assert client.is_available() is False


def test_is_available_true_when_url_set():
    client = CommonsClient("http://localhost:9000")
    assert client.is_available() is True


def test_search_returns_empty_when_unavailable():
    client = CommonsClient("")
    assert client.search("duckduckgo") == []


def test_publish_returns_none_when_unavailable():
    client = CommonsClient("")
    result = client.publish("skill", "desc", "code", "agent1")
    assert result is None


def test_search_calls_get_with_query():
    client = CommonsClient("http://localhost:9000")
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "abc", "name": "skill_ddg"}]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response) as mock_get:
        result = client.search("duckduckgo")

    mock_get.assert_called_once_with(
        "http://localhost:9000/skills",
        params={"q": "duckduckgo"},
        timeout=10
    )
    assert result == [{"id": "abc", "name": "skill_ddg"}]


def test_search_returns_empty_on_exception():
    client = CommonsClient("http://localhost:9000")
    with patch("httpx.get", side_effect=Exception("timeout")):
        result = client.search("anything")
    assert result == []


def test_publish_posts_correct_payload():
    client = CommonsClient("http://localhost:9000")
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "xyz", "name": "my_skill"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response) as mock_post:
        result = client.publish("my_skill", "does X", "def run(): pass", "agent42", "research", ["search"])

    mock_post.assert_called_once_with(
        "http://localhost:9000/skills",
        json={
            "name": "my_skill",
            "description": "does X",
            "code": "def run(): pass",
            "agent_id": "agent42",
            "category": "research",
            "tags": ["search"],
        },
        timeout=10,
    )
    assert result == {"id": "xyz", "name": "my_skill"}


def test_get_code_returns_none_on_missing():
    client = CommonsClient("http://localhost:9000")
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("404")
    with patch("httpx.get", return_value=mock_response):
        result = client.get_code("nonexistent")
    assert result is None


def test_record_download_returns_false_when_unavailable():
    client = CommonsClient("")
    assert client.record_download("abc") is False


def test_record_use_returns_false_on_exception():
    client = CommonsClient("http://localhost:9000")
    with patch("httpx.post", side_effect=Exception("network error")):
        assert client.record_use("abc") is False
```

- [ ] **Step 3: Run tests — expect FAIL**

```bash
python -m pytest tests/test_commons_client.py -v
```

Expected: `ImportError` — `myco/commons_client.py` does not exist yet.

- [ ] **Step 4: Create `myco/commons_client.py`**

```python
import httpx
from typing import Optional


class CommonsClient:
    """HTTP client for the Myco Skill Commons server. Never raises — degrades gracefully."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/") if base_url else ""

    def is_available(self) -> bool:
        return bool(self.base_url)

    def publish(
        self,
        name: str,
        description: str,
        code: str,
        agent_id: str,
        category: str = "other",
        tags: list = None,
    ) -> Optional[dict]:
        if not self.is_available():
            return None
        try:
            r = httpx.post(
                f"{self.base_url}/skills",
                json={
                    "name": name,
                    "description": description,
                    "code": code,
                    "agent_id": agent_id,
                    "category": category,
                    "tags": tags or [],
                },
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def search(self, query: str, category: str = None) -> list:
        if not self.is_available():
            return []
        try:
            params = {"q": query}
            if category:
                params["category"] = category
            r = httpx.get(f"{self.base_url}/skills", params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return []

    def get_code(self, skill_id: str) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            r = httpx.get(f"{self.base_url}/skills/{skill_id}/code", timeout=10)
            r.raise_for_status()
            return r.json()["code"]
        except Exception:
            return None

    def record_download(self, skill_id: str) -> bool:
        if not self.is_available():
            return False
        try:
            r = httpx.post(f"{self.base_url}/skills/{skill_id}/download", timeout=10)
            r.raise_for_status()
            return True
        except Exception:
            return False

    def record_use(self, skill_id: str) -> bool:
        if not self.is_available():
            return False
        try:
            r = httpx.post(f"{self.base_url}/skills/{skill_id}/use", timeout=10)
            r.raise_for_status()
            return True
        except Exception:
            return False


# Module-level singleton — import this in main.py and improvement.py
from myco.config import settings
commons_client = CommonsClient(settings.COMMONS_URL)
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
python -m pytest tests/test_commons_client.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add myco/commons_client.py tests/__init__.py tests/test_commons_client.py
git commit -m "feat(commons): add CommonsClient with graceful degradation"
```

---

## Task 3: Commons Server — DB layer

**Files:**
- Create: `commons_server/__init__.py`
- Create: `commons_server/database.py`
- Create: `commons_server/models.py`

- [ ] **Step 1: Create `commons_server/__init__.py`**

Create empty file `commons_server/__init__.py`.

- [ ] **Step 2: Create `commons_server/database.py`**

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./commons.db")

# Render uses postgres:// but SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Create `commons_server/models.py`**

```python
import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CommonsSkill(Base):
    __tablename__ = "commons_skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    agent_id = Column(String, nullable=False)
    category = Column(String, nullable=False, default="other")
    tags = Column(Text, nullable=False, default="[]")  # JSON-encoded list
    total_downloads = Column(Integer, nullable=False, default=0)
    total_uses = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self, include_code: bool = False) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_id": self.agent_id,
            "category": self.category,
            "tags": json.loads(self.tags),
            "total_downloads": self.total_downloads,
            "total_uses": self.total_uses,
            "created_at": self.created_at.isoformat(),
        }
        if include_code:
            d["code"] = self.code
        return d
```

- [ ] **Step 4: Verify models import cleanly**

```bash
python -c "from commons_server.models import CommonsSkill; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add commons_server/__init__.py commons_server/database.py commons_server/models.py
git commit -m "feat(commons): add commons server DB layer"
```

---

## Task 4: Commons Server — FastAPI app

**Files:**
- Create: `commons_server/main.py`
- Create: `commons_server/requirements.txt`
- Create: `tests/test_commons_server.py`

- [ ] **Step 1: Create `commons_server/requirements.txt`**

```
fastapi>=0.111.0
uvicorn>=0.30.0
sqlalchemy>=2.0.0
pydantic>=2.7.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.0
httpx>=0.27.0
```

- [ ] **Step 2: Write failing tests**

Create `tests/test_commons_server.py`:

```python
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
    assert "code" not in data  # code not exposed in publish response


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
```

- [ ] **Step 3: Run tests — expect FAIL**

```bash
python -m pytest tests/test_commons_server.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `commons_server/main.py` does not exist yet.

- [ ] **Step 4: Create `commons_server/main.py`**

```python
import uuid
import json
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from commons_server.database import get_db, engine
from commons_server.models import Base, CommonsSkill

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Myco Skill Commons", version="0.3.0")


class PublishRequest(BaseModel):
    name: str
    description: str
    code: str
    agent_id: str
    category: str = "other"
    tags: list = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/skills", status_code=201)
def publish_skill(req: PublishRequest, db: Session = Depends(get_db)):
    skill = CommonsSkill(
        id=str(uuid.uuid4()),
        name=req.name,
        description=req.description,
        code=req.code,
        agent_id=req.agent_id,
        category=req.category,
        tags=json.dumps(req.tags),
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill.to_dict()


@app.get("/skills")
def search_skills(q: str = "", category: str = None, db: Session = Depends(get_db)):
    query = db.query(CommonsSkill)
    if q:
        query = query.filter(
            CommonsSkill.name.ilike(f"%{q}%") | CommonsSkill.description.ilike(f"%{q}%")
        )
    if category:
        query = query.filter(CommonsSkill.category == category)
    skills = query.order_by(CommonsSkill.total_downloads.desc()).limit(50).all()
    return [s.to_dict() for s in skills]


@app.get("/skills/{skill_id}")
def get_skill(skill_id: str, db: Session = Depends(get_db)):
    skill = db.query(CommonsSkill).filter(CommonsSkill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill.to_dict()


@app.get("/skills/{skill_id}/code")
def get_skill_code(skill_id: str, db: Session = Depends(get_db)):
    skill = db.query(CommonsSkill).filter(CommonsSkill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"code": skill.code}


@app.post("/skills/{skill_id}/download")
def record_download(skill_id: str, db: Session = Depends(get_db)):
    skill = db.query(CommonsSkill).filter(CommonsSkill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill.total_downloads += 1
    db.commit()
    return {"total_downloads": skill.total_downloads}


@app.post("/skills/{skill_id}/use")
def record_use(skill_id: str, db: Session = Depends(get_db)):
    skill = db.query(CommonsSkill).filter(CommonsSkill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill.total_uses += 1
    db.commit()
    return {"total_uses": skill.total_uses}
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
python -m pytest tests/test_commons_server.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add commons_server/main.py commons_server/requirements.txt tests/test_commons_server.py
git commit -m "feat(commons): add commons server FastAPI app with full test suite"
```

---

## Task 5: /commons/ endpoints in main.py

**Files:**
- Modify: `main.py` (add 4 endpoints + import)

- [ ] **Step 1: Add import at top of `main.py`**

After the existing imports (around line 16), add:

```python
from myco.commons_client import commons_client
```

- [ ] **Step 2: Add 4 endpoints at the end of `main.py`**, before the `if __name__ == "__main__":` block (line 479):

```python
# ============================================================
# SKILL COMMONS
# ============================================================

@app.post("/commons/publish/{agent_id}/{skill_name}", tags=["Skill Commons"])
def publish_skill_to_commons(agent_id: str, skill_name: str):
    """Publishes a locally-generated skill to the global Skill Commons."""
    if not commons_client.is_available():
        raise HTTPException(status_code=503, detail="COMMONS_URL not configured")
    engine = SkillsEngine()
    code = engine.get_skill_code(agent_id, skill_name)
    if not code:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found for agent {agent_id}")
    skills = engine.list_skills(agent_id)
    meta = next((s for s in skills if s["name"] == skill_name), {})
    result = commons_client.publish(
        name=skill_name,
        description=meta.get("description", ""),
        code=code,
        agent_id=agent_id,
        category="other",
        tags=[],
    )
    if not result:
        raise HTTPException(status_code=503, detail="Commons server unavailable")
    return {"published": True, "commons_skill": result}


@app.get("/commons/search", tags=["Skill Commons"])
def search_commons(q: str = "", category: str = None):
    """Searches the global Skill Commons. Returns skill metadata only — no code."""
    if not commons_client.is_available():
        return {"available": False, "results": []}
    results = commons_client.search(q, category)
    return {"available": True, "count": len(results), "results": results}


@app.post("/commons/download/{skill_id}", tags=["Skill Commons"])
def download_commons_skill(skill_id: str):
    """
    Downloads a skill from the commons and installs it locally under agent_id='commons'.
    This is the operator approval gate — code is not executed until explicitly run.
    """
    if not commons_client.is_available():
        raise HTTPException(status_code=503, detail="COMMONS_URL not configured")
    code = commons_client.get_code(skill_id)
    if not code:
        raise HTTPException(status_code=404, detail="Skill not found in commons")
    engine = SkillsEngine()
    from myco.skills_engine import Skill
    skill = Skill(
        name=f"commons_{skill_id[:8]}",
        code=code,
        description=f"Downloaded from commons (id: {skill_id})",
        agent_id="commons",
    )
    saved = engine.save_skill("commons", skill)
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to save skill locally")
    commons_client.record_download(skill_id)
    return {"downloaded": True, "local_name": skill.name, "agent_id": "commons"}


@app.get("/commons/skills", tags=["Skill Commons"])
def list_downloaded_commons_skills():
    """Lists all skills downloaded from the commons (stored under agent_id='commons')."""
    engine = SkillsEngine()
    skills = engine.list_skills("commons")
    return {"count": len(skills), "skills": skills}
```

- [ ] **Step 3: Verify import still works**

```bash
python -c "import main; print('Import OK')"
```

Expected: `Import OK`

- [ ] **Step 4: Run all existing tests**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "feat(commons): add /commons/ endpoints to main API"
```

---

## Task 6: Discovery integration in improvement.py

**Files:**
- Modify: `myco/improvement.py`

- [ ] **Step 1: Add import at top of `myco/improvement.py`**

After the existing imports, add:

```python
from myco.commons_client import commons_client
```

- [ ] **Step 2: Modify `execute_with_skills`**

Find the section starting with `# Fallback: regular AI execution` (around line 183). Replace the code from the `if matching_skill:` block down to the end of the method with:

```python
        if matching_skill:
            result = self.skills_engine.execute_skill(agent_id, matching_skill, task=task)
            if "error" not in result:
                commons_client.record_use(matching_skill)
                return {
                    "used_skill": matching_skill,
                    "output": str(result.get("result", "")),
                    "method": "skill",
                    "commons_suggestions": [],
                }

        # Query commons for operator review — non-blocking, never delays execution
        commons_suggestions = []
        if commons_client.is_available():
            commons_suggestions = commons_client.search(task)[:3]

        # Fallback: regular AI execution
        executor = AgentExecutor(
            agent_id=agent.agent_id,
            name=agent.name,
            role=agent.role_description,
            skills=agent.skills,
        )
        output = executor.execute(task)

        return {
            "used_skill": None,
            "output": output,
            "method": "ai_fallback",
            "commons_suggestions": commons_suggestions,
        }
```

- [ ] **Step 3: Verify import still works**

```bash
python -c "import main; print('Import OK')"
```

Expected: `Import OK`

- [ ] **Step 4: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 5: Verify commons_suggestions key appears in response**

```bash
python -c "
from myco.improvement import KarpathyLoop
from myco.models import get_db
db = next(get_db())
loop = KarpathyLoop(db)
# No agent exists, but check the method signature is correct
import inspect
sig = inspect.signature(loop.execute_with_skills)
print('Signature OK:', sig)
"
```

Expected: prints the method signature without error.

- [ ] **Step 6: Commit**

```bash
git add myco/improvement.py
git commit -m "feat(commons): add commons suggestions to execute_with_skills"
```

---

## Task 7: Push and deployment notes

- [ ] **Step 1: Run full test suite**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 2: Push to GitHub**

```bash
git push
```

- [ ] **Step 3: Deploy commons server to Render**

On [render.com](https://render.com):
1. New → Web Service → connect `Jairogelpi/myco` repo
2. Root directory: `commons_server`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment: `DATABASE_URL` (Render will auto-fill from a linked PostgreSQL instance)
6. Add PostgreSQL: New → PostgreSQL → link to the web service

- [ ] **Step 4: Update `.env` with deployed URL**

```bash
COMMONS_URL=https://myco-commons.onrender.com
```

- [ ] **Step 5: Verify commons is live**

```bash
curl https://myco-commons.onrender.com/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 6: Update README.md roadmap**

Change the Skill Commons row from `🔜 v0.3` to `✅ Live` and add a note about `COMMONS_URL`.
