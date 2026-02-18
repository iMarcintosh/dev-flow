from typing import Dict, List, Optional
from app.agent.base_agent import BaseDevFlowAgent, AgentTrigger


class AgentRegistry:
    """
    Singleton registry for all DevFlow agents.
    
    Agents self-register on import, making them automatically
    available throughout the application.
    """
    
    _instance: Optional['AgentRegistry'] = None
    _agents: Dict[str, BaseDevFlowAgent] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, agent: BaseDevFlowAgent):
        """Register an agent."""
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' is already registered")
        self._agents[agent.name] = agent
        print(f"✓ Registered agent: {agent.name}")
    
    def get(self, name: str) -> Optional[BaseDevFlowAgent]:
        """Get an agent by name."""
        return self._agents.get(name)
    
    def all(self) -> List[BaseDevFlowAgent]:
        """Get all registered agents."""
        return list(self._agents.values())
    
    def scheduled(self) -> List[BaseDevFlowAgent]:
        """Get all scheduled agents."""
        return [
            agent for agent in self.all()
            if agent.trigger == AgentTrigger.SCHEDULED
        ]
    
    def list_agents(self) -> List[dict]:
        """List all agents with their metadata."""
        return [agent.to_dict() for agent in self.all()]


# Global singleton instance
registry = AgentRegistry()
