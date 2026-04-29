from sqlalchemy.orm import Session
from myco.models import TaxRule
from myco.config import settings


class TaxResolver:
    """Resolves tax rate based on hierarchical rules.

    Precedence (highest to lowest):
    1. Job-specific rule
    2. Agent-specific rule
    3. Category rule
    4. Global rule in DB
    5. KERNEL_TAX_RATE config default
    """

    def __init__(self, db: Session):
        self.db = db

    def resolve(self, job_id: str = None, agent_id: str = None, category: str = None) -> tuple[float, str]:
        """Resolve tax rate and return (rate, reason).

        Args:
            job_id: The specific job ID
            agent_id: The agent executing the job
            category: The job category

        Returns:
            (tax_rate: float, reason: str)
        """
        # 1. Job-specific rule (highest priority)
        if job_id:
            rule = self.db.query(TaxRule).filter_by(
                rule_type="job",
                target_id=job_id
            ).first()
            if rule:
                return rule.tax_rate, f"job:{job_id}"

        # 2. Agent-specific rule
        if agent_id:
            rule = self.db.query(TaxRule).filter_by(
                rule_type="agent",
                target_id=agent_id
            ).first()
            if rule:
                return rule.tax_rate, f"agent:{agent_id}"

        # 3. Category rule
        if category:
            rule = self.db.query(TaxRule).filter_by(
                rule_type="category",
                target_id=category
            ).first()
            if rule:
                return rule.tax_rate, f"category:{category}"

        # 4. Global rule in DB
        rule = self.db.query(TaxRule).filter_by(
            rule_type="global",
            target_id=None
        ).first()
        if rule:
            return rule.tax_rate, "global_rule"

        # 5. Config default
        return settings.KERNEL_TAX_RATE, "default"
