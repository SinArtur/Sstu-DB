#!/bin/bash
# Скрипт для исправления проблемы с Docker сетью

echo "=== Fixing Docker network issue ==="
cd ~/opt/Sstu-DB

echo ""
echo "1. Checking current DOCKER iptables rules..."
iptables -L DOCKER -n | head -20

echo ""
echo "2. Setting FORWARD policy to ACCEPT..."
iptables -P FORWARD ACCEPT

echo ""
echo "3. Adding specific rules for Docker bridge..."
bridge=$(docker network inspect --format='{{.Id}}' sstu-db_default | cut -c1-12)
echo "Bridge: br-$bridge"
iptables -I FORWARD -i br-$bridge -j ACCEPT
iptables -I FORWARD -o br-$bridge -j ACCEPT

echo ""
echo "4. Restarting backend container..."
docker compose -f docker-compose.prod.yml restart backend
sleep 15

echo ""
echo "5. Testing connectivity from backend..."
docker compose -f docker-compose.prod.yml exec -T backend python - <<'PY'
import socket
for host, port in [("db", 5432), ("redis", 6379)]:
    s = socket.socket()
    s.settimeout(3)
    try:
        s.connect((host, port))
        print(f"{host}:{port} ✓ OK")
    except Exception as e:
        print(f"{host}:{port} ✗ FAIL -> {e}")
    finally:
        s.close()
PY

echo ""
echo "6. Checking backend logs..."
docker compose -f docker-compose.prod.yml logs --tail=20 backend

echo ""
echo "7. Checking container status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=== Done ==="
echo "If connections are OK, the site should be working now."
echo "Visit https://polikek.ru to check."

