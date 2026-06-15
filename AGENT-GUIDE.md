# 🤖 DevFlow Agenten - Komplette Anleitung

## 📊 Aktueller Status (Stand: 2026-02-23)

**✅ Vollständig implementierte Features:**

### 🎨 Custom Agents mit modernem UI
- **Agent Hub** - Moderne Card-UI mit Icon-basierten Statistiken
- **Diagonal Shine Effect** - Elegante Hover-Animation (400ms Delay, 1.2s smooth)
- **Scheduled Agents** - Automatische Ausführung via Cron (stündlich, täglich, wöchentlich, custom)
- **Token Tracking** - Präzise Token-Zählung mit tiktoken (Prompt + Completion)
- **Execution History** - Vollständige Logs aller Scheduled Runs

### 🛠️ Verfügbare Tools
1. **Task Creator** - Text → strukturierte Tasks
2. **Chat Agent** - Board Q&A Chatbot  
3. **Daily Summary** - Scheduled Agent (täglich 9:00 Uhr)
4. **Knowledge Base** - RAG mit lokalen Embeddings (kein OpenAI nötig)
5. **Code Execution** - Python, JavaScript, Bash in Docker Sandbox
6. **Web Search** - Echtzeit-Websuche

**⚠️ API-Keys:**
- Optional für echte AI (Claude, GPT-4)
- Ohne Keys: Rule-based Pattern-Matching (funktioniert trotzdem!)
- Mit Keys: Intelligentes Verständnis und kreative Lösungen

---

## 🎯 Agent Hub - Neue Features

### Modern Card UI
**Features:**
- **Icon-basierte Stats** - Activity, Stars, Downloads ohne Text-Labels
- **Fixed Layout** - 420px Höhe, Chat-Button immer unten
- **Tool-Icons** - Search, Code, FileText, Trello statt Namen
- **Full Model Display** - Kompletter Modellname mit Tooltip
- **Action Buttons** - Edit/Delete in Top-Right Corner

### Diagonal Shine Effect
**Spezifikationen:**
- **400ms Hover Delay** - Verhindert Trigger bei schnellem Überfahren
- **1.2s Animation** - Smooth diagonal sweep von oben-links nach unten-rechts
- **12px Blur** - Weiche Kanten für Premium-Look
- **GPU-accelerated** - 60fps Performance
- **Kein Reverse** - Instant fade-out beim Mouse Leave

### Agent Details Modal
**Tabs:**
1. **Overview** - Agent-Info, Config, Tools
2. **Analytics** - Success Rate, Response Times, Token Breakdown
3. **Tool Usage** - Statistiken welche Tools wie oft genutzt wurden
4. **Scheduled Runs** - Execution History mit expandable Details (nur für Scheduled Agents)

**Analytics:**
- Total Runs, Success Rate, Avg Response Time
- Token Tracking: Prompt Tokens + Completion Tokens
- Visibility-based Access: Private (nur Owner), Public/Team (aggregiert)

---

## 🕐 Scheduled Agents erstellen

### Schritt 1: Agent konfigurieren
1. Gehe zu **Agent Hub** (`/agents`)
2. Klick **"Create Agent"**
3. **Configuration Tab:**
   - Name: z.B. "Daily Weather Report"
   - Model: claude-3-5-sonnet-20241022
   - System Prompt: "Erstelle einen Wetterbericht für Gelnhausen"
   - Temperature: 0.7

### Schritt 2: Tools auswählen
4. **Tools Tab:**
   - ✅ Web Search (für aktuelle Daten)
   - ✅ Knowledge Base (optional)

### Schritt 3: Schedule konfigurieren
5. **Schedule Tab:**
   - Trigger Type: **Scheduled** (statt Manual)
   - Preset auswählen:
     - Hourly: `0 * * * *`
     - Daily at 9 AM: `0 9 * * *`
     - Weekly (Monday): `0 9 * * 1`
     - Monthly (1st): `0 9 1 * *`
     - Weekdays: `0 9 * * 1-5`
     - **Custom**: Eigene Cron-Expression
   - Next Run Preview wird angezeigt

6. Klick **"Create Agent"**

