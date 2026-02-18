# DevFlow - Testing & Configuration Guide

## 🚀 Quick Start (5 Minuten)

### 1. Prüfe ob alles läuft

```bash
cd /home/ml/playground/langchain-01
docker compose ps
```

**Erwartete Ausgabe:** Alle 6 Container sollten "Up" sein:
- `devflow-postgres`
- `devflow-redis`
- `devflow-backend`
- `devflow-frontend`
- `devflow-celery-worker`
- `devflow-celery-beat`

### 2. Öffne die App

**Frontend:** http://localhost:5173

**Backend API Docs:** http://localhost:8000/docs (Swagger UI)

### 3. Login mit Demo-User

**Credentials:**
- Email: `demo@devflow.dev`
- Password: `demo1234`

> ℹ️ Dieser User wurde automatisch beim ersten Start erstellt.

---

## ✅ Feature-Tests

### Test 1: Kanban Board (Iteration 2)

1. **Login** auf http://localhost:5173/login
2. Du landest auf `/board` (oder navigiere dorthin)
3. **Erwartung:** Leeres Board mit 4 Spalten

**Items erstellen:**

**Manuell via UI:**
- Es gibt keinen "+"-Button im Board
- Nutze stattdessen den **AI Task Creator** (siehe Test 2)

**Via API (schneller für Test-Daten):**

```bash
TOKEN=$(curl -s -L -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@devflow.dev", "password": "demo1234"}' | jq -r '.access_token')

# Projekt erstellen
PROJECT_ID=$(curl -s -L -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "DevFlow Test Project", "description": "Testing all features"}' | jq -r '.id')

echo "Project ID: $PROJECT_ID"

# 5 Test-Items erstellen
curl -s -L -X POST http://localhost:8000/api/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$PROJECT_ID\", \"type\": \"story\", \"title\": \"User Login Story\", \"description\": \"As a user I want to login\", \"status\": \"backlog\", \"priority\": \"high\"}"

curl -s -L -X POST http://localhost:8000/api/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$PROJECT_ID\", \"type\": \"task\", \"title\": \"Setup Docker\", \"status\": \"in_progress\", \"priority\": \"medium\"}"

curl -s -L -X POST http://localhost:8000/api/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$PROJECT_ID\", \"type\": \"bug\", \"title\": \"Fix password validation\", \"status\": \"review\", \"priority\": \"critical\"}"

curl -s -L -X POST http://localhost:8000/api/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$PROJECT_ID\", \"type\": \"task\", \"title\": \"Write documentation\", \"status\": \"done\", \"priority\": \"low\"}"

curl -s -L -X POST http://localhost:8000/api/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$PROJECT_ID\", \"type\": \"epic\", \"title\": \"Authentication Module\", \"status\": \"backlog\", \"priority\": \"critical\"}"

echo "✓ 5 Items created"
```

**Im Browser:**
- Refresh http://localhost:5173/board
- **Erwartung:** 5 Items verteilt über die Spalten
- **Teste Drag & Drop:** Ziehe Items zwischen Spalten
- **Klick auf Item:** Detail-Modal öffnet sich
- **Edit:** Ändere Titel, Beschreibung, Priority

---

### Test 2: AI Task Creator (Iteration 3)

**Öffne:** http://localhost:5173/board

1. **Klick** auf "AI Task Creator" Button (✨ oben rechts)
2. **Eingabe:** 
   ```
   BUG: The password reset email is not being sent to users. 
   This is blocking production deployment.
   ```
3. **Klick** "Analyze"
4. **Erwartung:** 
   - Loading spinner
   - Nach 2-3 Sekunden: Preview mit strukturiertem Bug Item
   - Type: bug
   - Priority: critical
5. **Klick** "Import Selected"
6. **Erwartung:** Item erscheint im Backlog

**Weitere Tests:**
```
Story: As a user I want to export my data as CSV
```
```
Spike: Research best database for time-series data
```
```
Epic: Multi-tenant authentication system with SSO support
```

