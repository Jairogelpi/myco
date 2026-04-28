import os
import json
from datetime import datetime
from openai import OpenAI
from myco.config import settings

# ------------------------------------------------------------------
# Initialize AI client: OpenRouter (preferred) → OpenAI (fallback) → None (mock)
# ------------------------------------------------------------------
client = None
MODEL = "mock"

if settings.OPENROUTER_API_KEY:
    client = OpenAI(
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": "https://myco.local",  # required by OpenRouter
            "X-Title": "Myco Organism OS",         # identifies your app
        }
    )
    MODEL = settings.OPENROUTER_MODEL
elif settings.OPENAI_API_KEY:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    MODEL = settings.OPENAI_MODEL


class AgentExecutor:
    """
    Executes work using OpenRouter/OpenAI API.
    Each agent has its own system prompt derived from its role.
    """
    
    def __init__(self, agent_id: str, name: str, role: str, skills: list = None):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.skills = skills or []
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        skills_str = ", ".join(self.skills) if self.skills else "general problem solving"
        return (
            f"You are {self.name} (ID: {self.agent_id}), a digital worker specialized in: {self.role}.\n"
            f"Your skills: {skills_str}.\n"
            f"You work autonomously. You deliver concise, high-quality output.\n"
            f"Always respond in a structured format. If the task requires code, include it.\n"
            f"If research, provide sources or reasoning. If writing, provide final copy."
        )
    
    def execute(self, task_description: str, context: str = "") -> str:
        """Sends task to AI API and returns the deliverable."""
        if not client:
            return f"[MOCK OUTPUT] Agent {self.agent_id} would execute: {task_description[:100]}..."
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"TASK: {task_description}\n\nCONTEXT: {context}"}
        ]
        
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            if not response or not response.choices:
                return f"[ERROR] Agent {self.agent_id}: empty response from API"
            return response.choices[0].message.content
        except Exception as e:
            err_msg = str(e)
            if "api_key" in err_msg.lower() or "auth" in err_msg.lower():
                return f"[ERROR] Agent {self.agent_id}: API key invalid or missing. Check OPENROUTER_API_KEY in .env"
            elif "rate" in err_msg.lower() or "quota" in err_msg.lower():
                return f"[ERROR] Agent {self.agent_id}: Rate limit or quota exceeded. Try a cheaper model."
            elif "NoneType" in err_msg:
                return f"[ERROR] Agent {self.agent_id}: API client not initialized. Check .env config and restart server."
            return f"[ERROR] Agent {self.agent_id} failed: {err_msg}"

def get_model_info() -> dict:
    """Returns current AI provider configuration."""
    if settings.OPENROUTER_API_KEY:
        return {"provider": "openrouter", "model": MODEL, "base_url": settings.OPENROUTER_BASE_URL}
    elif settings.OPENAI_API_KEY:
        return {"provider": "openai", "model": MODEL}
    return {"provider": "mock", "model": "none"}

def create_default_agents_for_charter(charter_mission: str) -> list:
    """
    Based on charter mission, suggests default agent roles.
    """
    mission = charter_mission.lower()
    agents = []
    
    if "newsletter" in mission or "content" in mission:
        agents = [
            {"name": "Researcher", "role": "Research and data collection", "skills": ["research", "scraping"]},
            {"name": "Writer", "role": "Content creation and copywriting", "skills": ["writing", "editing"]},
            {"name": "Distributor", "role": "Distribution and delivery", "skills": ["delivery", "analytics"]},
        ]
    elif "lead" in mission or "sales" in mission:
        agents = [
            {"name": "Prospector", "role": "Lead identification and scraping", "skills": ["scraping", "validation"]},
            {"name": "Outreach", "role": "Cold outreach and messaging", "skills": ["outreach", "copywriting"]},
            {"name": "Qualifier", "role": "Lead qualification and scoring", "skills": ["analysis", "scoring"]},
        ]
    else:
        agents = [
            {"name": "Analyst", "role": "Data analysis and insights", "skills": ["analysis", "research"]},
            {"name": "Executor", "role": "Task execution and delivery", "skills": ["execution", "delivery"]},
        ]
    
    return agents
