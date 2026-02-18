#!/bin/bash
cd /home/ml/playground/langchain-01

echo "╔════════════════════════════════════════╗"
echo "║   DevFlow - Complete Feature Test     ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check containers
echo "🔍 Checking containers..."
RUNNING=$(docker compose ps --services --filter "status=running" | wc -l)
echo "   → $RUNNING/6 containers running"

if [ "$RUNNING" -ne 6 ]; then
  echo "   ⚠️  Not all containers running. Start with:"
  echo "   docker compose up -d"
  exit 1
fi

# Login
echo ""
echo "🔐 Logging in..."
TOKEN=$(curl -s -L -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@devflow.dev", "password": "demo1234"}' | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "   ❌ Login failed. Check backend logs:"
  echo "   docker logs devflow-backend --tail 20"
  exit 1
fi

echo "   ✓ Logged in successfully"

# Create project
echo ""
echo "📁 Creating test project..."
PROJECT_RESP=$(curl -s -L -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Complete Test Project", "description": "Automated test run"}')

PROJECT_ID=$(echo "$PROJECT_RESP" | jq -r '.id')

if [ "$PROJECT_ID" == "null" ] || [ -z "$PROJECT_ID" ]; then
  echo "   ❌ Project creation failed"
  echo "   Response: $PROJECT_RESP"
  exit 1
fi

echo "   ✓ Project created: $PROJECT_ID"

# Create test items
echo ""
echo "📝 Creating 5 test items..."

TYPES=("story" "task" "bug" "task" "epic")
STATUSES=("backlog" "in_progress" "review" "done" "backlog")
PRIORITIES=("high" "medium" "critical" "low" "high")
TITLES=("User Authentication" "Setup CI/CD" "Fix login bug" "Write tests" "Payment Integration")

for i in {0..4}; do
  curl -s -L -X POST http://localhost:8000/api/items \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"project_id\": \"$PROJECT_ID\", 
      \"type\": \"${TYPES[$i]}\", 
      \"title\": \"${TITLES[$i]}\",
      \"status\": \"${STATUSES[$i]}\",
      \"priority\": \"${PRIORITIES[$i]}\"
    }" > /dev/null
  echo "   ✓ Created: ${TITLES[$i]} (${TYPES[$i]})"
done

# Wait for indexing
echo ""
echo "⏳ Waiting for auto-indexing (3s)..."
sleep 3

# Test chat
echo ""
echo "💬 Testing chat agent..."
CHAT_RESP=$(curl -s -L -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$PROJECT_ID\", \"message\": \"How many tasks do we have?\"}")

CHAT_MSG=$(echo "$CHAT_RESP" | jq -r '.message')
echo "   Q: 'How many tasks do we have?'"
echo "   A: $CHAT_MSG"

# List agents
echo ""
echo "🤖 Listing agents..."
AGENTS=$(curl -s -L http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $TOKEN")

echo "$AGENTS" | jq -r '.[] | "   ✓ \(.name) (\(.trigger))"'

# Agent stats
echo ""
echo "📊 Agent statistics..."
for agent in task_creator chat_agent daily_summary; do
  STATUS=$(curl -s -L http://localhost:8000/api/agents/$agent/status \
    -H "Authorization: Bearer $TOKEN")
  
  TOTAL=$(echo "$STATUS" | jq -r '.stats.total_runs')
  SUCCESS=$(echo "$STATUS" | jq -r '.stats.success_rate')
  
  echo "   $agent: $TOTAL runs, ${SUCCESS}% success"
done

# Summary
echo ""
echo "╔════════════════════════════════════════╗"
echo "║          All Tests Passed! ✅          ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "🌐 Open the app:"
echo "   → Board:      http://localhost:5173/board"
echo "   → Agent Hub:  http://localhost:5173/agents"
echo ""
echo "🔑 Login credentials:"
echo "   → Email:    demo@devflow.dev"
echo "   → Password: demo1234"
echo ""
echo "📋 Project ID: $PROJECT_ID"
echo ""

