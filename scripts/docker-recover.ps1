# Recover when Docker / docker compose hangs on Windows.
# Run from an elevated PowerShell if force-removal still fails.

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

Write-Host "=== HRMS Docker recovery ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"

Write-Host "`n1) Force-stop HRMS containers (10s timeout each)..." -ForegroundColor Yellow
$names = @("hrms-postgres", "hrms-minio", "hrms-minio-init", "hrms-backend", "hrms-frontend")
foreach ($name in $names) {
    docker rm -f $name --time 10 2>$null
}

Write-Host "`n2) Compose down with short stop timeout..." -ForegroundColor Yellow
docker compose down --remove-orphans --timeout 10 2>$null

Write-Host "`n3) Start fresh stack..." -ForegroundColor Yellow
docker compose up -d postgres minio minio-init

Write-Host "`n4) Status:" -ForegroundColor Yellow
docker compose ps -a

Write-Host "`n5) MinIO init logs:" -ForegroundColor Yellow
docker logs hrms-minio-init 2>&1 | Select-Object -Last 15

Write-Host "`nDone. Verify:" -ForegroundColor Green
Write-Host "  MinIO health: http://127.0.0.1:9000/minio/health/live"
Write-Host "  API storage:  http://127.0.0.1:8000/health/storage"
Write-Host ""
Write-Host "If docker commands still hang, restart Docker Desktop:" -ForegroundColor Magenta
Write-Host "  Docker Desktop tray icon -> Quit Docker Desktop -> start again"
Write-Host "  Then re-run: .\scripts\docker-recover.ps1"
