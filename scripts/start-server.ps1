# Lit-Pick Backend Server Startup Script for Windows
# Handles port cleanup and server startup

param(
    [int]$Port = 5000,
    [int]$RetryCount = 5,
    [int]$RetryDelay = 2
)

Write-Host "🚀 Lit-Pick Backend Server Startup" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if port is available
function Test-PortAvailable {
    param([int]$Port)
    $connections = netstat -ano | Select-String ":$Port" | Select-String "LISTENING"
    return $connections.Count -eq 0
}

# Function to force close port
function Close-Port {
    param([int]$Port)
    Write-Host "Attempting to close port $Port..." -ForegroundColor Yellow
    
    $connections = netstat -ano | Select-String ":$Port" | Select-String "LISTENING"
    if ($connections) {
        foreach ($conn in $connections) {
            $parts = $conn -split '\s+' | Where-Object {$_ -ne ''}
            $processId = $parts[-1]
            Write-Host "Killing process $processId on port $Port..." -ForegroundColor Yellow
            taskkill /PID $processId /F /T 2>$null | Out-Null
        }
    }
}

# Try to close port and retry
$portAvailable = Test-PortAvailable $Port
$attempt = 0

while (-not $portAvailable -and $attempt -lt $RetryCount) {
    $attempt++
    Write-Host "Port $Port not available (attempt $attempt/$RetryCount)" -ForegroundColor Yellow
    Close-Port $Port
    Start-Sleep -Seconds $RetryDelay
    $portAvailable = Test-PortAvailable $Port
}

if ($portAvailable) {
    Write-Host "✅ Port $Port is now available" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting server..." -ForegroundColor Green
    Write-Host ""
    
    # Activate virtual environment and run server
    & .\.venv\Scripts\Activate.ps1
    & python main.py
} else {
    Write-Host "❌ Failed to free port $Port after $RetryCount attempts" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Restart your computer" -ForegroundColor Yellow
    Write-Host "2. Or use a different port: .\start-server.ps1 -Port 8000" -ForegroundColor Yellow
    Write-Host "3. Or manually close the process using: Get-Process | Stop-Process -Force" -ForegroundColor Yellow
}