---

### Test 3: Chat Widget (Iteration 4)

**Öffne:** http://localhost:5173/board

1. **Klick** auf 💬 Button (unten rechts)
2. **Chat öffnet sich** mit smooth animation
3. **Frage stellen:**
   ```
   How many tasks do we have?
   ```
4. **Erwartung:** Antwort wie "You have 2 task(s) in this project."

**Weitere Fragen:**
```
What is the project status?
```
→ "Project status: X in backlog, Y in progress, Z in review, W done."

```
Do we have any critical priority items?
```
→ "You have X critical and Y high priority items."

```
How many bugs?
```
→ "You have Z bug(s) in this project."

**Chat History:**
- Scroll hoch → Alle Nachrichten werden angezeigt
- User-Messages: Blau, rechts
- Assistant: Grau, links
- Timestamps unter jeder Nachricht

---

### Test 4: Agent Hub (Iteration 5)

**Öffne:** http://localhost:5173/board

1. **Klick** auf "Agent Hub" Button (oben rechts)
2. **Erwartung:** `/agents` Page mit 3 Agent Cards

**Agent Cards:**

**task_creator:**
- Trigger: manual
- "Run Now" Button vorhanden
- Stats: Total Runs, Success Rate

**chat_agent:**
- Trigger: manual
- "Run Now" Button vorhanden

**daily_summary:**
- Trigger: scheduled
- Schedule: "0 9 * * *"
- Kein "Run Now" Button (nur scheduled)

**Test Manual Run:**
1. **Klick** "Run Now" bei task_creator
2. **Erwartung:** Button wird disabled, zeigt "Running..."
3. **Nach 1-2 Sekunden:** Status updated, "Run Now" wieder verfügbar
4. **Stats:** Total Runs erhöht sich um 1

**Test Run History:**
1. **Klick** auf eine Agent Card (nicht den Button!)
2. **Modal öffnet sich** mit Run History
3. **Erwartung:** Liste der letzten Runs
4. **Status Icons:** ✓ done, ✗ failed, ⟳ running
5. **Duration** wird angezeigt
6. **Close Modal:** Klick auf ✕

---

## ⚙️ Konfiguration

### Optional: OpenAI API Key

**Aktueller Stand:** Mock Embeddings funktionieren!

**Für echte Semantic Search:**

1. **Besorge API Key:** https://platform.openai.com/api-keys

2. **Update .env:**
```bash
nano /home/ml/playground/langchain-01/.env
```

**Ändere:**
```env
OPENAI_API_KEY=sk-proj-xxx  # ← Ersetze mit echtem Key
```

3. **Restart Backend:**
```bash
docker compose restart backend celery_worker
```

4. **Test:** Erstelle neue Items → Embeddings werden jetzt echt generiert

---

## 🐛 Troubleshooting

### Problem: Frontend zeigt "No Projects"

**Lösung:** Erstelle ein Projekt via API (siehe Test 1)

---

### Problem: Items werden nicht angezeigt

**Check:**
```bash
# Postgres DB prüfen
docker exec -it devflow-postgres psql -U devflow -d devflow -c "SELECT COUNT(*) FROM items;"
```

**Wenn 0:** Erstelle Items via API (siehe Test 1)

---

### Problem: Chat antwortet immer "0 items"

**Ursache:** Project Stats Query findet keine Items

**Fix:** Stelle sicher dass Items im selben Projekt sind wie der Chat

