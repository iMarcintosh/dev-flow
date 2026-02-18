# 🤖 DevFlow Agenten - Komplette Anleitung

## 📊 Aktueller Status

**✅ Alle 3 Agenten sind funktionstüchtig:**

1. **Task Creator** - Text → strukturierte Tasks
2. **Chat Agent** - Board Q&A Chatbot  
3. **Daily Summary** - Scheduled Agent (täglich 9:00 Uhr)

**⚠️ Aktueller Modus: RULE-BASED (ohne echte AI)**
- Agenten funktionieren JETZT schon
- Nutzen Pattern-Matching und Logik
- Keine API-Keys nötig
- Für echte AI: API-Keys hinzufügen (siehe unten)

---

## 🎯 Agent 1: Task Creator

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

## 💬 Agent 2: Chat Agent

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

## 📅 Agent 3: Daily Summary

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
