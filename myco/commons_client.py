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

    def get_royalties(self, agent_id: str) -> Optional[dict]:
        if not self.is_available():
            return None
        try:
            r = httpx.get(f"{self.base_url}/royalties/{agent_id}", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def get_royalties_leaderboard(self) -> list:
        if not self.is_available():
            return []
        try:
            r = httpx.get(f"{self.base_url}/royalties", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return []


# Module-level singleton — import this in main.py and improvement.py
from myco.config import settings
commons_client = CommonsClient(settings.COMMONS_URL)
