# PowerShell startup script for Lit-Pick
# Starts both backend and frontend

param(
    [switch]$Backend = $false,
    [switch]$Frontend = $false,
    [switch]$Both = $false,
    [switch]$Test = $false,
    [switch]$Help = $false
)

function Show-Help {
    Write-Host @"
Lit-Pick Startup Script

Usage:
    .\start.ps1 [options]

Options:
    -Backend    Start only the backend
    -Frontend   Start only the frontend
    -Both       Start both backend and frontend (default)
    -Test       Run performance tests
    -Help       Show this help message

Examples:
    # Start both
    .\start.ps1

    # Start only backend
    .\start.ps1 -Backend

    # Run tests
    .\start.ps1 -Test

Notes:
    - Make sure .venv is activated
    - Backend runs on port 5000
    - Frontend runs on port 5173
"@
}

if ($Help) {
    Show-Help
    exit 0
}

# If no options specified, default to both
if (-not $Backend -and -not $Frontend -and -not $Test -and -not $Both) {
    $Both = $true
}

$scriptPath = Get-Location

# Check if .venv exists and activate
$venvPath = Join-Path $scriptPath ".venv"
if (Test-Path $venvPath) {
    Write-Host "✅ Found virtual environment" -ForegroundColor Green
    & "$venvPath\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  Virtual environment not found at $venvPath" -ForegroundColor Yellow
}

function Start-Backend {
    Write-Host "`n🚀 Starting Backend (port 5000)..." -ForegroundColor Cyan
    Write-Host "📚 URL: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "📖 Docs: http://localhost:5000/docs" -ForegroundColor Cyan
    Write-Host "`nPress Ctrl+C to stop`n" -ForegroundColor Gray
    
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd $scriptPath; uvicorn main:app --host 0.0.0.0 --port 5000 --reload`""
}

function Start-Frontend {
    Write-Host "`n🎨 Starting Frontend (port 5173)..." -ForegroundColor Cyan
    Write-Host "🌐 URL: http://localhost:5173" -ForegroundColor Cyan
    Write-Host "`nPress Ctrl+C to stop`n" -ForegroundColor Gray
    
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd $scriptPath\LitPick-Ui; npm run dev`""
}

function Run-Tests {
    Write-Host "`n🧪 Running Performance Tests..." -ForegroundColor Cyan
    Write-Host "`nMake sure backend is running first!`n" -ForegroundColor Yellow
    
    Start-Sleep -Seconds 2
    python benchmark.py
}

# Main execution
if ($Backend) {
    Start-Backend
}
elseif ($Frontend) {
    Start-Frontend
}
elseif ($Test) {
    Run-Tests
}
elseif ($Both) {
    Start-Backend
    Start-Sleep -Seconds 3
    Start-Frontend
    
    Write-Host "`n" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host "✅ Lit-Pick is running!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📚 Backend:  http://localhost:5000" -ForegroundColor Cyan
    Write-Host "📖 Docs:     http://localhost:5000/docs" -ForegroundColor Cyan
    Write-Host "🎨 Frontend: http://localhost:5173" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C in any window to stop services" -ForegroundColor Gray
}