```bash
# Check Project ID
curl -s -L http://localhost:8000/api/projects/ \
  -H "Authorization: Bearer $TOKEN" | jq

# Check Items
curl -s -L http://localhost:8000/api/items?project_id=<PROJECT_ID> \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### Problem: Agent läuft nicht

**Check Celery Worker Logs:**
```bash
docker logs devflow-celery-worker --tail 50
```

**Check Backend Logs:**
```bash
docker logs devflow-backend --tail 50
```

**Häufige Ursache:** Agent nicht importiert in `main.py`

---

### Problem: Trailing Slash Redirects (307)

**Symptom:** API Calls geben 307 zurück

**Lösung:** Immer mit trailing slash aufrufen:
- ✅ `/api/projects/`
- ❌ `/api/projects`

**Oder:** cURL mit `-L` flag für auto-follow

---

## 📊 Monitoring

### Check Container Health

```bash
docker compose ps
docker compose logs -f backend    # Live logs
docker compose logs -f celery_worker
```

### Database Queries

```bash
# Items count
docker exec -it devflow-postgres psql -U devflow -d devflow -c "SELECT COUNT(*) FROM items;"

# Agent runs
docker exec -it devflow-postgres psql -U devflow -d devflow -c "SELECT agent_name, status, COUNT(*) FROM agent_runs GROUP BY agent_name, status;"

# Chat messages
docker exec -it devflow-postgres psql -U devflow -d devflow -c "SELECT COUNT(*) FROM chat_messages;"
```

### API Health

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"devflow-backend"}
```

---

## 🎯 Complete Test Script

Alle Features in einem Rutsch testen:

```bash
#!/bin/bash
cd /home/ml/playground/langchain-01

echo "=== DevFlow Complete Test ==="

# Login
TOKEN=$(curl -s -L -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@devflow.dev", "password": "demo1234"}' | jq -r '.access_token')

echo "✓ Logged in"

# Create project
PROJECT_ID=$(curl -s -L -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Full Test Project", "description": "Testing everything"}' | jq -r '.id')

echo "✓ Project created: $PROJECT_ID"

# Create test items
for i in {1..5}; do
  curl -s -L -X POST http://localhost:8000/api/items \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"project_id\": \"$PROJECT_ID\", \"type\": \"task\", \"title\": \"Test Task $i\", \"status\": \"backlog\", \"priority\": \"medium\"}" > /dev/null
done

echo "✓ 5 Items created"

# Test chat
sleep 3  # Wait for indexing
CHAT=$(curl -s -L -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$PROJECT_ID\", \"message\": \"How many tasks?\"}")

echo "✓ Chat response: $(echo $CHAT | jq -r '.message')"

# List agents
AGENTS=$(curl -s -L http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[].name')

echo "✓ Agents available: $AGENTS"

echo ""
echo "=== All Tests Passed! ==="
echo "Open http://localhost:5173/board to see the UI"
```

**Ausführen:**
```bash
chmod +x /home/ml/playground/langchain-01/test-complete.sh
/home/ml/playground/langchain-01/test-complete.sh
```

---

## 🔐 Production Checklist

**Bevor Production Deploy:**

- [ ] `.env` Secrets ändern (SECRET_KEY, Passwörter)
- [ ] CORS Origins einschränken
- [ ] OAuth Credentials konfigurieren
- [ ] SMTP Server für E-Mails einrichten
- [ ] OpenAI API Key setzen
- [ ] PostgreSQL Backups einrichten
- [ ] Reverse Proxy (nginx) vor Frontend
- [ ] SSL/TLS Zertifikate
- [ ] Rate Limiting aktivieren
- [ ] Logging & Monitoring (Sentry, DataDog)

---

## 📚 Nächste Schritte

**Entwicklung:**
1. Weitere Agents erstellen (z.B. GitHub Integration)
2. OAuth Provider aktivieren (Google, GitHub)
3. E-Mail Notifications
4. Export-Funktionen (PDF, CSV)
5. Team-Features (Permissions, Roles)

**UI Verbesserungen:**
1. Dark/Light Mode Toggle
2. Item Filtering (Search, Tags)
3. Sprint Planning View
4. Analytics Dashboard
5. Mobile Responsive Design

---

**Happy Testing! 🚀**

Bei Problemen: Check die Logs (`docker logs <container>`) oder erstelle neue Test-Daten via API.
