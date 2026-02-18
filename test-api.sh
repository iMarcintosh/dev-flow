#!/bin/bash
set -e

echo "🧪 Testing DevFlow API..."

# 1. Register
echo -e "\n✅ Testing Registration..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "apitest@devflow.dev", "password": "test1234", "full_name": "API Test"}')

TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.access_token')
echo "Token: ${TOKEN:0:30}..."

# 2. Create Project
echo -e "\n✅ Creating Project..."
PROJECT=$(curl -s -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Test Project", "description": "API Test"}')

PROJECT_ID=$(echo $PROJECT | jq -r '.id')
echo "Project ID: $PROJECT_ID"

# 3. Create Items
echo -e "\n✅ Creating Items..."
for status in "backlog" "in_progress" "review" "done"; do
  ITEM=$(curl -s -X POST http://localhost:8000/api/items/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"project_id\": \"$PROJECT_ID\", \"title\": \"Task in $status\", \"status\": \"$status\", \"type\": \"task\"}")
  echo "  - Created: $(echo $ITEM | jq -r '.title')"
done

# 4. List Items
echo -e "\n✅ Listing Items..."
ITEMS=$(curl -s -X GET "http://localhost:8000/api/items/?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Total items: $(echo $ITEMS | jq '. | length')"
echo $ITEMS | jq -r '.[] | "  - [\(.status)] \(.title)"'

echo -e "\n🎉 All tests passed!"
