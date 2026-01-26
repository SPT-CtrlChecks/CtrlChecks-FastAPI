# Quick Start Script for FastAPI Ollama Service
# Activates venv and starts the server

Write-Host "Starting FastAPI Ollama Service..." -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Running setup..." -ForegroundColor Yellow
    Write-Host ""
    .\setup.ps1
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "Try running: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

Write-Host "Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Check if Ollama is running
Write-Host "Checking Ollama connection..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Ollama may not be running at http://localhost:11434" -ForegroundColor Yellow
    Write-Host "Start Ollama with: ollama serve" -ForegroundColor Yellow
}
Write-Host ""

# Start the server
Write-Host "Starting FastAPI server on http://0.0.0.0:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
