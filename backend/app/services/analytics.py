"""
Analytics Service for tracking and aggregating usage metrics.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, Integer
from sqlalchemy.sql import text

from app.models.analytics import AgentAnalytics, ToolUsageLog
from app.models.custom_agent import CustomAgent

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking and querying analytics"""
    
    @staticmethod
    async def track_agent_run(
        db: AsyncSession,
        agent_id: UUID,
        user_id: UUID,
        success: bool,
        response_time: float,
        tokens_used: Optional[Dict[str, int]] = None,
        tools_used: Optional[List[str]] = None
    ):
        """
        Track a single agent run and update daily analytics.
        
        Args:
            db: Database session
            agent_id: Agent UUID
            user_id: User UUID
            success: Whether run was successful
            response_time: Response time in seconds
            tokens_used: Dict with 'prompt', 'completion', 'total' keys
            tools_used: List of tool names used
        """
        # Get today's date (midnight)
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get or create analytics record for today
        result = await db.execute(
            select(AgentAnalytics).where(
                and_(
                    AgentAnalytics.agent_id == agent_id,
                    AgentAnalytics.user_id == user_id,
                    AgentAnalytics.date == today
                )
            )
        )
        analytics = result.scalar_one_or_none()
        
        if not analytics:
            analytics = AgentAnalytics(
                agent_id=agent_id,
                user_id=user_id,
                date=today,
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                total_response_time=0.0,
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                tool_calls_count=0
            )
            db.add(analytics)
        
        # Update run counts
        analytics.total_runs += 1
        if success:
            analytics.successful_runs += 1
        else:
            analytics.failed_runs += 1
        
        # Update response time metrics
        analytics.total_response_time += response_time
        if analytics.avg_response_time is None:
            analytics.avg_response_time = response_time
        else:
            # Recalculate average
            analytics.avg_response_time = analytics.total_response_time / analytics.total_runs
        
        if analytics.min_response_time is None or response_time < analytics.min_response_time:
            analytics.min_response_time = response_time
        
        if analytics.max_response_time is None or response_time > analytics.max_response_time:
            analytics.max_response_time = response_time
        
        # Update token usage if available
        if tokens_used:
            analytics.total_tokens += tokens_used.get('total', 0)
            analytics.prompt_tokens += tokens_used.get('prompt', 0)
            analytics.completion_tokens += tokens_used.get('completion', 0)
        
        # Update tool usage
        if tools_used:
            analytics.tool_calls_count += len(tools_used)
            
            # Log individual tool usage
            for tool_name in tools_used:
                tool_log = ToolUsageLog(
                    agent_id=agent_id,
                    user_id=user_id,
                    tool_name=tool_name,
                    success=success
                )
                db.add(tool_log)
        
        await db.commit()
        logger.info(f"Tracked analytics for agent {agent_id}")
    
    @staticmethod
    async def get_agent_analytics(
        db: AsyncSession,
        agent_id: UUID,
        user_id: Optional[UUID] = None,
        days: int = 30
    ) -> List[Dict]:
        """
        Get analytics for an agent over a time period.
        
        Args:
            db: Database session
            agent_id: Agent UUID
            user_id: Optional user filter
            days: Number of days to look back
            
        Returns:
            List of analytics records
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(AgentAnalytics).where(
            and_(
                AgentAnalytics.agent_id == agent_id,
                AgentAnalytics.date >= start_date
            )
        )
        
        if user_id:
            query = query.where(AgentAnalytics.user_id == user_id)
        
        query = query.order_by(AgentAnalytics.date)
        
        result = await db.execute(query)
        analytics = result.scalars().all()
        
        return [
            {
                "date": a.date.isoformat(),
                "total_runs": a.total_runs,
                "successful_runs": a.successful_runs,
                "failed_runs": a.failed_runs,
                "avg_response_time": a.avg_response_time,
                "min_response_time": a.min_response_time,
                "max_response_time": a.max_response_time,
                "total_tokens": a.total_tokens,
                "tool_calls": a.tool_calls_count
            }
            for a in analytics
        ]
    
    @staticmethod
    async def get_summary_stats(
        db: AsyncSession,
        agent_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        days: int = 30
    ) -> Dict:
        """
        Get summary statistics.
        
        Args:
            db: Database session
            agent_id: Optional agent filter
            user_id: Optional user filter (for access control)
            days: Number of days to look back
            
        Returns:
            Summary statistics dict
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        conditions = [AgentAnalytics.date >= start_date]
        if agent_id:
            conditions.append(AgentAnalytics.agent_id == agent_id)
            
            # Check agent visibility for access control
            agent_result = await db.execute(
                select(CustomAgent.visibility, CustomAgent.user_id).where(CustomAgent.id == agent_id)
            )
            agent_row = agent_result.first()
            
            if agent_row:
                visibility, owner_id = agent_row
                # For private agents, only show stats for the owner
                if visibility == 'private' and user_id:
                    conditions.append(AgentAnalytics.user_id == user_id)
                # For public/team agents, aggregate all users (no user_id filter)
        
        # Aggregate query
        result = await db.execute(
            select(
                func.sum(AgentAnalytics.total_runs).label('total_runs'),
                func.sum(AgentAnalytics.successful_runs).label('successful_runs'),
                func.sum(AgentAnalytics.failed_runs).label('failed_runs'),
                func.avg(AgentAnalytics.avg_response_time).label('avg_response_time'),
                func.sum(AgentAnalytics.total_tokens).label('total_tokens'),
                func.sum(AgentAnalytics.prompt_tokens).label('prompt_tokens'),
                func.sum(AgentAnalytics.completion_tokens).label('completion_tokens'),
                func.sum(AgentAnalytics.tool_calls_count).label('tool_calls')
            ).where(and_(*conditions))
        )
        
        row = result.first()
        
        return {
            "total_runs": row.total_runs or 0,
            "successful_runs": row.successful_runs or 0,
            "failed_runs": row.failed_runs or 0,
            "success_rate": (row.successful_runs / row.total_runs * 100) if row.total_runs else 0,
            "avg_response_time": round(row.avg_response_time, 2) if row.avg_response_time else 0,
            "total_tokens": row.total_tokens or 0,
            "prompt_tokens": row.prompt_tokens or 0,
            "completion_tokens": row.completion_tokens or 0,
            "tool_calls": row.tool_calls or 0
        }
    
    @staticmethod
    async def get_tool_usage_stats(
        db: AsyncSession,
        agent_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        days: int = 30
    ) -> List[Dict]:
        """
        Get tool usage statistics.
        
        Args:
            db: Database session
            agent_id: Optional agent filter
            user_id: Optional user filter
            days: Number of days to look back
            
        Returns:
            List of tool usage stats
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        conditions = [ToolUsageLog.timestamp >= start_date]
        if agent_id:
            conditions.append(ToolUsageLog.agent_id == agent_id)
        if user_id:
            conditions.append(ToolUsageLog.user_id == user_id)
        
        result = await db.execute(
            select(
                ToolUsageLog.tool_name,
                func.count(ToolUsageLog.id).label('usage_count'),
                func.sum(func.cast(ToolUsageLog.success, Integer)).label('success_count')
            )
            .where(and_(*conditions))
            .group_by(ToolUsageLog.tool_name)
            .order_by(func.count(ToolUsageLog.id).desc())
        )
        
        return [
            {
                "tool_name": row.tool_name,
                "usage_count": row.usage_count,
                "success_count": row.success_count,
                "success_rate": (row.success_count / row.usage_count * 100) if row.usage_count else 0
            }
            for row in result
        ]


# Global instance
analytics_service = AnalyticsService()