### Was passiert?
- Agent wird in DB gespeichert mit Schedule
- Backend registriert Agent bei Celery Beat
- `next_scheduled_run` wird berechnet
- Schedule Badge erscheint auf Agent Card
- Celery Beat führt Agent zur geplanten Zeit aus
- `last_scheduled_run` wird nach Ausführung aktualisiert

---

## 📊 Scheduled Runs anzeigen

### Via Agent Details Modal
1. Klick auf Agent Card
2. **Scheduled Runs Tab** öffnen
3. Siehe Liste aller Executions:
   - Status (Pending/Running/Completed/Failed)
   - Input (System Prompt)
   - Response (expandable)
   - Execution Time
   - Tools Used

### Via API
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/custom-agents/{agent_id}/scheduled-runs?limit=20
```

**Response:**
```json
{
  "runs": [
    {
      "id": "uuid",
      "status": "completed",
      "input_text": "Erstelle einen Wetterbericht...",
      "response": "Das Wetter in Gelnhausen heute...",
      "executed_at": "2026-02-18T22:00:00Z",
      "response_time": 2.5,
      "tools_used": ["web_search"]
    }
  ]
}
```

---

## 📈 Analytics & Token Tracking

### Token-Zählung
**Implementierung:**
- **tiktoken** Library für präzise Counts
- **Encoding**: cl100k_base (default), o200k_base (gpt-4o)
- **Berechnung**:
  - Prompt Tokens: System Prompt + User Input
  - Completion Tokens: Agent Response
  - Total: Prompt + Completion

**Warum wichtig?**
- Kosten-Tracking für API-Calls
- Performance-Analyse
- Prompt-Optimierung

### Analytics API
```bash
# Summary Stats
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analytics/agents/{agent_id}/summary

# Response:
{
  "total_runs": 13,
  "success_rate": 100.0,
  "avg_response_time": 2.3,
  "total_tokens": 1252,
  "prompt_tokens": 654,
  "completion_tokens": 598
}
```

### Visibility-based Access
- **Private Agents**: Nur Owner sieht eigene Analytics
- **Public/Team Agents**: Aggregierte Daten aller User
- Implementiert via SQL Filter in `get_summary_stats()`

---

## 🎯 Agent 1: Task Creator (Legacy)

### Was macht er?
Analysiert freien Text und erstellt strukturierte Board-Items.

### Wie benutzen?

**Option A: Im Board**
1. Klick auf **"✨ AI Task Creator"** Button (oben rechts)
2. Text eingeben, z.B.:
   ```
   Wir müssen die Login-Seite überarbeiten. 
   Die Passwort-Validierung ist zu schwach und 
   es fehlt ein "Forgot Password" Link.
   ```
3. **"Analysieren"** klicken
4. Warten (Live-Logs werden angezeigt)
5. **Preview** checken und bestätigen
6. Items werden zum Board hinzugefügt

**Option B: Per API**
```bash
curl -X POST http://localhost:8000/api/agents/task_creator/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJECT_ID",
    "data": {
      "text": "Bug: Login button is not working on mobile"
    }
  }'
```

### Was kommt raus?
```json
{
  "items": [
    {
      "type": "bug",
      "title": "Fix Login Button on Mobile",
      "description": "Login button is not working on mobile devices",
      "priority": "high",
      "acceptance_criteria": "- Button is clickable\n- Works on iOS/Android"
    }
  ]
}
```

---

## 💬 Agent 2: Chat Agent (Legacy)

### Was macht er?
Beantwortet Fragen über dein Board mit Kontext-Bewusstsein.

### Wie benutzen?

**Im Board:**
1. Klick auf **💬 Chat Widget** (unten rechts)
2. Frage stellen, z.B.:
   - "Wie viele Tasks sind offen?"
   - "Zeig mir alle Bugs"
   - "Was sind die High-Priority Items?"
   - "Erstelle einen Task: User Profil designen"
3. Agent antwortet mit Statistiken + kann Items erstellen/updaten

**Per API:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJECT_ID",
    "message": "How many tasks are in review?"
  }'
```

### Beispiel-Konversation:
```
Du: Wie viele Tasks habe ich?
Bot: You have 2 task(s) in your project.

Du: Welche sind High Priority?
Bot: Found 1 high priority items: "Fix Login Bug"

Du: Erstelle Task: Add Dark Mode
Bot: ✓ Created task "Add Dark Mode" in backlog
```

---

