# Git Deployment Guide

This repository is configured for deployment to AWS EC2.

## Repository Information

- **Repository URL**: `https://github.com/SPT-CtrlChecks/CtrlChecks-FastAPI.git`
- **Default Branch**: `main`

## Quick Deployment

### Using User Data Script (Automated)

1. Launch EC2 instance
2. In "Advanced details" → "User data", paste the contents of:
   `infrastructure/scripts/ollama-user-data.sh`
3. The script will automatically:
   - Install Ollama
   - Clone this repository
   - Set up Python environment
   - Install dependencies
   - Pull required models
   - Configure systemd services

### Manual Deployment

```bash
# 1. SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 2. Create application directory
sudo mkdir -p /opt/fastapi-ollama
sudo chown ubuntu:ubuntu /opt/fastapi-ollama
cd /opt/fastapi-ollama

# 3. Clone repository
git clone https://github.com/SPT-CtrlChecks/CtrlChecks-FastAPI.git .

# 4. Set up Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configure environment
cp env.example .env
nano .env  # Edit with your settings

# 6. Install Ollama (if not installed)
curl -fsSL https://ollama.com/install.sh | sh

# 7. Pull models
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b

# 8. Set up systemd services (see deployment guide)

# 9. Start services
sudo systemctl start ollama
sudo systemctl start fastapi-ollama
```

## Updating the Service

```bash
cd /opt/fastapi-ollama
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart fastapi-ollama
```

Or use the deployment script:

```bash
cd /opt/fastapi-ollama
sudo ./deploy.sh
```

## Environment Variables

Copy `env.example` to `.env` and configure:

```env
OLLAMA_URL=http://localhost:11434
PORT=8000
WORKER_URL=http://localhost:3001
ALLOWED_ORIGINS=*
TIMEOUT_SECONDS=180.0
```

## Production Models

- `llama3.1:8b` (4.9GB) - General purpose
- `qwen2.5-coder:7b` (4.5GB) - Code generation

## Verification

```bash
# Check health
curl http://localhost:8000/health

# List models
curl http://localhost:8000/api/tags

# Check services
sudo systemctl status ollama
sudo systemctl status fastapi-ollama
```

## Troubleshooting

See `README_DEPLOYMENT.md` for detailed troubleshooting steps.
