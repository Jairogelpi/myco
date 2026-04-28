from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os

from myco.models import init_db, get_db, Agent, Job, Transaction, Opportunity, Charter
from myco.kernel import Kernel
from myco.charter import create_charter_from_yaml, get_active_charter, CHARTER_TEMPLATE
from myco.agent import AgentExecutor, create_default_agents_for_charter, get_model_info
from myco.autonomy import AutonomyEngine
from myco.improvement import KarpathyLoop
from myco.skills_engine import SkillsEngine
from myco.config import settings
from myco.commons_client import commons_client

app = FastAPI(title="Myco", description="The organism operating system for autonomous digital workers.")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/system/model", tags=["System"])
def get_system_model():
    """Returns current AI provider and model configuration."""
    return get_model_info()

# Initialize DB on startup
@app.on_event("startup")
def startup():
    init_db()

# ============================================================
# Pydantic schemas
# ============================================================

class CharterCreate(BaseModel):
    yaml_content: str

class AgentCreate(BaseModel):
    name: str
    role_description: str
    skills: Optional[List[str]] = []
    wallet: Optional[float] = None

class JobCreate(BaseModel):
    publisher: str
    description: str
    budget: float
    job_type: Optional[str] = "task"
    deadline_hours: Optional[int] = 24

class BidRequest(BaseModel):
    agent_id: str
    price: float

class CompleteRequest(BaseModel):
    deliverable: str
    rating: Optional[int] = 4

class ExecuteRequest(BaseModel):
    task: str
    context: Optional[str] = ""

class AutoPublishRequest(BaseModel):
    agent_id: str
    need_description: str
    budget: float

class AutoNeedRequest(BaseModel):
    agent_id: str
    task_description: str

class EvaluateRequest(BaseModel):
    agent_id: str
    task: str
    output: str
    feedback: Optional[str] = None
    rating: Optional[int] = None

class ExecuteWithSkillsRequest(BaseModel):
    agent_id: str
    task: str

# ============================================================
# CHARTER
# ============================================================

@app.post("/charter", tags=["Charter"])
def plant_charter(payload: CharterCreate, db: Session = Depends(get_db)):
    """Plant a new Charter. This is the seed of the organism."""
    charter = create_charter_from_yaml(db, payload.yaml_content)
    return {
        "message": "Charter planted successfully",
        "charter_id": charter.id,
        "mission": charter.mission,
        "seed_capital": charter.seed_capital
    }

@app.get("/charter", tags=["Charter"])
def get_current_charter(db: Session = Depends(get_db)):
    charter = get_active_charter(db)
    if not charter:
        raise HTTPException(status_code=404, detail="No active charter found")
    return charter

@app.get("/charter/template", tags=["Charter"])
def get_template():
    """Returns a default charter template."""
    return {"template": CHARTER_TEMPLATE}

# ============================================================
# ORGANISM
# ============================================================

@app.get("/organism", tags=["Organism"])
def get_organism_state(db: Session = Depends(get_db)):
    """Returns the full state of the organism."""
    kernel = Kernel(db)
    charter = get_active_charter(db)
    pnl = kernel.get_organism_pnl()
    agents = kernel.list_agents()
    open_jobs = kernel.get_open_jobs()
    opportunities = db.query(Opportunity).filter(Opportunity.status == "open").all()
    
    return {
        "charter": {
            "mission": charter.mission if charter else None,
            "north_star": charter.north_star if charter else None,
            "seed_capital": charter.seed_capital if charter else None,
            "status": charter.status if charter else "no_charter"
        },
        "financials": pnl,
        "agents": [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "wallet": round(a.wallet, 2),
                "reputation": a.reputation,
                "status": a.status,
                "skills": a.skills,
                "total_earned": round(a.total_earned, 2)
            }
            for a in agents
        ],
        "open_jobs": [
            {
                "job_id": j.job_id,
                "description": j.description,
                "budget": j.budget,
                "publisher": j.publisher
            }
            for j in open_jobs
        ],
        "open_opportunities": [
            {
                "opp_id": o.opp_id,
                "description": o.description,
                "gap_type": o.gap_type,
                "estimated_value": o.estimated_value
            }
            for o in opportunities
        ]
    }

