import yaml
import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from myco.models import Charter as CharterModel

def generate_id(prefix: str = "c", length: int = 8) -> str:
    return f"{prefix}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=length))}"

def load_charter_from_yaml(yaml_content: str) -> dict:
    """Parsea un charter YAML a diccionario Python."""
    data = yaml.safe_load(yaml_content)
    if not data or "charter" not in data:
        raise ValueError("YAML must contain a 'charter' root key")
    return data["charter"]

def create_charter_from_yaml(db: Session, yaml_content: str) -> CharterModel:
    """Crea un charter en la base de datos desde YAML."""
    data = load_charter_from_yaml(yaml_content)
    
    charter = CharterModel(
        id=random.randint(1000, 9999),
        mission=data.get("mission", ""),
        north_star=data.get("north_star", "revenue"),
        seed_capital=float(data.get("seed_capital", 500)),
        max_monthly_burn=float(data.get("max_monthly_burn", 400)),
        ethics=data.get("ethics", []),
        status="active"
    )
    db.add(charter)
    db.commit()
    db.refresh(charter)
    return charter

def get_active_charter(db: Session) -> CharterModel:
    return db.query(CharterModel).filter(CharterModel.status == "active").first()

# Example charter template
CHARTER_TEMPLATE = """
charter:
  mission: "Generate $10K/month selling competitive intelligence newsletters to retailers"
  north_star: "MRR"
  seed_capital: 500
  max_monthly_burn: 400
  ethics:
    - "No scraping sites with robots.txt prohibition"
    - "No generating spam"
    - "No spending more than 20% on compute without ROI justification"
"""
