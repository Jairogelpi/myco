import random
import string
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from myco.models import Agent, Job, Transaction, Opportunity, Charter
from myco.config import settings
from myco.tax import TaxResolver

class Kernel:
    """
    The Kernel is the soil of Myco.
    It maintains: Registry, Ledger, Opportunity Scanner.
    It does NOT command. It detects gaps and publishes Jobs.
    It adjudicates based on reputation/price ratio.
    It collects 15% tax on every transaction.
    """

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _generate_id(prefix: str, length: int = 8) -> str:
        return f"{prefix}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=length))}"

    # ============================================================
    # REGISTRY: Agent lifecycle
    # ============================================================

    def register_agent(self, name: str, role_description: str, skills: list = None, 
                       wallet: float = None, charter_id: int = None) -> Agent:
        """Registers a new agent in the organism."""
        agent = Agent(
            agent_id=self._generate_id("agent"),
            name=name,
            role_description=role_description,
            wallet=wallet or settings.AGENT_BUDGET_DEFAULT,
            status="idle",
            charter_id=charter_id,
            skills=skills or [],
            total_earned=0.0,
            total_spent=0.0
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def get_agent(self, agent_id: str) -> Agent:
        return self.db.query(Agent).filter(Agent.agent_id == agent_id).first()

    def list_agents(self, status: str = None):
        query = self.db.query(Agent)
        if status:
            query = query.filter(Agent.status == status)
        return query.all()

    def kill_bankrupt_agents(self):
        """Agents with wallet <= 0 and no job assignment for 72h are marked dead."""
        cutoff = datetime.utcnow() - timedelta(hours=settings.AGENT_LIFESPAN_HOURS)
        victims = self.db.query(Agent).filter(
            Agent.wallet <= 0,
            Agent.last_heartbeat < cutoff,
            Agent.status != "dead"
        ).all()
        for agent in victims:
            agent.status = "dead"
        self.db.commit()
        return len(victims)

    # ============================================================
    # OPPORTUNITY SCANNER
    # ============================================================

    def scan_opportunities(self, charter: Charter) -> list:
        """
        Analyzes the charter vs current agent capabilities.
        Publishes Opportunities where gaps exist.
        """
        opportunities = []
        active_agents = self.list_agents(status="idle") + self.list_agents(status="working")
        
        if not active_agents:
            # No agents at all = biggest gap
            opp = Opportunity(
                opp_id=self._generate_id("opp"),
                description=f"No agents deployed for mission: {charter.mission[:100]}",
                gap_type="skill_gap",
                estimated_value=charter.seed_capital * 0.2
            )
            self.db.add(opp)
            opportunities.append(opp)
        
        # Check if we have diversity of skills
        all_skills = set()
        for a in active_agents:
            all_skills.update(a.skills or [])
        
        mission_lower = charter.mission.lower()
        required_skills = []
        if "newsletter" in mission_lower or "content" in mission_lower:
            required_skills = ["research", "writing", "delivery"]
        elif "lead" in mission_lower:
            required_skills = ["scraping", "outreach", "validation"]
        elif "data" in mission_lower:
            required_skills = ["collection", "analysis", "visualization"]
        else:
            required_skills = ["generalist"]
        
        for skill in required_skills:
            if skill not in all_skills:
                opp = Opportunity(
                    opp_id=self._generate_id("opp"),
                    description=f"Missing skill: {skill} needed for mission execution",
                    gap_type="skill_gap",
                    estimated_value=50.0
                )
                self.db.add(opp)
                opportunities.append(opp)
        
        self.db.commit()
        return opportunities

    def convert_opportunity_to_job(self, opp: Opportunity, budget: float = 100.0) -> Job:
        """Converts an Opportunity into a funded Job on the marketplace."""
        job = Job(
            job_id=self._generate_id("job"),
            publisher="kernel",
            description=opp.description,
            job_type="need",
            budget=budget,
            status="open"
        )
        opp.status = "claimed"
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    # ============================================================
    # MARKETPLACE: Job Board + Matching
    # ============================================================

    def publish_job(self, publisher: str, description: str, budget: float,
                    job_type: str = "task", category: str = None, deadline_hours: int = 24) -> Job:
        """Publishes a Job to the internal marketplace."""
        job = Job(
            job_id=self._generate_id("job"),
            publisher=publisher,
            description=description,
            job_type=job_type,
            category=category,
            budget=budget,
            deadline_hours=deadline_hours,
            status="open"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_open_jobs(self):
        return self.db.query(Job).filter(Job.status == "open").all()

    def bid_on_job(self, job_id: str, agent_id: str, price: float) -> dict:
        """
        Matching: picks best bid based on reputation/price ratio.
        For MVP: auto-assigns if only one bid, or picks best ratio.
        """
        job = self.db.query(Job).filter(Job.job_id == job_id).first()
        if not job or job.status != "open":
            return {"error": "Job not available"}
        
        agent = self.get_agent(agent_id)
        if not agent or agent.status == "dead":
            return {"error": "Agent not valid"}
        
        # Check if agent can afford to do the work (opportunity cost)
        if agent.wallet < 0:
            return {"error": "Agent bankrupt"}
        
        # Simple matching: assign to bidder if price within budget
        if price <= job.budget:
            job.assigned_to = agent_id
            job.status = "assigned"
            agent.status = "working"
            self.db.commit()
            return {"assigned": True, "job_id": job_id, "agent": agent_id, "price": price}
        
        return {"assigned": False, "reason": "Bid too high"}

    def complete_job(self, job_id: str, deliverable: str, rating: int = None) -> dict:
        """
        Completes a job: transfers payment, deducts tax, updates reputations.
        """
        job = self.db.query(Job).filter(Job.job_id == job_id).first()
        if not job or job.status != "assigned":
            return {"error": "Job not in assigned state"}
        
        worker = self.get_agent(job.assigned_to)
        if not worker:
            return {"error": "Worker not found"}
        
        # Payment calculation
        payment = job.budget
        resolver = TaxResolver(self.db)
        tax_rate, tax_reason = resolver.resolve(job_id, worker.agent_id, job.category)
        tax = payment * tax_rate
        net_payment = payment - tax
        
        # Update worker wallet
        worker.wallet += net_payment
        worker.total_earned += net_payment
        worker.status = "idle"
        worker.last_heartbeat = datetime.utcnow()
        
        # Update job
        job.status = "completed"
        job.deliverable = deliverable
        job.rating = rating or 4
        job.completed_at = datetime.utcnow()
        
        # Create transaction: publisher -> worker
        self._create_transaction(job.publisher, worker.agent_id, net_payment, job_id, "payment")
        # Create transaction: tax to kernel
        self._create_transaction(worker.agent_id, "kernel", tax, job_id, "tax")
        
        # Reputation update based on rating
        if job.rating >= 4:
            worker.reputation = min(100, worker.reputation + 2)
        elif job.rating <= 2:
            worker.reputation = max(0, worker.reputation - 5)
        
        self.db.commit()
        return {
            "completed": True,
            "job_id": job_id,
            "worker": worker.agent_id,
            "payment": net_payment,
            "tax": tax,
            "tax_rate": tax_rate,
            "tax_reason": tax_reason,
            "reputation": worker.reputation
        }

    def _create_transaction(self, from_agent: str, to_agent: str, amount: float, 
                            job_id: str, tx_type: str = "payment"):
        tx = Transaction(
            tx_id=self._generate_id("tx"),
            from_agent=from_agent,
            to_agent=to_agent,
            amount=amount,
            job_id=job_id,
            tx_type=tx_type
        )
        self.db.add(tx)

    # ============================================================
    # LEDGER: Financial state of the organism
    # ============================================================

    def get_organism_pnl(self) -> dict:
        """Returns P&L of the entire organism."""
        total_in = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.to_agent == "kernel"
        ).scalar() or 0.0
        
        total_out = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.from_agent == "kernel"
        ).scalar() or 0.0
        
        agent_wealth = self.db.query(func.sum(Agent.wallet)).filter(
            Agent.status != "dead"
        ).scalar() or 0.0
        
        active_agents = self.db.query(Agent).filter(Agent.status != "dead").count()
        dead_agents = self.db.query(Agent).filter(Agent.status == "dead").count()
        completed_jobs = self.db.query(Job).filter(Job.status == "completed").count()
        
        return {
            "total_tax_collected": round(total_in, 2),
            "total_distributed": round(total_out, 2),
            "agent_wealth_total": round(agent_wealth, 2),
            "active_agents": active_agents,
            "dead_agents": dead_agents,
            "completed_jobs": completed_jobs
        }

    def get_agent_transactions(self, agent_id: str):
        return self.db.query(Transaction).filter(
            (Transaction.from_agent == agent_id) | (Transaction.to_agent == agent_id)
        ).order_by(Transaction.created_at.desc()).all()
