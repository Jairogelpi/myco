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