## 📅 Agent 3: Daily Summary (Legacy)

### Was macht er?
Läuft täglich um 9:00 Uhr und erstellt eine Zusammenfassung.

### Wie benutzen?

**Automatisch:**
- Läuft von selbst via Celery Beat
- Cron: `0 9 * * *` (jeden Tag 9:00 UTC)

**Manuell starten:**
1. Gehe zu **Agent Hub** (`/agents`)
2. Finde "Daily Summary Agent"
3. Klick **"Run Now"**
4. Siehe Live-Logs

**Per API:**
```bash
curl -X POST http://localhost:8000/api/agents/daily_summary/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJECT_ID",
    "data": {}
  }'
```

### Was kommt raus?
```json
{
  "summary": {
    "total_items": 10,
    "open_items": 7,
    "completed_today": 2,
    "high_priority_count": 3
  }
}
```

---

## 🚀 Echte AI aktivieren (Optional)

### Schritt 1: API Key holen

**Option A: Anthropic (empfohlen)**
- Gehe zu: https://console.anthropic.com/
- Erstelle API Key
- Modell: Claude Sonnet 4

**Option B: OpenAI**
- Gehe zu: https://platform.openai.com/api-keys
- Erstelle API Key
- Modell: GPT-4

### Schritt 2: .env bearbeiten

```bash
# In /home/ml/playground/langchain-01/.env

# Für Anthropic:
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
LLM_PROVIDER=anthropic

# ODER für OpenAI:
OPENAI_API_KEY=sk-xxx...
LLM_PROVIDER=openai
```

### Schritt 3: Backend neustarten

```bash
docker compose restart backend celery_worker
```

### Was ändert sich?

**VORHER (Rule-Based):**
- Pattern-Matching
- Einfache Logik
- Schnell, aber nicht kreativ

**NACHHER (AI-Powered):**
- Echtes Verständnis
- Kreative Vorschläge
- Bessere Acceptance Criteria
- Intelligente Task-Breakdown
- Natürliche Konversationen

---

## 🧪 Testen ohne API-Keys

**Du kannst JETZT schon alles testen!**

### Test 1: Task Creator
```
Text: "Wir brauchen eine Suche für das Dashboard"

Ergebnis:
- Type: story
- Title: "Add Search to Dashboard"
- Priority: medium (automatisch geschätzt)
```

### Test 2: Chat
```
Frage: "How many tasks?"
Antwort: "You have X task(s)" (zählt DB Items)
```

### Test 3: Daily Summary
```
Manuell starten in Agent Hub
→ Zeigt Stats aller Items
```

---

## 📈 Agent Hub nutzen

### Zugriff:
**Sidebar → Agent Hub** oder `http://localhost:5173/agents`

### Features:
- ✅ **Übersicht** aller Agenten
- ✅ **Live Status** (Idle/Running/Error)
- ✅ **Run History** (letzte 20 Runs)
- ✅ **Manual Trigger** - "Run Now" Button
- ✅ **Live Logs** - Streaming Terminal-Output
- ✅ **Stats** - Success Rate, Total Runs

### Was du siehst:

```
┌─────────────────────────────────────────┐
│ Task Creator                            │
│ Status: Idle                            │
│ Last Run: 2 minutes ago (Success)       │
│ Stats: 5 runs, 80% success              │
│ [Run Now]                               │
└─────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Agent startet nicht?
```bash
# Check Celery Worker logs
docker logs devflow-celery_worker --tail 50

# Check ob Agents registriert sind
curl http://localhost:8000/api/agents | jq
```

### Keine Live-Logs?
- Refresh Browser (Polling alle 5s)
- Check WebSocket Endpoint: `ws://localhost:8000/api/agents/ws/{run_id}`

### Agent Run failed?
- Agent Hub → Click auf Agent → Run History
- Siehe Error Message
- Check Backend Logs: `docker logs devflow-backend --tail 100`

---

## 💡 Best Practices

### Task Creator
✅ **Gute Inputs:**
- "Bug: Login button not working on Safari"
- "Story: Add user profile page with avatar upload"
- "Epic: Implement payment system with Stripe"

❌ **Schlechte Inputs:**
- "fix it" (zu vage)
- "" (leer)

### Chat Agent
✅ **Gute Fragen:**
- "How many bugs do we have?"
- "Show me high priority items"
- "Create task: Add footer"

