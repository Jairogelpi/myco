import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
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


ROYALTY_RATE = 1.0  # credits per use


class RoyaltyBalance(Base):
    __tablename__ = "royalty_balances"

    agent_id = Column(String, primary_key=True)
    credits = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "credits": self.credits,
            "updated_at": self.updated_at.isoformat(),
        }
