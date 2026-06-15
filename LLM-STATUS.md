# 🤖 LLM Integration Status

**Stand: 2026-02-23**

## ✅ Vollständig implementiert

### Per-User API Key Management
- Nutzer können eigene Anthropic/OpenAI/OpenRouter Keys in den Settings hinterlegen
- Keys werden verschlüsselt gespeichert (Fernet/AES-128)
- Fallback-Hierarchie: User Key → `.env` Global Key → Error
- `model_resolver.py` resolved den richtigen Key automatisch pro User

### Unterstützte Modelle
- **Anthropic:** `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-haiku-4-5-20251001`
- **OpenAI:** GPT-4o, GPT-4o-mini
- **OpenRouter:** Alle OpenRouter-kompatiblen Modelle

### Agent Chat (SSE Streaming)
- Agent Chat nutzt SSE statt WebSocket
- Streaming per `POST /api/agent-chat/conversations/{id}/messages/stream`
- LangGraph ReAct Agent für Tool-Calling
- Optimistic Updates im Frontend seit 2026-02-23

## ⚙️ Konfiguration

### Per User (empfohlen)
1. Login → Settings → API Keys
2. Key eingeben, testen, speichern
3. Alle Agent-Runs nutzen automatisch deinen persönlichen Key

### Global Fallback (.env)
```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
```

## 🔍 Debugging

```bash
# Backend-Logs für LLM-Calls prüfen
docker compose logs -f backend | grep -E "HTTP|LLM|model"

# Erwartete Success-Antwort:
# HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
```
