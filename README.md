# CtrlChecks Ollama FastAPI Service

FastAPI proxy service for Ollama models. Provides a REST API interface to interact with local Ollama instances.

## Features

- ✅ REST API proxy for Ollama
- ✅ Chat and generate endpoints
- ✅ Model listing
- ✅ Health checks
- ✅ CORS support
- ✅ Environment-based configuration
- ✅ Proper error handling

## Quick Start

### Prerequisites

- Python 3.11+
- Ollama installed and running on `http://localhost:11434`

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file (copy from `env.example`):

```bash
cp env.example .env
```

Then edit `.env` with your settings:

```env
OLLAMA_URL=http://localhost:11434
PORT=8000
WORKER_URL=http://localhost:3001
ALLOWED_ORIGINS=*
TIMEOUT_SECONDS=180.0
```

### Running

```bash
# Development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or use Python directly:

```bash
python main.py
```

## API Endpoints

### Health & Info

- `GET /` - Service information
- `GET /health` - Health check (checks Ollama connection)

### Models

- `GET /api/tags` - List available Ollama models
- `GET /models` - Alias for `/api/tags`

### Chat & Generate

- `POST /api/chat` - Chat with Ollama model
- `POST /api/generate` - Generate text with Ollama model

### Legacy Endpoints

- `POST /run` - Legacy direct prompt endpoint
- `POST /process` - Legacy task-based endpoint

## Example Usage

### List Models

```bash
curl http://localhost:8000/api/tags
```

### Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "stream": false
  }'
```

### Generate

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "prompt": "Write a short story",
    "stream": false
  }'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `PORT` | `8000` | Server port |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins (comma-separated) |
| `TIMEOUT_SECONDS` | `180.0` | Request timeout in seconds |

## Development

### Project Structure

```
Fast_API_Ollama/
├── main.py              # FastAPI application
├── ollama_client.py     # Ollama client wrapper
├── requirements.txt     # Python dependencies
├── env.example          # Environment variable template
├── deploy.sh            # Production deployment script
├── Dockerfile           # Docker configuration
├── README.md            # This file
├── README_DEPLOYMENT.md # Deployment guide
├── PRODUCTION_SETUP.md  # Production checklist
└── tests/               # Test files
```

### Adding New Endpoints

1. Add route handler in `main.py`
2. Use `httpx.AsyncClient` for Ollama requests
3. Handle errors with proper HTTP status codes
4. Update this README

## Production Deployment

### Using systemd

Create `/etc/systemd/system/ollama-proxy.service`:

```ini
[Unit]
Description=CtrlChecks Ollama Proxy
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/ollama-proxy
Environment="PATH=/opt/ollama-proxy/venv/bin"
ExecStart=/opt/ollama-proxy/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable ollama-proxy
sudo systemctl start ollama-proxy
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### "Connection refused" to Ollama

- Ensure Ollama is running: `ollama serve`
- Check `OLLAMA_URL` in `.env` matches your Ollama instance
- Verify Ollama is accessible: `curl http://localhost:11434/api/tags`

### "Model not found"

- Pull the models: `ollama pull llama3.1:8b` and `ollama pull qwen2.5-coder:7b`
- List available models: `ollama list`

### CORS errors

- Update `ALLOWED_ORIGINS` in `.env` with your frontend domain
- Restart the service after changing environment variables

## License

Part of the CtrlChecks AI Workflow Platform.
