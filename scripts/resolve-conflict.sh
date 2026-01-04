#!/bin/bash
set -e

echo "=== Resolving git conflict and applying fixes ==="

cd ~/opt/Sstu-DB

echo "1. Stashing local changes..."
git stash

echo ""
echo "2. Pulling latest changes from GitHub..."
git pull origin main

echo ""
echo "3. Checking if stash needs to be applied..."
if git stash list | grep -q "stash@{0}"; then
    echo "Applying stashed changes..."
    git stash pop || echo "No conflicts in stash"
else
    echo "No stashed changes"
fi

echo ""
echo "4. Checking .env configuration..."
if [ -f .env ]; then
    echo "DB_NAME from .env: $(grep '^DB_NAME=' .env | cut -d'=' -f2 || echo 'not set')"
    echo "DB_USER from .env: $(grep '^DB_USER=' .env | cut -d'=' -f2 || echo 'not set')"
else
    echo "ERROR: .env file not found!"
    exit 1
fi

echo ""
echo "5. Ensuring database exists..."
DB_NAME=$(grep "^DB_NAME=" .env | cut -d'=' -f2 || echo "sstudb")
DB_USER=$(grep "^DB_USER=" .env | cut -d'=' -f2 || echo "Sinan")

docker compose -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "\l" 2>/dev/null | grep -q "$DB_NAME" || {
    echo "Creating database $DB_NAME..."
    docker compose -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" || echo "Database might already exist"
}

echo ""
echo "6. Stopping containers..."
docker compose -f docker-compose.prod.yml down

echo ""
echo "7. Pruning networks..."
docker network prune -f

echo ""
echo "8. Starting containers with updated configuration..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "9. Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "10. Checking container status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "11. Checking backend logs (last 50 lines)..."
docker compose -f docker-compose.prod.yml logs --tail=50 backend

echo ""
echo "12. Testing connectivity..."
if docker compose -f docker-compose.prod.yml exec -T backend timeout 3 bash -c 'echo > /dev/tcp/db/5432' 2>/dev/null; then
    echo "✓ Database connection: OK"
else
    echo "✗ Database connection: FAILED"
fi

if docker compose -f docker-compose.prod.yml exec -T backend timeout 3 bash -c 'echo > /dev/tcp/redis/6379' 2>/dev/null; then
    echo "✓ Redis connection: OK"
else
    echo "✗ Redis connection: FAILED"
fi

echo ""
echo "=== Done ==="

