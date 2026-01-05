#!/bin/bash
# Quick script to update and rebuild frontend only

echo "=== Updating Frontend ==="
cd ~/opt/Sstu-DB

echo ""
echo "1. Pulling latest changes..."
git pull origin main

echo ""
echo "2. Rebuilding frontend (this may take a while and require sufficient memory)..."
if ! docker compose -f docker-compose.prod.yml build --no-cache frontend; then
    echo ""
    echo "ERROR: Frontend build failed. This is often due to insufficient memory."
    echo "Try one of these solutions:"
    echo "  1. Increase server memory or add swap space"
    echo "  2. Stop other containers: docker compose -f docker-compose.prod.yml stop backend nginx"
    echo "  3. Build with memory limit: docker compose -f docker-compose.prod.yml build --memory=1g frontend"
    exit 1
fi

echo ""
echo "3. Restarting frontend..."
docker compose -f docker-compose.prod.yml restart frontend

echo ""
echo "4. Waiting 10 seconds..."
sleep 10

echo ""
echo "5. Checking frontend status..."
docker compose -f docker-compose.prod.yml ps | grep frontend

echo ""
echo "=== Done ==="
echo "Frontend updated! Clear browser cache (Ctrl+Shift+R) and try again."

