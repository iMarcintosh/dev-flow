# 🤖 LLM Integration Status

**Stand: 2026-03-12**

## ✅ Vollständig implementiert

### Per-User API Key Management
- Nutzer können eigene Anthropic/OpenAI/OpenRouter Keys in den Settings hinterlegen
- Keys werden verschlüsselt gespeichert (Fernet/AES-128)
- Fallback-Hierarchie: User Key → `.env` Global Key → Error
- `model_resolver.py` resolved den richtigen Key automatisch pro User
- **Model-Discovery-Cache ist per-User** (`available_models:{user_id}`) — jeder Nutzer sieht nur Modelle, auf die er Zugriff hat
- **Embedding-Key für Knowledge-Base-Suche** wird ebenfalls per-User aufgelöst und an `KnowledgeBaseTool` weitergereicht

### Unterstützte Modelle

#### Anthropic (hardcoded, kein API-Endpoint verfügbar)
| Modell | Tier |
|--------|------|
| `claude-opus-4-6` | highest |
| `claude-sonnet-4-6` | high |
| `claude-haiku-4-5` | low |
| `claude-sonnet-4-5`, `claude-opus-4-5` | legacy |
| `claude-3-7-sonnet-latest` | high |
| `claude-3-haiku-20240307` | low |

#### OpenAI (live via `/v1/models` oder Fallback-Liste)
| Familie | Modelle | Kontext |
|---------|---------|---------|
| GPT-5 (2026) | `gpt-5`, `gpt-5-mini` | 1M |
| GPT-4.1 (2025) | `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano` | 1M |
| GPT-4o | `gpt-4o`, `gpt-4o-mini` | 128k |
| Reasoning | `o3`, `o3-mini`, `o1`, `o1-mini` | 200k/128k |

Live-Fetch filtert auf Präfixe `gpt-5`, `gpt-4.1`, `gpt-4o`, `o1`, `o3`, `o4` und schließt Preview/veraltete Suffix-Varianten aus.

#### OpenRouter
- Alle OpenRouter-kompatiblen Modelle (live via `/api/v1/models`)
- Kostenklasse wird aus `pricing.prompt` berechnet

### Agent Chat (SSE Streaming)
- Agent Chat nutzt SSE statt WebSocket
- Streaming per `POST /api/agent-chat/conversations/{id}/messages/stream`
- LangGraph ReAct Agent für Tool-Calling
- **No-Flicker:** User- und Assistenten-Nachricht werden optimistisch in den TanStack Query Cache geschrieben; `invalidateQueries` mit `refetchType: 'none'` verhindert sofortigen Re-Fetch
- **Streaming-Indikator:** Rotierender Conic-Gradient-Border (`animate-streaming-border`) statt Cursor-Span

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
