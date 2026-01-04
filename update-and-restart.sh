#!/bin/bash
# Script to update code from GitHub and restart services

echo "=== Updating code and restarting services ==="
cd ~/opt/Sstu-DB

echo ""
echo "1. Pulling latest changes from GitHub..."
git pull origin main

echo ""
echo "2. Rebuilding backend image..."
docker compose -f docker-compose.prod.yml build backend

echo ""
echo "3. Restarting all services..."
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "4. Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "5. Checking container status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "6. Checking backend logs..."
docker compose -f docker-compose.prod.yml logs --tail=30 backend

echo ""
echo "=== Done ==="
echo "Visit https://polikek.ru/admin/ to check Django admin"

