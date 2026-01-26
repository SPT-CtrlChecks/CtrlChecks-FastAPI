# FastAPI Ollama Service Setup Script
# Sets up Python virtual environment and installs dependencies

Write-Host "Setting up FastAPI Ollama Service..." -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  venv already exists, removing old one..." -ForegroundColor Yellow
    Remove-Item -Path "venv" -Recurse -Force
}

python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "  Virtual environment created" -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "  pip upgraded" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "  Dependencies installed" -ForegroundColor Green
Write-Host ""

# Verify uvicorn installation
Write-Host "Verifying installation..." -ForegroundColor Yellow
$uvicornCheck = uvicorn --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  uvicorn installed: $uvicornCheck" -ForegroundColor Green
} else {
    Write-Host "  WARNING: uvicorn not found in PATH" -ForegroundColor Yellow
    Write-Host "  Try: venv\Scripts\uvicorn.exe --version" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the service:" -ForegroundColor Cyan
Write-Host "  1. Activate virtual environment:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Run the server:" -ForegroundColor White
Write-Host "     uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Yellow
Write-Host ""
Write-Host "Or use Docker:" -ForegroundColor Cyan
Write-Host "  docker build -t fastapi-ollama ." -ForegroundColor Yellow
Write-Host "  docker run -p 8000:8000 fastapi-ollama" -ForegroundColor Yellow
Write-Host ""
