$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Creating Python virtual environment in backend/.venv"
python -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install --upgrade pip
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt

Write-Host "==> Installing frontend dependencies"
Set-Location frontend
npm install
Set-Location $Root

Write-Host "==> Local setup complete"
Write-Host "Run: ./scripts/start-local.ps1"
