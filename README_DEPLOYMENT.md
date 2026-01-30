# FastAPI Ollama - Production Deployment Guide

This guide covers deploying the FastAPI Ollama service to AWS EC2.

## Prerequisites

- AWS EC2 instance (recommended: g4dn.xlarge or larger for GPU support)
- Git repository access
- SSH access to EC2 instance
- Ubuntu 22.04 LTS or later

## Quick Deployment

### Option 1: Using User Data Script (Recommended)

1. **Launch EC2 Instance** with the user data script:
   - Use `infrastructure/scripts/ollama-user-data.sh` as user data
   - Set environment variables:
     - `GIT_REPO_URL`: Your repository URL
     - `GIT_BRANCH`: Branch to clone (default: main)
     - `WORKER_URL`: Worker service URL (optional)

2. **Wait for initialization** (5-10 minutes)

3. **Verify deployment**:
   ```bash
   curl http://YOUR_EC2_IP:8000/health
   ```

### Option 2: Manual Deployment

1. **SSH into EC2 instance**

2. **Clone repository**:
   ```bash
   sudo mkdir -p /opt/fastapi-ollama
   sudo chown ubuntu:ubuntu /opt/fastapi-ollama
   cd /opt/fastapi-ollama
   
   # Clone your repository
   git clone https://github.com/your-org/ctrlchecks-ai-workflow-os.git /tmp/repo
   cp -r /tmp/repo/Fast_API_Ollama/* .
   cp -r /tmp/repo/Fast_API_Ollama/.[^.]* . 2>/dev/null || true
   ```

3. **Set up Python environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your settings
   ```

5. **Install Ollama** (if not already installed):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

6. **Pull models**:
   ```bash
   ollama pull llama3.1:8b
   ollama pull qwen2.5-coder:7b
   ```

7. **Set up systemd services** (see deployment guide for details)

8. **Start services**:
   ```bash
   sudo systemctl start ollama
   sudo systemctl start fastapi-ollama
   ```

## Configuration

### Environment Variables

Edit `/opt/fastapi-ollama/.env`:

```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
PORT=8000

# Worker Service URL (if using worker service)
WORKER_URL=http://localhost:3001

# CORS Configuration
ALLOWED_ORIGINS=https://ctrlchecks.ai,https://app.ctrlchecks.ai

# Request Timeout
TIMEOUT_SECONDS=180.0
```

### Systemd Services

**Ollama Service** (`/etc/systemd/system/ollama.service`):
```ini
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=ubuntu
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=10
Environment="OLLAMA_HOST=0.0.0.0:11434"

[Install]
WantedBy=multi-user.target
```

**FastAPI Service** (`/etc/systemd/system/fastapi-ollama.service`):
```ini
[Unit]
Description=CtrlChecks FastAPI Ollama Service
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/fastapi-ollama
Environment="PATH=/opt/fastapi-ollama/venv/bin:/usr/bin:/usr/local/bin"
EnvironmentFile=/opt/fastapi-ollama/.env
ExecStart=/opt/fastapi-ollama/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Updating the Service

Use the deployment script:

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
# Check service status
sudo systemctl status fastapi-ollama
sudo journalctl -u fastapi-ollama -n 50

# Check Ollama status
sudo systemctl status ollama
ollama list
```

### Port 8000 not accessible

```bash
# Check if service is listening
sudo netstat -tlnp | grep 8000

# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp
```

### Models not found

```bash
# List installed models
ollama list

# Pull missing models
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Ollama models pulled (llama3.1:8b, qwen2.5-coder:7b)
- [ ] Systemd services enabled and running
- [ ] Firewall rules configured
- [ ] Health check endpoint responding
- [ ] CORS configured for production domains
- [ ] Logs being monitored
- [ ] Backup strategy in place

## Security Considerations

1. **Firewall**: Only expose necessary ports (8000 for FastAPI, 11434 for Ollama if needed)
2. **CORS**: Set specific origins in production, not `*`
3. **Authentication**: Consider adding API key authentication for production
4. **HTTPS**: Use a reverse proxy (nginx) with SSL certificates
5. **Environment Variables**: Never commit `.env` files to git

## Monitoring

- Check service logs: `sudo journalctl -u fastapi-ollama -f`
- Check Ollama logs: `sudo journalctl -u ollama -f`
- Health check: `curl http://localhost:8000/health`
- Model list: `curl http://localhost:8000/api/tags`
