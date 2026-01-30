#!/bin/bash
# Production deployment script for FastAPI Ollama service
# Run this script after cloning the repository on AWS EC2

set -e

APP_DIR="/opt/fastapi-ollama"
cd $APP_DIR

echo "=========================================="
echo "FastAPI Ollama Deployment"
echo "=========================================="

# Activate virtual environment
source venv/bin/activate

# Pull latest code (if using git)
if [ -d ".git" ]; then
    echo "Pulling latest code..."
    git pull origin main || git pull origin master || echo "Git pull failed, continuing..."
fi

# Install/update dependencies
echo "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example or env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please update .env file with your configuration"
    elif [ -f "env.example" ]; then
        cp env.example .env
        echo "Please update .env file with your configuration"
    else
        echo "ERROR: .env.example or env.example not found!"
        exit 1
    fi
fi

# Pull Ollama models if needed
echo "Checking Ollama models..."
if ! ollama list | grep -q "llama3.1:8b"; then
    echo "Pulling llama3.1:8b..."
    ollama pull llama3.1:8b
fi

if ! ollama list | grep -q "qwen2.5-coder:7b"; then
    echo "Pulling qwen2.5-coder:7b..."
    ollama pull qwen2.5-coder:7b
fi

# Restart services
echo "Restarting services..."
sudo systemctl restart ollama || echo "Ollama service restart failed"
sleep 5  # Wait for Ollama to start
sudo systemctl restart fastapi-ollama || echo "FastAPI service restart failed"

# Check service status
echo ""
echo "Service Status:"
sudo systemctl status ollama --no-pager -l || true
echo ""
sudo systemctl status fastapi-ollama --no-pager -l || true

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Test the service:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/api/tags"
echo "=========================================="
