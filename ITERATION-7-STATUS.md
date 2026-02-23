# DevFlow - Iteration 7 Status

**Date:** 2026-02-23
**Focus:** Agent Chat Bug Fixes
**Status:** ✅ **COMPLETE**

---

## 🎯 Iteration Goals

1. ✅ Fix: Sent messages not visible immediately after sending
2. ✅ Fix: Long conversations showing oldest 100 messages instead of newest 100

---

## ✅ Completed Fixes

### Bug 1: Optimistic Update beim Senden

**Root Cause:**
`AgentChatPage.tsx` had no optimistic update for the user's message. After sending, `isStreaming=true` showed a streaming bubble, but the actual user message was never added to the local cache — it only appeared after `invalidateQueries()` on `event.type === 'end'`.

**Fix:**
Immediately after `setIsStreaming(true)`, the user message is written into the TanStack Query cache:

```typescript
const optimisticMessage: AgentMessage = {
  id: crypto.randomUUID(),
  conversation_id: selectedConversationId,
  role: 'user',
  content: text,
  message_metadata: {},
  created_at: new Date().toISOString(),
}
queryClient.setQueryData(
  ['conversation-messages', selectedConversationId],
  (old: AgentMessage[] = []) => [...old, optimisticMessage]
)
```

After streaming completes, `invalidateQueries()` replaces the optimistic entry with the real DB record.

**File:** `frontend/src/components/agent-chat/AgentChatPage.tsx`

---

### Bug 2: Neueste Nachrichten bei langen Conversations

**Root Cause:**
`get_conversation_history()` in `conversation_service.py` ordered by `created_at ASC` with a limit of 100 — returning the **oldest** 100 messages, cutting off the most recent ones.

**Fix:**
Order DESC to get newest first, limit, then reverse in Python:

```python
query = (
    select(AgentMessage)
    .where(AgentMessage.conversation_id == conversation_id)
    .order_by(AgentMessage.created_at.desc())  # Newest first
    .limit(limit)
)
result = await db.execute(query)
messages = list(result.scalars().all())
return list(reversed(messages))  # Back to chronological order
```

**File:** `backend/app/services/conversation_service.py`

---

## 📦 Files Modified

```
frontend/src/components/agent-chat/AgentChatPage.tsx
  + import AgentMessage type
  + optimistic cache update before fetch starts

backend/app/services/conversation_service.py
  ~ get_conversation_history(): ASC → DESC + reversed()
```

---

## ✅ Verification Checklist

- [ ] Send message → user bubble appears immediately (no reload needed)
- [ ] Agent response streams while user bubble is visible
- [ ] After stream ends → `invalidateQueries` syncs real DB state
- [ ] Conversation with >100 messages → newest messages visible
- [ ] Scroll-to-bottom still works after sending

---

**Created:** 2026-02-23
**Status:** ✅ Complete
