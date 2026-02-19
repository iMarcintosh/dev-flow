#!/bin/bash
# DevFlow Development Setup Script
# Runs DB migrations and creates a test user.
# Usage: ./scripts/setup-dev.sh

set -e

echo "==> Running database migrations..."
docker compose exec backend alembic upgrade head

echo "==> Creating test user..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@devflow.dev", "password": "test1234", "full_name": "Test User"}')

if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "201" ]; then
  echo "==> Test user created."
elif [ "$RESPONSE" = "400" ]; then
  echo "==> Test user already exists, skipping."
else
  echo "ERROR: Unexpected response $RESPONSE when creating test user." >&2
  exit 1
fi

echo ""
echo "Setup complete!"
echo ""
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "  Test login:"
echo "    Email:    test@devflow.dev"
echo "    Password: test1234"
