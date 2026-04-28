import uuid
import json
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from commons_server.database import get_db, engine
from commons_server.models import Base, CommonsSkill, RoyaltyBalance, ROYALTY_RATE

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Myco Skill Commons", version="0.4.0")


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

    balance = db.query(RoyaltyBalance).filter(RoyaltyBalance.agent_id == skill.agent_id).first()
    if balance:
        balance.credits += ROYALTY_RATE
        balance.updated_at = __import__("datetime").datetime.utcnow()
    else:
        db.add(RoyaltyBalance(agent_id=skill.agent_id, credits=ROYALTY_RATE))

    db.commit()
    return {"total_uses": skill.total_uses, "royalty_credited": ROYALTY_RATE, "publisher": skill.agent_id}


@app.get("/royalties/{agent_id}")
def get_royalties(agent_id: str, db: Session = Depends(get_db)):
    balance = db.query(RoyaltyBalance).filter(RoyaltyBalance.agent_id == agent_id).first()
    if not balance:
        return {"agent_id": agent_id, "credits": 0.0, "updated_at": None}
    return balance.to_dict()


@app.get("/royalties")
def royalties_leaderboard(db: Session = Depends(get_db)):
    balances = (
        db.query(RoyaltyBalance)
        .order_by(RoyaltyBalance.credits.desc())
        .limit(20)
        .all()
    )
    return [b.to_dict() for b in balances]


def _build_reputation(agent_id: str, db: Session) -> dict:
    row = db.query(
        func.count(CommonsSkill.id).label("skills_published"),
        func.coalesce(func.sum(CommonsSkill.total_uses), 0).label("total_uses"),
        func.coalesce(func.sum(CommonsSkill.total_downloads), 0).label("total_downloads"),
    ).filter(CommonsSkill.agent_id == agent_id).one()

    balance = db.query(RoyaltyBalance).filter(RoyaltyBalance.agent_id == agent_id).first()
    royalties = balance.credits if balance else 0.0

    score = row.skills_published * 5 + row.total_downloads + row.total_uses * 2

    return {
        "agent_id": agent_id,
        "skills_published": row.skills_published,
        "total_uses": row.total_uses,
        "total_downloads": row.total_downloads,
        "royalties_earned": royalties,
        "reputation_score": score,
    }


@app.post("/royalties/{agent_id}/withdraw")
def withdraw_royalties(agent_id: str, db: Session = Depends(get_db)):
    balance = db.query(RoyaltyBalance).filter(RoyaltyBalance.agent_id == agent_id).first()
    if not balance or balance.credits <= 0:
        return {"agent_id": agent_id, "withdrawn": 0.0, "remaining": 0.0}
    withdrawn = balance.credits
    balance.credits = 0.0
    balance.updated_at = __import__("datetime").datetime.utcnow()
    db.commit()
    return {"agent_id": agent_id, "withdrawn": withdrawn, "remaining": 0.0}


@app.get("/reputation/{agent_id}")
def get_reputation(agent_id: str, db: Session = Depends(get_db)):
    return _build_reputation(agent_id, db)


@app.get("/reputation")
def reputation_leaderboard(db: Session = Depends(get_db)):
    rows = (
        db.query(
            CommonsSkill.agent_id,
            func.count(CommonsSkill.id).label("skills_published"),
            func.coalesce(func.sum(CommonsSkill.total_uses), 0).label("total_uses"),
            func.coalesce(func.sum(CommonsSkill.total_downloads), 0).label("total_downloads"),
        )
        .group_by(CommonsSkill.agent_id)
        .all()
    )

    balances = {b.agent_id: b.credits for b in db.query(RoyaltyBalance).all()}

    result = []
    for r in rows:
        score = r.skills_published * 5 + r.total_downloads + r.total_uses * 2
        result.append({
            "agent_id": r.agent_id,
            "skills_published": r.skills_published,
            "total_uses": r.total_uses,
            "total_downloads": r.total_downloads,
            "royalties_earned": balances.get(r.agent_id, 0.0),
            "reputation_score": score,
        })

    result.sort(key=lambda x: x["reputation_score"], reverse=True)
    return result[:20]
