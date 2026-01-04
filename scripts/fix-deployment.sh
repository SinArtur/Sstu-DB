#!/bin/bash
set -e

echo "=== Deployment Fix Script ==="
echo ""

cd ~/opt/Sstu-DB || exit 1

echo "1. Checking current container status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "2. Checking .env file..."
if [ -f .env ]; then
    echo ".env file exists"
    grep -E "DB_|REDIS_" .env | sed 's/PASSWORD=.*/PASSWORD=***/' || echo "No DB/REDIS vars found"
else
    echo "ERROR: .env file not found!"
    exit 1
fi

echo ""
echo "3. Checking database connection from backend container..."
docker compose -f docker-compose.prod.yml exec -T backend timeout 3 bash -c 'echo > /dev/tcp/db/5432' 2>/dev/null && echo "✓ DB port is open" || echo "✗ DB port is closed"

echo ""
echo "4. Checking Redis connection from backend container..."
docker compose -f docker-compose.prod.yml exec -T backend timeout 3 bash -c 'echo > /dev/tcp/redis/6379' 2>/dev/null && echo "✓ Redis port is open" || echo "✗ Redis port is closed"

echo ""
echo "5. Checking if database exists..."
DB_NAME=$(grep "^DB_NAME=" .env | cut -d'=' -f2 || echo "sstudb")
DB_USER=$(grep "^DB_USER=" .env | cut -d'=' -f2 || echo "sstudb_user")
echo "DB_NAME: $DB_NAME"
echo "DB_USER: $DB_USER"

docker compose -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "\l" | grep -q "$DB_NAME" && echo "✓ Database $DB_NAME exists" || {
    echo "✗ Database $DB_NAME does not exist, creating..."
    docker compose -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" || echo "Failed to create database"
}

echo ""
echo "6. Checking backend logs (last 50 lines)..."
docker compose -f docker-compose.prod.yml logs --tail=50 backend | tail -20

echo ""
echo "7. Restarting containers with updated configuration..."
docker compose -f docker-compose.prod.yml down
sleep 5
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "8. Waiting for services to start..."
sleep 30

echo ""
echo "9. Checking container status after restart..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "10. Checking backend logs again..."
docker compose -f docker-compose.prod.yml logs --tail=30 backend

echo ""
echo "11. Final connectivity test..."
docker compose -f docker-compose.prod.yml exec -T backend timeout 3 bash -c 'echo > /dev/tcp/db/5432' 2>/dev/null && echo "✓ DB connection: OK" || echo "✗ DB connection: FAILED"
docker compose -f docker-compose.prod.yml exec -T backend timeout 3 bash -c 'echo > /dev/tcp/redis/6379' 2>/dev/null && echo "✓ Redis connection: OK" || echo "✗ Redis connection: FAILED"

echo ""
echo "=== Script completed ==="

