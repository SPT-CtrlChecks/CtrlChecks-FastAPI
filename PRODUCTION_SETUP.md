# FastAPI Ollama - Production Setup Checklist

## Pre-Deployment Checklist

### 1. Repository Setup
- [ ] Repository is accessible (public or SSH keys configured)
- [ ] Fast_API_Ollama directory contains all necessary files:
  - [ ] `main.py`
  - [ ] `ollama_client.py`
  - [ ] `requirements.txt`
  - [ ] `.env.example`
  - [ ] `Dockerfile` (if using Docker)
  - [ ] `deploy.sh`

### 2. Environment Configuration
- [ ] `.env.example` file exists with all required variables
- [ ] Production `.env` values prepared:
  - [ ] `OLLAMA_URL` (default: `http://localhost:11434`)
  - [ ] `PORT` (default: `8000`)
  - [ ] `WORKER_URL` (if using worker service)
  - [ ] `ALLOWED_ORIGINS` (production domains, not `*`)
  - [ ] `TIMEOUT_SECONDS` (default: `180.0`)

### 3. AWS EC2 Instance
- [ ] Instance type selected (g4dn.xlarge or larger for GPU)
- [ ] Security group configured:
  - [ ] Port 8000 open (FastAPI)
  - [ ] Port 11434 open (Ollama, if needed externally)
  - [ ] SSH access (port 22)
- [ ] Key pair created and downloaded
- [ ] IAM role with necessary permissions (if using S3, CloudWatch, etc.)

## Deployment Steps

### Step 1: Launch EC2 Instance

**Using User Data Script (Automated):**

1. Launch EC2 instance
2. In "Advanced details" → "User data", paste the contents of:
   `infrastructure/scripts/ollama-user-data.sh`
3. Set environment variables (if needed):
   - `GIT_REPO_URL`: Your repository URL
   - `GIT_BRANCH`: Branch to clone (default: main)
   - `WORKER_URL`: Worker service URL (optional)

**Manual Launch:**

1. Launch EC2 instance
2. SSH into instance
3. Follow manual deployment steps below

### Step 2: Manual Deployment (if not using user data)

```bash
# 1. Install dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv git curl

# 2. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 3. Create application directory
sudo mkdir -p /opt/fastapi-ollama
sudo chown ubuntu:ubuntu /opt/fastapi-ollama
cd /opt/fastapi-ollama

# 4. Clone repository
REPO_DIR="/tmp/ctrlchecks-repo"
git clone https://github.com/your-org/ctrlchecks-ai-workflow-os.git $REPO_DIR

# 5. Copy Fast_API_Ollama files
cp -r $REPO_DIR/Fast_API_Ollama/* .
cp -r $REPO_DIR/Fast_API_Ollama/.[^.]* . 2>/dev/null || true

# 6. Set up Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 7. Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# 8. Pull Ollama models
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b

# 9. Set up systemd services (see deployment guide)

# 10. Start services
sudo systemctl start ollama
sudo systemctl start fastapi-ollama
```

### Step 3: Verify Deployment

```bash
# Check Ollama
ollama list
curl http://localhost:11434/api/tags

# Check FastAPI
curl http://localhost:8000/health
curl http://localhost:8000/api/tags

# Check services
sudo systemctl status ollama
sudo systemctl status fastapi-ollama
```

## Post-Deployment

### 1. Security Hardening
- [ ] Update `.env` with production values
- [ ] Set specific CORS origins (not `*`)
- [ ] Configure firewall rules
- [ ] Set up SSL/HTTPS (nginx reverse proxy)
- [ ] Consider API key authentication

### 2. Monitoring
- [ ] CloudWatch agent installed and configured
- [ ] Logs being collected
- [ ] Health checks configured
- [ ] Alarms set up for service failures

### 3. Backup & Recovery
- [ ] Backup strategy for `.env` file
- [ ] Document recovery procedures
- [ ] Test restore process

## Updating the Service

```bash
cd /opt/fastapi-ollama
sudo ./deploy.sh
```

Or manually:

```bash
cd /opt/fastapi-ollama
source venv/bin/activate
git pull  # If using git
pip install -r requirements.txt
sudo systemctl restart fastapi-ollama
```

## Troubleshooting

### Service won't start
```bash
sudo journalctl -u fastapi-ollama -n 50
sudo systemctl status fastapi-ollama
```

### Models not found
```bash
ollama list
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

### Port issues
```bash
sudo netstat -tlnp | grep 8000
sudo ufw allow 8000/tcp
```

## Production Models

- **llama3.1:8b** (4.9GB) - General purpose tasks
- **qwen2.5-coder:7b** (4.5GB) - Code generation tasks

Total disk space needed: ~10GB for models + application

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u fastapi-ollama -f`
2. Review deployment guide: `Guide/Fast_API_Ollama/06_Application_Deployment.md`
3. Check README: `Fast_API_Ollama/README.md`
