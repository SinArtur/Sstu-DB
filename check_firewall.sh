#!/bin/bash
# Скрипт для проверки firewall и портов

echo "=== Проверка UFW ==="
sudo ufw status verbose

echo ""
echo "=== Проверка iptables (INPUT chain) ==="
sudo iptables -L INPUT -n -v | head -20

echo ""
echo "=== Проверка iptables (правила для портов 80 и 443) ==="
sudo iptables -L INPUT -n -v | grep -E "80|443" || echo "Правил для портов 80/443 не найдено в INPUT"

echo ""
echo "=== Проверка открытых портов ==="
sudo netstat -tlnp | grep -E ':(80|443)' || ss -tlnp | grep -E ':(80|443)'

echo ""
echo "=== Проверка, слушает ли nginx ==="
sudo netstat -tlnp | grep nginx || ss -tlnp | grep nginx

echo ""
echo "=== Проверка внешнего IP ==="
curl -s ifconfig.me
echo ""

echo ""
echo "=== Проверка доступности порта 80 извне (если возможно) ==="
# Это может не сработать, но попробуем
timeout 2 bash -c "</dev/tcp/$(curl -s ifconfig.me)/80" 2>/dev/null && echo "Порт 80 доступен извне" || echo "Не удалось проверить порт 80 извне"

