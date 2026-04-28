from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from myco.config import settings

Base = declarative_base()
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Charter(Base):
    __tablename__ = "charters"
    id = Column(Integer, primary_key=True, index=True)
    mission = Column(Text, nullable=False)
    north_star = Column(String(50), default="revenue")
    seed_capital = Column(Float, default=500.0)
    max_monthly_burn = Column(Float, default=400.0)
    ethics = Column(JSON, default=list)
    status = Column(String(20), default="active")  # active, paused, dead
    stripe_funded = Column(Float, default=0.0)     # total USD funded via Stripe
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(16), unique=True, index=True)  # e.g., "agent_7a3f"
    name = Column(String(100))
    role_description = Column(Text)
    wallet = Column(Float, default=100.0)
    reputation = Column(Float, default=50.0)  # 0-100
    status = Column(String(20), default="idle")  # idle, working, dead
    charter_id = Column(Integer, ForeignKey("charters.id"))
    skills = Column(JSON, default=list)
    memory_summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    total_earned = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    usdc_balance = Column(Float, default=0.0)
    wallet_address = Column(String(100), nullable=True)  # future on-chain address

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(16), unique=True, index=True)
    publisher = Column(String(16), nullable=False)  # agent_id or "kernel"
    description = Column(Text, nullable=False)
    job_type = Column(String(50), default="task")  # task, need, service
    budget = Column(Float, default=0.0)
    deadline_hours = Column(Integer, default=24)
    status = Column(String(20), default="open")  # open, assigned, completed, failed
    assigned_to = Column(String(16), nullable=True)
    deliverable = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 post-completion
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    tx_id = Column(String(16), unique=True, index=True)
    from_agent = Column(String(16), nullable=False)
    to_agent = Column(String(16), nullable=False)
    amount = Column(Float, default=0.0)
    job_id = Column(String(16), nullable=True)
    tx_type = Column(String(20), default="payment")  # payment, tax, dividend, burn
    created_at = Column(DateTime, default=datetime.utcnow)

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    opp_id = Column(String(16), unique=True, index=True)
    description = Column(Text, nullable=False)
    gap_type = Column(String(50))  # skill_gap, capacity_gap, market_gap
    estimated_value = Column(Float, default=0.0)
    status = Column(String(20), default="open")  # open, claimed, discarded
    created_at = Column(DateTime, default=datetime.utcnow)

class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(String(16), unique=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    proposed_by = Column(String(16), nullable=False)  # agent_id
    status = Column(String(20), default="open")  # open, approved, rejected, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    closes_at = Column(DateTime, nullable=False)

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(String(16), nullable=False)
    agent_id = Column(String(16), nullable=False)
    choice = Column(String(4), nullable=False)  # "yes" or "no"
    weight = Column(Float, default=1.0)          # reputation_score at time of vote
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
