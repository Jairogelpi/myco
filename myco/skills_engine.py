import os
import json
import importlib.util
from datetime import datetime
from myco.config import settings

SKILLS_DIR = "./data/skills"

class Skill:
    """A skill is a reusable capability that an agent can learn."""
    
    def __init__(self, name: str, code: str, description: str, agent_id: str, 
                 success_rate: float = 0.0, uses: int = 0):
        self.name = name
        self.code = code
        self.description = description
        self.agent_id = agent_id
        self.success_rate = success_rate
        self.uses = uses
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "success_rate": self.success_rate,
            "uses": self.uses,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SkillsEngine:
    """
    Manages agent-generated skills. Each agent has its own skills/ directory.
    Skills are Python code snippets that the agent wrote to solve a problem better.
    """
    
    def __init__(self):
        os.makedirs(SKILLS_DIR, exist_ok=True)
    
    def _agent_skills_dir(self, agent_id: str) -> str:
        path = os.path.join(SKILLS_DIR, agent_id)
        os.makedirs(path, exist_ok=True)
        return path
    
    def _skill_path(self, agent_id: str, skill_name: str) -> str:
        return os.path.join(self._agent_skills_dir(agent_id), f"{skill_name}.py")
    
    def _manifest_path(self, agent_id: str) -> str:
        return os.path.join(self._agent_skills_dir(agent_id), "manifest.json")
    
    def list_skills(self, agent_id: str) -> list:
        """Returns all skills for an agent."""
        manifest_path = self._manifest_path(agent_id)
        if not os.path.exists(manifest_path):
            return []
        with open(manifest_path, "r") as f:
            return json.load(f)
    
    def get_skill_code(self, agent_id: str, skill_name: str) -> str:
        """Returns the Python code for a skill."""
        path = self._skill_path(agent_id, skill_name)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return f.read()
    
    def save_skill(self, agent_id: str, skill: Skill) -> bool:
        """Saves a skill: code to .py file, metadata to manifest."""
        try:
            # Save code
            code_path = self._skill_path(agent_id, skill.name)
            with open(code_path, "w") as f:
                f.write(skill.code)
            
            # Update manifest
            manifest = self.list_skills(agent_id)
            existing = next((s for s in manifest if s["name"] == skill.name), None)
            if existing:
                existing.update(skill.to_dict())
            else:
                manifest.append(skill.to_dict())
            
            with open(self._manifest_path(agent_id), "w") as f:
                json.dump(manifest, f, indent=2)
            
            return True
        except Exception as e:
            print(f"[SkillsEngine] Failed to save skill: {e}")
            return False
    
    def execute_skill(self, agent_id: str, skill_name: str, *args, **kwargs):
        """
        Dynamically loads and executes a skill's Python code.
        The skill module must have a `run(*args, **kwargs)` function.
        """
        code = self.get_skill_code(agent_id, skill_name)
        if not code:
            return {"error": f"Skill {skill_name} not found"}
        
        try:
            # Create a module from the skill code
            spec = importlib.util.spec_from_loader(
                f"skill_{skill_name}", 
                loader=None
            )
            module = importlib.util.module_from_spec(spec)
            exec(code, module.__dict__)
            
            if not hasattr(module, "run"):
                return {"error": f"Skill {skill_name} has no run() function"}
            
            result = module.run(*args, **kwargs)
            
            # Update usage stats
            manifest = self.list_skills(agent_id)
            for s in manifest:
                if s["name"] == skill_name:
                    s["uses"] = s.get("uses", 0) + 1
                    break
            with open(self._manifest_path(agent_id), "w") as f:
                json.dump(manifest, f, indent=2)
            
            return {"result": result, "skill": skill_name}
        except Exception as e:
            return {"error": f"Skill execution failed: {str(e)}"}
    
    def generate_skill_from_lesson(self, agent_id: str, agent_name: str, 
                                    task: str, failure: str, lesson: str,
                                    ai_client, model: str) -> Skill:
        """
        The Karpathy Loop: generates a new skill from a failure/lesson.
        Asks the AI to write a Python function that would have handled the task better.
        """
        prompt = f"""You are {agent_name} (ID: {agent_id}), an autonomous digital worker.

You attempted this task:
---
{task}
---

But you encountered this problem:
---
{failure}
---

Your lesson learned:
---
{lesson}
---

Write a reusable Python skill to handle this better next time.

RULES:
1. The code must define a `run(*args, **kwargs)` function
2. Keep it under 100 lines
3. Include a docstring explaining what it does
4. Make it reusable for similar tasks, not just this exact one
5. Only use standard library modules (no external deps unless essential)

Output ONLY valid Python code. No markdown, no explanation."""

        try:
            response = ai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a Python code generator. Output only valid Python code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            code = response.choices[0].message.content
            
            # Clean up code (remove markdown fences if present)
            code = code.replace("```python", "").replace("```", "").strip()
            
            # Generate skill name from task
            skill_name = f"skill_{task.lower()[:30].replace(' ', '_').replace(',', '').replace('.', '')}_{int(datetime.utcnow().timestamp())}"
            
            skill = Skill(
                name=skill_name,
                code=code,
                description=lesson,
                agent_id=agent_id
            )
            
            return skill
        except Exception as e:
            print(f"[KarpathyLoop] Failed to generate skill: {e}")
            return None
