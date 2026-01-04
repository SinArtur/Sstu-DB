# PowerShell script to migrate database from local to server
$ErrorActionPreference = "Stop"

$serverIP = "144.31.7.222"
$serverUser = "root"
$dumpFile = "database_dump.sql"
$remotePath = "/root/opt/Sstu-DB/"

Write-Host "=== Database Migration Script ===" -ForegroundColor Green
Write-Host ""

# Check if dump exists
if (-not (Test-Path $dumpFile)) {
    Write-Host "Error: database_dump.sql not found!" -ForegroundColor Red
    exit 1
}

$dumpSize = (Get-Item $dumpFile).Length
Write-Host "Found database dump: $([math]::Round($dumpSize/1KB, 2)) KB" -ForegroundColor Yellow

Write-Host ""
Write-Host "To upload and restore the database, run these commands on your server:" -ForegroundColor Cyan
Write-Host ""
Write-Host "# 1) Upload dump file to server (run from Windows):" -ForegroundColor White
Write-Host "scp database_dump.sql ${serverUser}@${serverIP}:${remotePath}" -ForegroundColor Gray
Write-Host ""
Write-Host "# 2) On server, restore the database:" -ForegroundColor White
Write-Host "cd ~/opt/Sstu-DB" -ForegroundColor Gray
Write-Host "docker compose -f docker-compose.prod.yml exec -T db psql -U Sinan -d sstudb < database_dump.sql" -ForegroundColor Gray
Write-Host ""
Write-Host "# 3) Restart backend:" -ForegroundColor White
Write-Host "docker compose -f docker-compose.prod.yml restart backend" -ForegroundColor Gray
Write-Host ""
Write-Host "=== Alternative: Manual steps ===" -ForegroundColor Yellow
Write-Host "If you don't have scp, copy the content of database_dump.sql and create it on the server manually." -ForegroundColor Gray

