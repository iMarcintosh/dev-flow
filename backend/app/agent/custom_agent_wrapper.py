"""
CustomAgentWrapper - Bridges custom agents with BaseDevFlowAgent system.

Allows custom agents created by users to work with the existing
agent infrastructure (scheduling, webhooks, etc.)
"""

from uuid import UUID
from typing import Optional
from app.agent.base_agent import BaseDevFlowAgent, AgentInput, AgentResult, AgentTrigger
from app.database import async_session_maker
from app.agent import custom_agent_runner


class CustomAgentWrapper(BaseDevFlowAgent):
    """
    Wrapper that makes a custom agent compatible with BaseDevFlowAgent.
    
    This allows custom agents to be triggered by the same mechanisms
    as built-in agents (manual, scheduled, webhooks, etc.)
    """
    
    def __init__(self, agent_id: UUID, agent_name: str, trigger: AgentTrigger = AgentTrigger.MANUAL):
        """
        Initialize wrapper for a custom agent.
        
        Args:
            agent_id: UUID of the custom agent in the database
            agent_name: Name for registration
            trigger: How this agent should be triggered
        """
        self.agent_id = agent_id
        self.name = f"custom_{agent_name}"
        self.description = f"Custom agent: {agent_name}"
        self.trigger = trigger
        self.schedule = None
        
        super().__init__()
    
    async def run(self, input_data: AgentInput, run_id: str) -> AgentResult:
        """
        Execute the custom agent.
        
        Args:
            input_data: Standard agent input
            run_id: Unique run identifier
        
        Returns:
            AgentResult with success status and output
        """
        await self.log(run_id, f"Starting custom agent: {self.name}", "info")
        
        # Get input text
        input_text = input_data.data.get("text", "")
        if not input_text:
            input_text = input_data.data.get("message", "")
        
        if not input_text:
            await self.log(run_id, "No input text provided", "warning")
            return AgentResult(
                success=False,
                output={},
                message="No input text provided",
                error="Missing 'text' or 'message' in input data"
            )
        
        await self.log(run_id, f"Input: {input_text[:100]}...", "info")
        
        try:
            # Execute custom agent
            async with async_session_maker() as db:
                result = await custom_agent_runner.run_custom_agent(
                    db=db,
                    agent_id=self.agent_id,
                    user_id=UUID(input_data.user_id),
                    input_text=input_text,
                    project_id=UUID(input_data.project_id) if input_data.project_id else None,
                )
            
            if result["success"]:
                await self.log(run_id, "Agent execution successful", "info")
                return AgentResult(
                    success=True,
                    output={
                        "response": result["response"],
                        "model": result["model"],
                        "tools_used": result.get("tools_used", []),
                    },
                    message=f"Agent '{result['agent_name']}' completed successfully"
                )
            else:
                await self.log(run_id, f"Agent execution failed: {result.get('error')}", "error")
                return AgentResult(
                    success=False,
                    output={"error": result.get("error")},
                    message="Agent execution failed",
                    error=result.get("error")
                )
        
        except Exception as e:
            await self.log(run_id, f"Unexpected error: {str(e)}", "error")
            return AgentResult(
                success=False,
                output={},
                message="Unexpected error during agent execution",
                error=str(e)
            )


def create_wrapper_for_agent(
    agent_id: UUID,
    agent_name: str,
    trigger: AgentTrigger = AgentTrigger.MANUAL
) -> CustomAgentWrapper:
    """
    Factory function to create a wrapper for a custom agent.
    
    Args:
        agent_id: UUID of custom agent
        agent_name: Name for the wrapper
        trigger: Trigger type
    
    Returns:
        CustomAgentWrapper instance
    """
    return CustomAgentWrapper(
        agent_id=agent_id,
        agent_name=agent_name,
        trigger=trigger,
    )
