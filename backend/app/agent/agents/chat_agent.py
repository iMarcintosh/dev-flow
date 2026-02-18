"""Chat agent for board conversations with context awareness."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.agent.base_agent import (
    BaseDevFlowAgent,
    AgentTrigger,
    AgentInput,
    AgentResult
)
from app.agent.memory.vector_store import vector_store
from app.database import async_session_maker
from app.models.chat import ChatMessage
from app.config import settings

logger = logging.getLogger(__name__)


class ChatAgent(BaseDevFlowAgent):
    """
    Chat agent with board context and memory.
    
    Capabilities:
    - Answers questions about board items
    - Provides project statistics
    - Can reference specific items
    - Maintains conversation history
    """
    
    name = "chat_agent"
    description = "Board chatbot with project context and memory"
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
                    model="claude-3-haiku-20240307",
                    anthropic_api_key=settings.anthropic_api_key,
                    temperature=0.7,
                    max_tokens=2048
                )
            elif settings.openai_api_key:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model="gpt-4",
                    openai_api_key=settings.openai_api_key,
                    temperature=0.7
                )
            else:
                self._llm = None
        return self._llm
    
    async def run(self, input: AgentInput, run_id: str) -> AgentResult:
        """Process chat message and generate response."""
        try:
            user_message = input.data.get("message", "")
            project_id = input.project_id
            
            await self.log(run_id, f"Processing message: {user_message[:100]}...")
            
            async with async_session_maker() as db:
                # 1. Get conversation history (last 20 messages)
                await self.log(run_id, "Loading conversation history...")
                history = await self._get_conversation_history(
                    db, project_id, limit=20
                )
                
                # 2. Get project stats
                await self.log(run_id, "Gathering project statistics...")
                stats = await vector_store.get_project_stats(db, project_id)
                
                # 3. Semantic search for relevant items
                await self.log(run_id, "Searching for relevant items...")
                relevant_items = await vector_store.similarity_search(
                    db, user_message, project_id, top_k=5
                )
                
                # 4. Build context
                context = self._build_context(stats, relevant_items, history)
                
                # 5. Generate response (simple rule-based for now, ready for LLM)
                await self.log(run_id, "Generating response...")
                response = await self._generate_response(
                    user_message, context, relevant_items
                )
                
                # 6. Save messages to DB
                await self._save_messages(
                    db, project_id, input.user_id, user_message, response
                )
                
                await self.log(run_id, "Response generated successfully")
                
                return AgentResult(
                    success=True,
                    output={
                        "message": response,
                        "referenced_items": [
                            {
                                "id": str(item.id),
                                "title": item.title,
                                "type": item.type.value,
                                "status": item.status.value
                            }
                            for item in relevant_items[:3]
                        ]
                    },
                    message="Chat response generated"
                )
                
        except Exception as e:
            await self.log(run_id, f"Error: {str(e)}", level="error")
            logger.exception("Chat agent failed")
            return AgentResult(
                success=False,
                output={},
                message=f"Error: {str(e)}"
            )
    
    async def _get_conversation_history(
        self, db, project_id: str, limit: int = 20
    ) -> List[ChatMessage]:
        """Fetch recent conversation history."""
        from sqlalchemy import select
        
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.project_id == project_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        return list(reversed(messages))
    
    def _build_context(
        self, stats: Dict, items: List, history: List[ChatMessage]
    ) -> str:
        """Build contextual information for the agent."""
        parts = ["# Project Context\n"]
        
        # Statistics
        parts.append(f"Total Items: {stats['total_items']}")
        parts.append(f"By Status: {json.dumps(stats['by_status'])}")
        parts.append(f"By Type: {json.dumps(stats['by_type'])}")
        parts.append(f"By Priority: {json.dumps(stats['by_priority'])}")
        parts.append("")
        
        # Relevant items
        if items:
            parts.append("# Relevant Items:\n")
            for idx, item in enumerate(items[:5], 1):
                parts.append(f"{idx}. [{item.type.value.upper()}] {item.title}")
                parts.append(f"   Status: {item.status.value}, Priority: {item.priority.value}")
                if item.description:
                    parts.append(f"   {item.description[:200]}...")
                parts.append("")
        
        # Recent conversation
        if history:
            parts.append("# Recent Conversation:\n")
            for msg in history[-5:]:
                role = "User" if msg.role == "user" else "Assistant"
                parts.append(f"{role}: {msg.content[:100]}...")
        
        return "\n".join(parts)
    
    async def _generate_response(
        self, message: str, context: str, items: List
    ) -> str:
        """
        Generate response based on message and context.
        Uses LLM if available, otherwise falls back to rule-based logic.
        """
        llm = self._get_llm()
        
        if llm:
            # Use LLM for intelligent responses
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                
                system_prompt = f"""You are a helpful AI assistant for DevFlow, a project management tool.
You have access to the user's project board with all their tasks, bugs, stories, and epics.

{context}

