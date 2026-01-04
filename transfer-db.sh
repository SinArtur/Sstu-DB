#!/bin/bash
# Script to transfer and restore database on server
# This script should be run ON THE SERVER after uploading database_dump.sql

echo "=== Database Restoration Script ==="
echo ""

cd ~/opt/Sstu-DB

if [ ! -f "database_dump.sql" ]; then
    echo "Error: database_dump.sql not found!"
    echo "Please upload it first using: scp database_dump.sql root@144.31.7.222:~/opt/Sstu-DB/"
    exit 1
fi

echo "Found database_dump.sql"
echo ""

echo "1. Checking if backend can connect to database..."
docker compose -f docker-compose.prod.yml exec -T db psql -U Sinan -d sstudb -c "SELECT 1;" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Warning: Cannot connect to database. Make sure fix-docker-network.sh was run first!"
fi

echo ""
echo "2. Dropping existing database and recreating..."
docker compose -f docker-compose.prod.yml exec -T db psql -U Sinan -d postgres <<EOF
DROP DATABASE IF EXISTS sstudb;
CREATE DATABASE sstudb OWNER Sinan;
EOF

echo ""
echo "3. Restoring database from dump..."
docker compose -f docker-compose.prod.yml exec -T db psql -U Sinan -d sstudb < database_dump.sql

echo ""
echo "4. Restarting backend..."
docker compose -f docker-compose.prod.yml restart backend

echo ""
echo "5. Waiting for backend to start..."
sleep 10

echo ""
echo "6. Checking backend logs..."
docker compose -f docker-compose.prod.yml logs --tail=20 backend

echo ""
echo "=== Done ==="
echo "Database has been restored. Check https://polikek.ru to verify."

