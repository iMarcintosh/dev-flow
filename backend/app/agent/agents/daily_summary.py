"""Daily summary agent - runs on schedule to provide project insights."""

import logging
from datetime import datetime, timedelta

from app.agent.base_agent import (
    BaseDevFlowAgent,
    AgentTrigger,
    AgentInput,
    AgentResult
)
from app.agent.memory.vector_store import vector_store
from app.database import async_session_maker
from app.models.item import Item
from sqlalchemy import select

logger = logging.getLogger(__name__)


class DailySummaryAgent(BaseDevFlowAgent):
    """
    Scheduled agent that generates daily project summaries.
    
    Runs every day at 9 AM to provide:
    - Items created/updated in last 24h
    - Priority distribution
    - Status changes
    - Recommendations
    """
    
    name = "daily_summary"
    description = "Daily project summary and insights"
    trigger = AgentTrigger.SCHEDULED
    schedule = "0 9 * * *"  # Every day at 9 AM (cron format)
    
    async def run(self, input: AgentInput, run_id: str) -> AgentResult:
        """Generate daily summary for a project."""
        try:
            project_id = input.project_id
            
            await self.log(run_id, "Starting daily summary generation...")
            
            async with async_session_maker() as db:
                # Get project stats
                await self.log(run_id, "Gathering project statistics...")
                stats = await vector_store.get_project_stats(db, project_id)
                
                # Get items created in last 24h
                await self.log(run_id, "Checking recent activity...")
                yesterday = datetime.utcnow() - timedelta(days=1)
                
                stmt = (
                    select(Item)
                    .where(Item.project_id == project_id)
                    .where(Item.created_at >= yesterday)
                )
                result = await db.execute(stmt)
                new_items = result.scalars().all()
                
                # Build summary
                await self.log(run_id, "Building summary...")
                summary = self._build_summary(stats, new_items)
                
                await self.log(run_id, f"Summary complete: {len(new_items)} new items")
                
                return AgentResult(
                    success=True,
                    output={
                        "summary": summary,
                        "new_items_count": len(new_items),
                        "total_items": stats["total_items"],
                        "stats": stats
                    },
                    message="Daily summary generated successfully"
                )
                
        except Exception as e:
            await self.log(run_id, f"Error: {str(e)}", level="error")
            logger.exception("Daily summary agent failed")
            return AgentResult(
                success=False,
                output={},
                message=f"Error: {str(e)}"
            )
    
    def _build_summary(self, stats: dict, new_items: list) -> str:
        """Build human-readable summary."""
        lines = ["# Daily Project Summary\n"]
        
        # Overview
        lines.append(f"**Total Items:** {stats['total_items']}")
        lines.append(f"**New Items (24h):** {len(new_items)}\n")
        
        # Status breakdown
        lines.append("## Status Breakdown")
        for status, count in stats.get('by_status', {}).items():
            lines.append(f"- {status.capitalize()}: {count}")
        lines.append("")
        
        # Priority distribution
        lines.append("## Priority Distribution")
        for priority, count in stats.get('by_priority', {}).items():
            lines.append(f"- {priority.capitalize()}: {count}")
        lines.append("")
        
        # Recent activity
        if new_items:
            lines.append("## Recent Activity")
            for item in new_items[:5]:  # Show max 5
                lines.append(f"- [{item.type.value.upper()}] {item.title}")
        
        # Recommendations
        lines.append("\n## Recommendations")
        critical = stats.get('by_priority', {}).get('critical', 0)
        high = stats.get('by_priority', {}).get('high', 0)
        
        if critical > 0:
            lines.append(f"⚠️ {critical} critical priority items need attention")
        if high > 3:
            lines.append(f"⚡ {high} high priority items - consider prioritization")
        
        backlog = stats.get('by_status', {}).get('backlog', 0)
        if backlog > 10:
            lines.append(f"📋 Large backlog ({backlog} items) - time for grooming?")
        
        return "\n".join(lines)


# Register agent
from app.agent.registry import registry
registry.register(DailySummaryAgent())