CRITICAL RULES - NEVER VIOLATE THESE:
1. ONLY reference items that are EXPLICITLY listed in the "Relevant Items" section above
2. If no relevant items are found, say "I don't see any items matching that" - DO NOT make up items
3. NEVER invent item titles, descriptions, or details that aren't in the context
4. Use exact item titles from the context - do not paraphrase or change them
5. If you're unsure, say "I'm not certain" instead of guessing
6. When asked about counts, ONLY use the statistics provided in the context
7. ALWAYS respond in the SAME LANGUAGE the user asked in (German → German, English → English, etc.)

Guidelines:
- Be concise and helpful
- Reference specific items by their EXACT title in quotes when relevant
- Use the project statistics when answering questions about counts or status
- If you mention an item, format it like: "the bug 'Password field doesn't accept special characters'"
- Be conversational but professional
- If the context doesn't contain enough information to answer, explicitly say so

Remember: Accuracy is more important than being helpful. It's better to say "I don't have that information" than to make something up."""

                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=message)
                ]
                
                response = llm.invoke(messages)
                return response.content
                
            except Exception as e:
                logger.error(f"LLM call failed: {e}, falling back to rules")
                # Fall through to rule-based logic
        
        # Rule-based fallback (original logic)
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["how many", "count", "total"]):
            if "bug" in message_lower:
                return self._count_response(context, "bug")
            elif "task" in message_lower:
                return self._count_response(context, "task")
            elif "story" in message_lower or "stories" in message_lower:
                return self._count_response(context, "story")
            else:
                return self._general_count_response(context)
        
        elif any(word in message_lower for word in ["status", "progress"]):
            return self._status_response(context)
        
        elif any(word in message_lower for word in ["priority", "urgent", "critical"]):
            return self._priority_response(context, items)
        
        elif items:
            item_refs = ", ".join([
                f"'{item.title}' ({item.type.value})"
                for item in items[:3]
            ])
            return f"I found these relevant items: {item_refs}. What would you like to know about them?"
        
        else:
            return "I'm here to help with your board! Ask me about tasks, bugs, stories, or project status."
    
    def _count_response(self, context: str, item_type: str) -> str:
        """Extract count for specific item type."""
        import json
        
        # Parse context for type counts
        for line in context.split('\n'):
            if "By Type:" in line:
                try:
                    type_data = json.loads(line.split("By Type: ")[1])
                    count = type_data.get(item_type, 0)
                    return f"You have {count} {item_type}(s) in this project."
                except:
                    pass
        
        return f"I couldn't find the count for {item_type}s."
    
    def _general_count_response(self, context: str) -> str:
        """General item count response."""
        for line in context.split('\n'):
            if "Total Items:" in line:
                count = line.split(": ")[1]
                return f"This project has {count} total items."
        
        return "I couldn't retrieve the item count."
    
    def _status_response(self, context: str) -> str:
        """Project status overview."""
        import json
        
        for line in context.split('\n'):
            if "By Status:" in line:
                try:
                    status_data = json.loads(line.split("By Status: ")[1])
                    backlog = status_data.get('backlog', 0)
                    in_progress = status_data.get('in_progress', 0)
                    review = status_data.get('review', 0)
                    done = status_data.get('done', 0)
                    
                    return (
                        f"Project status: {backlog} in backlog, "
                        f"{in_progress} in progress, {review} in review, "
                        f"{done} done."
                    )
                except:
                    pass
        
        return "I couldn't retrieve the project status."
    
    def _priority_response(self, context: str, items: List) -> str:
        """Priority-related response."""
        import json
        
        for line in context.split('\n'):
            if "By Priority:" in line:
                try:
                    priority_data = json.loads(line.split("By Priority: ")[1])
                    critical = priority_data.get('critical', 0)
                    high = priority_data.get('high', 0)
                    
                    if critical > 0 or high > 0:
                        high_priority_items = [
                            item for item in items 
                            if item.priority.value in ['critical', 'high']
                        ]
                        
                        msg = f"You have {critical} critical and {high} high priority items."
                        
                        if high_priority_items:
                            top_item = high_priority_items[0]
                            msg += f" Top priority: '{top_item.title}' ({top_item.priority.value})."
                        
                        return msg
                    else:
                        return "No critical or high priority items at the moment."
                except:
                    pass
        
        return "I couldn't retrieve priority information."
    
    async def _save_messages(
        self, db, project_id: str, user_id: str, 
        user_message: str, assistant_message: str
    ):
        """Save user and assistant messages to database."""
        # User message
        user_msg = ChatMessage(
            user_id=user_id,
            project_id=project_id,
            role="user",
            content=user_message
        )
        db.add(user_msg)
        
        # Assistant message
        assistant_msg = ChatMessage(
            user_id=user_id,  # Same user for context
            project_id=project_id,
            role="assistant",
            content=assistant_message
        )
        db.add(assistant_msg)
        
        await db.commit()


# Register agent
from app.agent.registry import registry
registry.register(ChatAgent())