# ============================================================
# AGENTS
# ============================================================

@app.post("/agents", tags=["Agents"])
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)):
    """Register a new digital worker in the organism."""
    charter = get_active_charter(db)
    kernel = Kernel(db)
    agent = kernel.register_agent(
        name=payload.name,
        role_description=payload.role_description,
        skills=payload.skills,
        wallet=payload.wallet,
        charter_id=charter.id if charter else None
    )
    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "wallet": agent.wallet,
        "status": agent.status,
        "message": f"Agent {agent.name} registered with wallet {agent.wallet} tokens"
    }

@app.get("/agents", tags=["Agents"])
def list_agents(status: Optional[str] = None, db: Session = Depends(get_db)):
    kernel = Kernel(db)
    return kernel.list_agents(status=status)

@app.get("/agents/{agent_id}", tags=["Agents"])
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    kernel = Kernel(db)
    agent = kernel.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    transactions = kernel.get_agent_transactions(agent_id)
    return {
        "agent": agent,
        "transactions": [
            {"tx_id": t.tx_id, "from": t.from_agent, "to": t.to_agent, 
             "amount": t.amount, "type": t.tx_type}
            for t in transactions
        ]
    }

@app.post("/agents/{agent_id}/execute", tags=["Agents"])
def execute_task(agent_id: str, payload: ExecuteRequest, db: Session = Depends(get_db)):
    """Execute a task using an agent's skills + OpenAI."""
    kernel = Kernel(db)
    agent = kernel.get_agent(agent_id)
    if not agent or agent.status == "dead":
        raise HTTPException(status_code=404, detail="Agent not available")
    
    executor = AgentExecutor(
        agent_id=agent.agent_id,
        name=agent.name,
        role=agent.role_description,
        skills=agent.skills
    )
    
    result = executor.execute(payload.task, payload.context)
    agent.last_heartbeat = datetime.utcnow()
    db.commit()
    
    return {"agent_id": agent_id, "task": payload.task, "output": result}

# ============================================================
# MARKETPLACE (JOBS)
# ============================================================

@app.post("/jobs", tags=["Marketplace"])
def publish_job(payload: JobCreate, db: Session = Depends(get_db)):
    """Publish a job to the internal marketplace."""
    kernel = Kernel(db)
    job = kernel.publish_job(
        publisher=payload.publisher,
        description=payload.description,
        budget=payload.budget,
        job_type=payload.job_type,
        deadline_hours=payload.deadline_hours
    )
    return {
        "job_id": job.job_id,
        "description": job.description,
        "budget": job.budget,
        "status": job.status
    }

@app.get("/jobs", tags=["Marketplace"])
def list_open_jobs(db: Session = Depends(get_db)):
    kernel = Kernel(db)
    return kernel.get_open_jobs()

@app.post("/jobs/{job_id}/bid", tags=["Marketplace"])
def bid_on_job(job_id: str, payload: BidRequest, db: Session = Depends(get_db)):
    """Bid on a job. Auto-assigns if price within budget."""
    kernel = Kernel(db)
    result = kernel.bid_on_job(job_id, payload.agent_id, payload.price)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/jobs/{job_id}/complete", tags=["Marketplace"])
def complete_job(job_id: str, payload: CompleteRequest, db: Session = Depends(get_db)):
    """Complete a job, transfer payment, collect tax."""
    kernel = Kernel(db)
    result = kernel.complete_job(job_id, payload.deliverable, payload.rating)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# ============================================================
# OPPORTUNITIES
# ============================================================

@app.post("/opportunities/scan", tags=["Opportunities"])
def scan_opportunities(db: Session = Depends(get_db)):
    """Kernel scans for gaps between charter and current capabilities."""
    kernel = Kernel(db)
    charter = get_active_charter(db)
    if not charter:
        raise HTTPException(status_code=400, detail="No active charter")
    
    opps = kernel.scan_opportunities(charter)
    
    # Auto-convert first opportunity to job if seed capital available
    jobs_created = []
    for opp in opps[:3]:  # Max 3 auto-jobs
        job = kernel.convert_opportunity_to_job(opp, budget=min(100, charter.seed_capital * 0.2))
        jobs_created.append({"opp_id": opp.opp_id, "job_id": job.job_id, "budget": job.budget})
    
    return {
        "opportunities_found": len(opps),
        "jobs_auto_created": jobs_created
    }

