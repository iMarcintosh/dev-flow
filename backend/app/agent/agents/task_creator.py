from app.agent.base_agent import BaseDevFlowAgent, AgentInput, AgentResult, AgentTrigger
from app.agent.registry import registry
from app.config import settings
from typing import Dict, Any, List
import json


class TaskCreatorAgent(BaseDevFlowAgent):
    """
    Agent that analyzes free-form text and creates structured tasks.
    
    Uses LLM (Claude/GPT) to:
    1. Classify the input (bug, story, epic, multiple items?)
    2. Enrich with proper title, description, acceptance criteria
    3. Break down into sub-tasks if needed
    4. Estimate priority
    5. Validate completeness
    """
    
    name = "task_creator"
    description = "Analyzes text input and creates structured board items using AI"
    trigger = AgentTrigger.MANUAL
    
    def __init__(self):
        super().__init__()
        self._llm = None
    
    def _get_llm(self):
        """Lazy-load LLM based on provider."""
        if self._llm is None:
            if settings.anthropic_api_key:
                from langchain_anthropic import ChatAnthropic
                self._llm = ChatAnthropic(
                    model="claude-3-haiku-20240307",  # Claude 3 Haiku (fast & available)
                    anthropic_api_key=settings.anthropic_api_key,
                    temperature=0.7,
                    max_tokens=4096
                )
            elif settings.openai_api_key:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model="gpt-4",
                    openai_api_key=settings.openai_api_key,
                    temperature=0.7
                )
            else:
                # Fallback to rule-based
                self._llm = None
        return self._llm
    
    async def run(self, input_data: AgentInput, run_id: str) -> AgentResult:
        """Execute the task creation workflow."""
        
        await self.log(run_id, "Starting task creation analysis...", "info")
        
        # Extract user input
        user_text = input_data.data.get("text", "")
        if not user_text:
            return AgentResult(
                success=False,
                output={},
                message="No input text provided",
                error="Missing 'text' in input data"
            )
        
        await self.log(run_id, f"Analyzing: {user_text[:100]}...", "info")
        
        try:
            # Step 1: Classify
            await self.log(run_id, "Step 1/5: Classifying input type...", "info")
            classification = await self._classify(user_text)
            
            # Step 2: Enrich
            await self.log(run_id, "Step 2/5: Enriching with metadata...", "info")
            enriched = await self._enrich(user_text, classification)
            
            # Step 3: Break down
            await self.log(run_id, "Step 3/5: Breaking down into tasks...", "info")
            tasks = await self._breakdown(enriched)
            
            # Step 4: Estimate priority
            await self.log(run_id, "Step 4/5: Estimating priorities...", "info")
            tasks_with_priority = await self._estimate_priority(tasks)
            
            # Step 5: Validate
            await self.log(run_id, "Step 5/5: Validating output...", "info")
            validated = await self._validate(tasks_with_priority)
            
            await self.log(run_id, f"✓ Analysis complete! Generated {len(validated)} items.", "info")
            
            return AgentResult(
                success=True,
                output={
                    "preview": validated,
                    "classification": classification,
                    "original_text": user_text
                },
                message=f"Successfully analyzed and created {len(validated)} items",
                items_created=[]  # Will be filled after user confirms
            )
            
        except Exception as e:
            await self.log(run_id, f"Error: {str(e)}", "error")
            return AgentResult(
                success=False,
                output={},
                message="Failed to analyze input",
                error=str(e)
            )
    
    async def _classify(self, text: str) -> Dict[str, Any]:
        """Classify the input type using LLM or fallback to rules."""
        llm = self._get_llm()
        
        if llm:
            # Use LLM for intelligent classification
            from langchain_core.messages import HumanMessage, SystemMessage
            
            prompt = f"""Analyze this text and classify it as a development item.

Text: {text}

Respond in JSON format:
{{
    "type": "bug|story|epic|task|spike",
    "multiple": true/false,
    "confidence": 0-100,
    "reasoning": "brief explanation"
}}

Types:
- bug: defect, error, broken functionality
- story: user feature, user story
- epic: large feature spanning multiple stories
- task: technical work, chore
- spike: research, investigation

Multiple: true if text describes several distinct items."""

            messages = [
                SystemMessage(content="You are an expert software project manager classifying development items."),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            result = json.loads(response.content)
            return result
        else:
            # Fallback to rule-based classification
            text_lower = text.lower()
            
            if "bug" in text_lower or "error" in text_lower or "broken" in text_lower:
                return {"type": "bug", "multiple": False, "confidence": 70, "reasoning": "Keyword match"}
            elif "epic" in text_lower or "feature" in text_lower:
                return {"type": "epic", "multiple": True, "confidence": 70, "reasoning": "Keyword match"}
            elif "story" in text_lower or "user" in text_lower:
                return {"type": "story", "multiple": False, "confidence": 70, "reasoning": "Keyword match"}
            elif "spike" in text_lower or "research" in text_lower or "investigate" in text_lower:
                return {"type": "spike", "multiple": False, "confidence": 70, "reasoning": "Keyword match"}
            else:
                return {"type": "task", "multiple": "," in text or "\n" in text, "confidence": 50, "reasoning": "Default"}
    
    async def _enrich(self, text: str, classification: Dict) -> Dict[str, Any]:
        """Enrich with proper structure using LLM or fallback."""
        llm = self._get_llm()
        
        if llm:
            # Use LLM for intelligent enrichment
            from langchain_core.messages import HumanMessage, SystemMessage
            
            prompt = f"""Create a well-structured {classification['type']} from this text.

Text: {text}

Respond in JSON format:
{{
    "title": "Clear, concise title (max 100 chars)",
    "description": "Detailed description with context",
    "acceptance_criteria": "- Criterion 1\\n- Criterion 2\\n- Criterion 3",
    "type": "{classification['type']}"
}}

Make it professional and actionable."""

            messages = [
                SystemMessage(content="You are an expert technical writer creating clear development items."),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            result = json.loads(response.content)
            return result
        else:
            # Fallback to simple parsing
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            
            return {
                "title": lines[0][:100] if lines else text[:100],
                "description": "\n".join(lines[1:]) if len(lines) > 1 else text,
                "type": classification["type"],
                "acceptance_criteria": "- Implement the described functionality\n- Write tests\n- Update documentation"
            }
    
    async def _breakdown(self, enriched: Dict) -> List[Dict[str, Any]]:
        """Break down into sub-tasks if needed."""
        # Simplified breakdown (in real implementation, use LLM)
        return [enriched]  # For now, just return the single item
    
    async def _estimate_priority(self, tasks: List[Dict]) -> List[Dict]:
        """Estimate priority for each task."""
        # Simplified priority estimation
        for task in tasks:
            if task["type"] == "bug":
                task["priority"] = "high"
            elif task["type"] == "epic":
                task["priority"] = "critical"
            else:
                task["priority"] = "medium"
        return tasks
    
    async def _validate(self, tasks: List[Dict]) -> List[Dict]:
        """Validate completeness."""
        validated = []
        for task in tasks:
            # Ensure all required fields
            if not task.get("title"):
                continue
            
            validated.append({
                "type": task.get("type", "task"),
                "title": task["title"],
                "description": task.get("description", ""),
                "acceptance_criteria": task.get("acceptance_criteria", ""),
                "priority": task.get("priority", "medium"),
                "tags": []
            })
        
        return validated


# Auto-register the agent
registry.register(TaskCreatorAgent())
