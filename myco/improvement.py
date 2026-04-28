from datetime import datetime
from myco.skills_engine import SkillsEngine, Skill
from myco.agent import AgentExecutor, client, MODEL
from myco.models import Agent as AgentModel
from myco.kernel import Kernel

class KarpathyLoop:
    """
    The self-improvement engine:
    1. Agent executes a task
    2. Result is evaluated (human feedback or self-evaluation)
    3. If result is poor, the loop triggers:
       a. Analyze what went wrong
       b. Generate a lesson learned
       c. Write a new skill (Python code) to handle it better
       d. Save the skill for future use
    4. Next similar task uses the skill directly
    """

    def __init__(self, db):
        self.db = db
        self.skills_engine = SkillsEngine()
        self.kernel = Kernel(db)

    def evaluate_and_improve(self, agent_id: str, task: str, output: str, 
                             feedback: str = None, rating: int = None) -> dict:
        """
        Evaluates a task output and triggers improvement if needed.
        Returns result of improvement cycle or 'no_improvement_needed'.
        """
        agent = self.kernel.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        # Determine if improvement is needed
        needs_improvement = False
        trigger_reason = ""
        
        if feedback and any(word in feedback.lower() for word in 
                          ["bad", "poor", "wrong", "incorrect", "incomplete", 
                           "terrible", "awful", "no", "fix", "improve"]):
            needs_improvement = True
            trigger_reason = "explicit_negative_feedback"
        elif rating and rating <= 2:
            needs_improvement = True
            trigger_reason = f"low_rating_{rating}"
        elif len(output) < 50:
            needs_improvement = True
            trigger_reason = "output_too_short"
        elif "error" in output.lower() or "failed" in output.lower():
            needs_improvement = True
            trigger_reason = "execution_error"
        
        if not needs_improvement:
            return {"improved": False, "reason": "no_improvement_triggered"}
        
        # Step 1: Generate lesson learned via AI
        lesson = self._generate_lesson(agent, task, output, feedback)
        if not lesson:
            return {"improved": False, "reason": "lesson_generation_failed"}
        
        # Step 2: Generate skill from lesson (Karpathy Loop core)
        skill = self.skills_engine.generate_skill_from_lesson(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            task=task,
            failure=output[:200],
            lesson=lesson,
            ai_client=client,
            model=MODEL
        )
        
        if not skill:
            return {"improved": False, "reason": "skill_generation_failed", "lesson": lesson}
        
        # Step 3: Save the skill
        saved = self.skills_engine.save_skill(agent.agent_id, skill)
        if not saved:
            return {"improved": False, "reason": "skill_save_failed"}
        
        # Step 4: Update agent metadata
        current_skills = agent.skills or []
        skill_tag = skill.name.replace(f"skill_", "").split("_")[0]
        if skill_tag not in current_skills:
            current_skills.append(skill_tag)
            agent.skills = current_skills
        
        agent.memory_summary = (agent.memory_summary or "") + f"\n[{datetime.utcnow().isoformat()}] Learned: {lesson}"
        self.db.commit()
        
        return {
            "improved": True,
            "trigger": trigger_reason,
            "lesson": lesson,
            "skill_name": skill.name,
            "skill_code_preview": skill.code[:200] + "..." if len(skill.code) > 200 else skill.code
        }
    
    def _generate_lesson(self, agent, task: str, output: str, feedback: str = None) -> str:
        """Asks the AI to articulate what went wrong and how to fix it."""
        if not client:
            return None
        
        # Neutral prompt - avoids content filtering on critical reflection
        feedback_text = feedback if feedback else "The output did not meet requirements."
        
        prompt = f"""Task: {task}

Produced output: {output[:300]}

Feedback: {feedback_text}

As the worker who did this task, write ONE sentence explaining what approach or tool would produce a better result next time. Focus on technique, not self-criticism. Be specific."""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": f"You are {agent.name}. You reflect on work to improve technique."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            if not response or not response.choices:
                print(f"[KarpathyLoop] API returned empty choices")
                return None
            
            msg = response.choices[0].message
            if not msg:
                print(f"[KarpathyLoop] API returned empty message")
                return None
            
            content = msg.content
            if not content:
                print(f"[KarpathyLoop] API returned None content")
                return None
            
            lesson = content.strip()
            if not lesson:
                return None
            
            print(f"[KarpathyLoop] Lesson generated: {lesson[:80]}...")
            return lesson
        except Exception as e:
            print(f"[KarpathyLoop] Lesson generation failed: {e}")
            return None
    
    def execute_with_skills(self, agent_id: str, task: str) -> dict:
        """
        Executes a task, trying to use existing skills first.
        If no skill matches, falls back to regular AI execution.
        """
        agent = self.kernel.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        # Check if any skill matches the task
        skills = self.skills_engine.list_skills(agent_id)
        matching_skill = None
        
        task_lower = task.lower()
        for skill_meta in skills:
            skill_name = skill_meta["name"]
            # Simple keyword matching
            skill_keywords = skill_name.replace("skill_", "").split("_")[:3]
            match_score = sum(1 for kw in skill_keywords if kw in task_lower)
            if match_score >= 1:
                matching_skill = skill_name
                break
        
        if matching_skill:
            # Try to use the skill
            result = self.skills_engine.execute_skill(agent_id, matching_skill, task=task)
            if "error" not in result:
                return {
                    "used_skill": matching_skill,
                    "output": str(result.get("result", "")),
                    "method": "skill"
                }
        
        # Fallback: regular AI execution
        executor = AgentExecutor(
            agent_id=agent.agent_id,
            name=agent.name,
            role=agent.role_description,
            skills=agent.skills
        )
        output = executor.execute(task)
        
        return {
            "used_skill": None,
            "output": output,
            "method": "ai_fallback"
        }
    
    def list_agent_skills(self, agent_id: str) -> list:
        """Returns all skills for an agent."""
        return self.skills_engine.list_skills(agent_id)