# ============================================================
# LEDGER
# ============================================================

@app.get("/ledger/pnl", tags=["Ledger"])
def get_pnl(db: Session = Depends(get_db)):
    """Profit & Loss of the organism."""
    kernel = Kernel(db)
    return kernel.get_organism_pnl()

# ============================================================
# AUTONOMY: Self-hiring, self-execution, self-completion
# ============================================================

@app.post("/autonomy/publish", tags=["Autonomy"])
def auto_publish_job(payload: AutoPublishRequest, db: Session = Depends(get_db)):
    """An agent publishes a job on the marketplace using its own wallet."""
    engine = AutonomyEngine(db)
    job = engine.auto_publish(payload.agent_id, payload.need_description, payload.budget)
    if not job:
        raise HTTPException(status_code=400, detail="Agent cannot publish (insufficient funds or invalid)")
    return {"published": True, "job_id": job.job_id, "publisher": payload.agent_id, "budget": payload.budget}

@app.post("/autonomy/bid/{job_id}", tags=["Autonomy"])
def auto_bid_job(job_id: str, db: Session = Depends(get_db)):
    """Finds capable idle agents and auto-bids on a job."""
    engine = AutonomyEngine(db)
    result = engine.auto_bid(job_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/autonomy/execute/{job_id}", tags=["Autonomy"])
def auto_execute_job(job_id: str, db: Session = Depends(get_db)):
    """Auto-executes an assigned job using AI."""
    engine = AutonomyEngine(db)
    result = engine.auto_execute(job_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/autonomy/complete/{job_id}", tags=["Autonomy"])
def auto_complete_job(job_id: str, db: Session = Depends(get_db)):
    """Auto-completes a job (execute + complete with payment)."""
    engine = AutonomyEngine(db)
    result = engine.auto_complete(job_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/autonomy/cycle", tags=["Autonomy"])
def run_autonomy_cycle(db: Session = Depends(get_db)):
    """
    Runs one full autonomy cycle:
    auto-bid on open jobs, auto-execute, auto-complete.
    This is the heartbeat of self-governance.
    """
    engine = AutonomyEngine(db)
    results = engine.run_cycle()
    return {"cycle_completed": True, **results}

@app.post("/autonomy/detect", tags=["Autonomy"])
def agent_detects_need(payload: AutoNeedRequest, db: Session = Depends(get_db)):
    """
    Simulates an agent detecting it needs help with a task.
    Parses task for missing skills and auto-publishes a job.
    """
    engine = AutonomyEngine(db)
    job = engine.agent_detects_need(payload.agent_id, payload.task_description)
    if not job:
        return {"detected": False, "message": "No skill gaps detected or insufficient funds"}
    return {"detected": True, "job_id": job.job_id, "publisher": payload.agent_id, 
            "description": job.description, "budget": job.budget}

# ============================================================
# KARPATHY LOOP: Self-Improvement
# ============================================================

@app.post("/improvement/evaluate", tags=["Karpathy Loop"])
def evaluate_and_improve(payload: EvaluateRequest, db: Session = Depends(get_db)):
    """
    The Karpathy Loop: evaluates a task output and triggers self-improvement.
    If the output was poor, the agent generates a lesson and writes a new skill.
    """
    loop = KarpathyLoop(db)
    result = loop.evaluate_and_improve(
        agent_id=payload.agent_id,
        task=payload.task,
        output=payload.output,
        feedback=payload.feedback,
        rating=payload.rating
    )
    return result

@app.post("/improvement/execute-with-skills", tags=["Karpathy Loop"])
def execute_with_skills(payload: ExecuteWithSkillsRequest, db: Session = Depends(get_db)):
    """
    Executes a task using existing skills first, falling back to AI.
    """
    loop = KarpathyLoop(db)
    result = loop.execute_with_skills(payload.agent_id, payload.task)
    return result

@app.get("/improvement/skills/{agent_id}", tags=["Karpathy Loop"])
def list_agent_skills(agent_id: str):
    """Returns all learned skills for an agent."""
    engine = SkillsEngine()
    skills = engine.list_skills(agent_id)
    return {"agent_id": agent_id, "skills_count": len(skills), "skills": skills}

@app.get("/improvement/skill-code/{agent_id}/{skill_name}", tags=["Karpathy Loop"])
def get_skill_code(agent_id: str, skill_name: str):
    """Returns the Python code for a specific skill."""
    engine = SkillsEngine()
    code = engine.get_skill_code(agent_id, skill_name)
    if not code:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"agent_id": agent_id, "skill_name": skill_name, "code": code}

# ============================================================
# SEED / AUTO-SETUP
# ============================================================

@app.post("/seed", tags=["Setup"])
def seed_organism(db: Session = Depends(get_db)):
    """
    One-click setup: plants default charter + creates initial agents.
    This is the 'nuclear option' to get started in 10 seconds.
    """
    kernel = Kernel(db)
    
    # Check if charter exists
    existing = get_active_charter(db)
    if existing:
        return {"message": "Organism already seeded", "charter_id": existing.id}
    
    # Plant charter
    charter = create_charter_from_yaml(db, CHARTER_TEMPLATE)
    
    # Create default agents based on charter
    agent_specs = create_default_agents_for_charter(charter.mission)
    created = []
    for spec in agent_specs:
        agent = kernel.register_agent(
            name=spec["name"],
            role_description=spec["role"],
            skills=spec["skills"],
            wallet=settings.AGENT_BUDGET_DEFAULT,
            charter_id=charter.id
        )
        created.append({"agent_id": agent.agent_id, "name": agent.name, "skills": agent.skills})
    
    # Initial opportunity scan
    opps = kernel.scan_opportunities(charter)
    jobs = []
    for opp in opps[:3]:
        job = kernel.convert_opportunity_to_job(opp, budget=50.0)
        jobs.append({"job_id": job.job_id, "description": job.description})
    
    return {
        "message": "Organism seeded successfully",
        "charter_id": charter.id,
        "mission": charter.mission,
        "agents_created": created,
        "initial_jobs": jobs,
        "next_steps": [
            "GET /organism to see full state",
            "POST /opportunities/scan to refresh gaps",
            "POST /jobs/{id}/bid to assign work",
            "POST /jobs/{id}/complete to close loops"
        ]
    }

from datetime import datetime

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
    from myco.skills_engine import Skill
    skill_engine = SkillsEngine()
    skill = Skill(
        name=f"commons_{skill_id[:8]}",
        code=code,
        description=f"Downloaded from commons (id: {skill_id})",
        agent_id="commons",
    )
    saved = skill_engine.save_skill("commons", skill)
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to save skill locally")
    commons_client.record_download(skill_id)
    return {"downloaded": True, "local_name": skill.name, "agent_id": "commons"}


@app.get("/commons/skills", tags=["Skill Commons"])
def list_downloaded_commons_skills():
    """Lists all skills downloaded from the commons (stored under agent_id='commons')."""
    skill_engine = SkillsEngine()
    skills = skill_engine.list_skills("commons")
    return {"count": len(skills), "skills": skills}


@app.get("/commons/royalties/{agent_id}", tags=["Skill Commons"])
def get_agent_royalties(agent_id: str):
    """Returns accumulated royalty credits for an agent in the commons."""
    result = commons_client.get_royalties(agent_id)
    if result is None:
        return {"agent_id": agent_id, "credits": 0.0, "updated_at": None, "commons_available": False}
    return result


@app.get("/commons/royalties", tags=["Skill Commons"])
def royalties_leaderboard():
    """Returns the top 20 agents by royalty credits earned in the commons."""
    return commons_client.get_royalties_leaderboard()


@app.get("/commons/reputation/{agent_id}", tags=["Skill Commons"])
def get_agent_reputation(agent_id: str):
    """Returns Proof-of-Agent-Work reputation profile for an agent."""
    result = commons_client.get_reputation(agent_id)
    if result is None:
        return {"agent_id": agent_id, "reputation_score": 0, "commons_available": False}
    return result


@app.get("/commons/reputation", tags=["Skill Commons"])
def reputation_leaderboard():
    """Returns the top 20 agents by reputation score (PoAW leaderboard)."""
    return commons_client.get_reputation_leaderboard()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
