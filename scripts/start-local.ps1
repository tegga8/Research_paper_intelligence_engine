$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (!(Test-Path "backend/.venv/Scripts/uvicorn.exe")) {
  Write-Error "Backend environment missing. Run ./scripts/setup-local.ps1 first."
}
if (!(Test-Path "frontend/node_modules")) {
  Write-Error "Frontend dependencies missing. Run ./scripts/setup-local.ps1 first."
}

$backend = Start-Process powershell -PassThru -ArgumentList @(
  "-NoExit", "-Command", "cd '$Root/backend'; . .venv/Scripts/Activate.ps1; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
)
$frontend = Start-Process powershell -PassThru -ArgumentList @(
  "-NoExit", "-Command", "cd '$Root/frontend'; `$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8000'; npm run dev"
)

Write-Host "Backend:  http://127.0.0.1:8000/docs"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Close the opened PowerShell windows to stop the app."
