#!/bin/bash
# Quick script to update and rebuild frontend only

echo "=== Updating Frontend ==="
cd ~/opt/Sstu-DB

echo ""
echo "1. Pulling latest changes..."
git pull origin main

echo ""
echo "2. Rebuilding frontend..."
docker compose -f docker-compose.prod.yml build frontend

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

