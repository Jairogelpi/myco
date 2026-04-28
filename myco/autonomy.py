import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from myco.models import Agent, Job, Charter
from myco.kernel import Kernel
from myco.agent import AgentExecutor
from myco.config import settings

class AutonomyEngine:
    """
    The autonomy engine enables agents to self-hire, self-assign, and self-complete.
    This is the core differentiator of Myco: agents are economic units, not managed workers.
    """

    def __init__(self, db: Session):
        self.db = db
        self.kernel = Kernel(db)

    @staticmethod
    def _generate_id(prefix: str, length: int = 8) -> str:
        return f"{prefix}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=length))}"

    def auto_publish(self, agent_id: str, need_description: str, budget: float, 
                     min_reputation: float = 40) -> Job:
        """
        An agent publishes a job on the marketplace using its own wallet.
        This is the core of self-hiring: 'I need X, I'll pay for it.'
        """
        agent = self.kernel.get_agent(agent_id)
        if not agent or agent.status == "dead":
            return None
        
        # Check if agent can afford it
        if agent.wallet < budget:
            return None
        
        # Reserve budget (deduct now, restore if job fails)
        agent.wallet -= budget
        agent.total_spent += budget
        
        job = Job(
            job_id=self._generate_id("job"),
            publisher=agent_id,  # Agent is the publisher, not kernel
            description=need_description,
            job_type="need",
            budget=budget,
            status="open"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def auto_bid(self, job_id: str, max_bidders: int = 3) -> dict:
        """
        Finds capable idle agents and auto-bids on a job.
        Picks the best bid based on skill match + reputation / price ratio.
        """
        job = self.db.query(Job).filter(Job.job_id == job_id).first()
        if not job or job.status != "open":
            return {"error": "Job not available"}
        
        # Find idle agents with matching skills
        idle_agents = self.db.query(Agent).filter(
            Agent.status == "idle",
            Agent.wallet > 0,
            Agent.status != "dead"
        ).all()
        
        if not idle_agents:
            return {"error": "No idle agents available"}
        
        # Score agents based on skill match and reputation
        scored = []
        for agent in idle_agents:
            # Skip if agent is the publisher (can't bid on own job)
            if agent.agent_id == job.publisher:
                continue
            
            # Calculate skill relevance score
            job_desc_lower = job.description.lower()
            skill_match = sum(1 for s in (agent.skills or []) if s.lower() in job_desc_lower)
            
            # Price: bid between 60-95% of budget based on reputation
            reputation_factor = agent.reputation / 100
            bid_price = job.budget * (0.6 + (1 - reputation_factor) * 0.35)
            bid_price = min(bid_price, job.budget)
            
            score = (skill_match * 10 + agent.reputation) / max(bid_price, 1)
            scored.append({"agent": agent, "price": bid_price, "score": score, "skill_match": skill_match})
        
        if not scored:
            return {"error": "No suitable agents found"}
        
        # Pick best bidder
        best = max(scored, key=lambda x: x["score"])
        result = self.kernel.bid_on_job(job_id, best["agent"].agent_id, best["price"])
        result["skill_match"] = best["skill_match"]
        result["bid_price"] = best["price"]
        return result

    def auto_execute(self, job_id: str) -> dict:
        """
        Auto-executes a job using the assigned agent's skills + AI.
        Returns the deliverable.
        """
        job = self.db.query(Job).filter(Job.job_id == job_id).first()
        if not job or job.status != "assigned":
            return {"error": "Job not assigned"}
        
        agent = self.kernel.get_agent(job.assigned_to)
        if not agent:
            return {"error": "Agent not found"}
        
        executor = AgentExecutor(
            agent_id=agent.agent_id,
            name=agent.name,
            role=agent.role_description,
            skills=agent.skills
        )
        
        result = executor.execute(job.description)
        return {
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "deliverable": result,
            "job_id": job_id
        }

    def auto_complete(self, job_id: str) -> dict:
        """
        Auto-completes a job with the deliverable from execution.
        """
        execution = self.auto_execute(job_id)
        if "error" in execution:
            return execution
        
        return self.kernel.complete_job(
            job_id=job_id,
            deliverable=execution["deliverable"],
            rating=4  # Default good rating for auto-completed jobs
        )

    def run_cycle(self) -> dict:
        """
        Runs one full autonomy cycle:
        1. Scan for open jobs
        2. Auto-bid on each
        3. Auto-execute assigned jobs
        4. Auto-complete them
        Returns summary of actions taken.
        """
        results = {
            "jobs_bid": 0,
            "jobs_executed": 0,
            "jobs_completed": 0,
            "errors": []
        }
        
        # Find open jobs
        open_jobs = self.kernel.get_open_jobs()
        
        for job in open_jobs:
            # Step 1: Auto-bid
            bid_result = self.auto_bid(job.job_id)
            if bid_result.get("assigned"):
                results["jobs_bid"] += 1
                
                # Step 2 & 3: Auto-execute and complete
                complete_result = self.auto_complete(job.job_id)
                if complete_result.get("completed"):
                    results["jobs_executed"] += 1
                    results["jobs_completed"] += 1
                elif "error" in complete_result:
                    results["errors"].append(f"Job {job.job_id}: {complete_result['error']}")
            elif "error" in bid_result:
                results["errors"].append(f"Job {job.job_id}: {bid_result['error']}")
        
        return results

    def agent_detects_need(self, agent_id: str, task_description: str) -> Job:
        """
        Simulates an agent detecting that it needs help.
        Parses the task to identify missing skills and publishes a job.
        Returns the published job or None.
        """
        agent = self.kernel.get_agent(agent_id)
        if not agent:
            return None
        
        # Simple heuristic: check if task keywords match agent skills
        task_lower = task_description.lower()
        agent_skills = [s.lower() for s in (agent.skills or [])]
        
        # Common skill gaps
        skill_keywords = {
            "delivery": ["email", "send", "distribute", "deliver", "newsletter", "subscriber"],
            "writing": ["write", "draft", "copy", "content", "newsletter", "report"],
            "research": ["research", "analyze", "data", "find", "scrape", "investigate"],
            "scraping": ["scrape", "extract", "crawl", "data collection"],
            "analytics": ["metric", "analytics", "track", "measure", "kpi"],
        }
        
        missing_skills = []
        for skill, keywords in skill_keywords.items():
            if skill not in agent_skills:
                if any(kw in task_lower for kw in keywords):
                    missing_skills.append(skill)
        
        if not missing_skills:
            return None
        
        # Publish job for the first missing skill
        skill = missing_skills[0]
        budget = min(50, agent.wallet * 0.3)  # Max 30% of wallet or $50
        
        if budget <= 0:
            return None
        
        description = f"Auto-detected need: {skill} capability required for task: {task_description[:80]}"
        
        return self.auto_publish(agent_id, description, budget)