❌ **Schlechte Fragen:**
- "asdfgh" (kein Kontext)

---

## 🎯 Nächste Schritte

1. **Jetzt testen** (ohne API-Keys):
   - Task Creator mit Beispiel-Text
   - Chat ein paar Fragen stellen
   - Daily Summary manuell triggern

2. **Optional: AI aktivieren**:
   - API Key holen
   - .env bearbeiten
   - Backend restart

3. **Eigene Agenten bauen**:
   - Copy template aus `task_creator.py`
   - In `registry.register()` eintragen
   - Backend restart

---

Viel Spaß! 🚀

---

## 🎨 UI Guide - Agent Hub

### Agent Card Features

**Card Layout:**
```
┌────────────────────────────────────────────┐
│  🌤️  Weather Bot          [🔒 Private]    │ ← Icon + Name + Visibility
│      Fetches daily weather forecasts       │ ← 2-line Description
│                                             │
│  🕐 Scheduled: Next run in 2h 15m          │ ← Schedule Badge (if scheduled)
│  ─────────────────────────────────────────  │
│  📊 13  ⭐ 0  |  🔍 💻                    │ ← Stats + Tool Icons
│  claude-3-5-sonnet-20241022                │ ← Model Badge
│                                             │
│  [💬 Chat]                                 │ ← Always at bottom
└────────────────────────────────────────────┘
      ↑ Hover: Diagonal shine effect (400ms delay)
```

**Hover Effects:**
- **400ms Delay** - Triggert nur bei intentionalem Hover
- **Diagonal Shine** - Eleganter Lichtstrahl von oben-links nach unten-rechts
- **1.2s Animation** - Smooth, nicht hektisch
- **Action Buttons** - Edit/Delete erscheinen in Top-Right Corner

**Stats Explained:**
- 📊 **Activity Icon** - Anzahl der Runs
- ⭐ **Star Icon** - Star Count (für Public Agents)
- 📥 **Download Icon** - Install Count (Marketplace only)
- 🔍💻📄🗂️ **Tool Icons** - Enabled Tools (max 4, dann "+X")

### Agent Details Modal

**Öffnen:**
- Klick auf Agent Card
- Oder: Edit → View Details

**Tabs:**

1. **📋 Overview**
   - Agent Name, Icon, Description
   - Model, Temperature, Max Tokens
   - System Prompt
   - Enabled Tools (Badges)
   - Visibility & Owner
   - Create/Update Timestamps

2. **📊 Analytics**
   - Total Runs
   - Success Rate (%)
   - Average Response Time (ms)
   - Total Tokens Used
   - Prompt Tokens
   - Completion Tokens
   - Chart: Runs over time (if data available)

3. **🔧 Tool Usage**
   - List of all tools with:
     - Tool Name
     - Usage Count
     - Success Rate
     - Progress Bar visualization

4. **🕐 Scheduled Runs** (nur für Scheduled Agents)
   - Execution History Table:
     - Status (✅ Completed, ❌ Failed, ⏳ Pending, ▶️ Running)
     - Input Text
     - Response (expandable)
     - Execution Time
     - Tools Used
     - Timestamp
   - Click to expand response details
   - Filter/Search (planned)

---

## 🛠️ Troubleshooting

### Scheduled Agent läuft nicht?

**1. Check Celery Worker:**
```bash
docker logs devflow-celery_worker --tail 50

# Sollte zeigen:
# "Registered custom scheduled agent: <agent_name>"
```

**2. Check Celery Beat:**
```bash
docker logs devflow-celery_beat --tail 50

# Sollte zeigen:
# "Scheduler: Sending due task custom-agent-<agent_id>"
```

**3. Check Schedule in DB:**
```bash
docker exec devflow-backend python -c "
from app.database import SessionLocal
from app.models.custom_agent import CustomAgent
db = SessionLocal()
agents = db.query(CustomAgent).filter_by(trigger='scheduled').all()
for a in agents:
    print(f'{a.name}: {a.schedule} (next: {a.next_scheduled_run})')
"
```

**4. Manual Trigger Test:**
```bash
curl -X POST http://localhost:8000/api/custom-agents/{agent_id}/trigger \
  -H "Authorization: Bearer $TOKEN"
```

### Token Count zeigt 0?

**Mögliche Ursachen:**
- Agent nicht mit `sync_agent_runner.py` ausgeführt (nutzt alten Runner)
- tiktoken nicht installiert → Check: `docker exec devflow-backend pip list | grep tiktoken`
- Agent-Run failed bevor Tokens gezählt werden konnten

**Fix:**
```bash
# Install tiktoken im Backend
docker exec devflow-backend pip install tiktoken

# Restart Backend
docker compose restart backend celery_worker
```

### Scheduled Runs Tab leer?

**Checklist:**
- ✅ Agent hat `trigger='scheduled'`?
- ✅ Agent wurde mindestens 1x ausgeführt?
- ✅ API Endpoint korrekt: `/api/custom-agents/{id}/scheduled-runs`?
- ✅ Frontend Service importiert: `scheduledRunsService`?

**Test API direkt:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/custom-agents/{agent_id}/scheduled-runs
```

### Shine Effect funktioniert nicht?

**Häufige Probleme:**
- Browser-Cache → Hard Refresh (Ctrl+Shift+R)
- CSS nicht geladen → Check Browser DevTools Network Tab
- React State Bug → Check Console für Errors

**Sollte sein:**
- Hover über Card → 400ms Delay → Diagonal Shine appears
- Leave Card → Instant fade-out

---

## 🚀 Best Practices

### Scheduled Agents

**✅ Gut:**
- System Prompts mit klarem Output-Format
- Schedule sinnvoll wählen (nicht jede Minute!)
- Web Search für aktuelle Daten aktivieren
- Error Handling in Prompt erwähnen

**❌ Vermeiden:**
- Zu komplexe Prompts (timeout risk)
- Zu häufige Schedules (API-Kosten!)
- Tools aktivieren die nicht gebraucht werden

**Beispiel guter Prompt:**
```
Du bist ein Wetter-Bot. Hole das aktuelle Wetter für Gelnhausen 
via Web Search und erstelle eine kurze Zusammenfassung.

Format:
- Temperatur
- Bedingungen
- Empfehlung (Jacke ja/nein)

Falls Fehler: Gib "Wetter nicht verfügbar" zurück.
```

### Token Optimierung

**Tipps:**
- Kurze System Prompts → weniger Prompt Tokens
- `max_tokens` limitieren → verhindert lange Responses
- Temperature niedriger → fokussiertere Antworten (weniger Tokens)
- Knowledge Base: Kleine Chunks → bessere Retrieval, weniger Context

**Token-Kosten vergleichen:**
```
Claude Sonnet 4:
- Prompt: $3 / 1M tokens
- Completion: $15 / 1M tokens

GPT-4o:
- Prompt: $5 / 1M tokens  
- Completion: $15 / 1M tokens
```

---

## 📝 Changelog

### 2026-02-23: Agent Chat Bug Fixes
- 🐛 Fixed: User message not visible after sending (optimistic update added)
- 🐛 Fixed: Long conversations showing oldest 100 messages instead of newest 100
- ✨ `AgentChatPage.tsx`: optimistic cache update before stream starts
- ✨ `conversation_service.py`: query orders DESC + limit, reverses for display

### 2026-02-18: Agent Cards UI & Token Tracking
- ✨ Moderne Card-UI mit Icon-basierten Stats
- ✨ Diagonal Shine Hover Effect (400ms delay, 1.2s animation)
- ✨ Token Tracking mit tiktoken (Prompt + Completion)
- ✨ Scheduled Runs UI mit Execution History
- ✨ Agent Details Modal mit 4 Tabs
- ✨ Visibility-based Analytics Access Control
- 🐛 Fixed: scheduled_runs API path
- 🐛 Fixed: Action buttons positioning

### 2026-02-17: Scheduled Agents Complete
- ✨ Cron-based scheduling mit Presets
- ✨ Next Run Preview
- ✨ Schedule Management UI
- ✨ Celery Beat Integration

### 2026-02-16: Custom Agent Tools
- ✨ Knowledge Base RAG
- ✨ Code Execution in Docker
- ✨ Web Search Tool
- ✨ Board Integration

---

**Viel Erfolg mit deinen Agents! 🚀**

Bei Fragen: Check die [README](README.md) oder [Testing Guide](TESTING-GUIDE.md)
