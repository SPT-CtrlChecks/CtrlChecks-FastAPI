from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
import time

app = FastAPI(title="CtrlChecks AI Backend")

# -------------------------------------------------
# CORS CONFIG
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# CONSTANTS
# -------------------------------------------------
OLLAMA_URL = "http://localhost:11434"

# -------------------------------------------------
# REQUEST MODELS
# -------------------------------------------------
class RunRequest(BaseModel):
    prompt: str
    model: str = "qwen2.5:3b"
    timeout: int = 180

class ProcessRequest(BaseModel):
    task: str
    input: str
    model: str = "qwen2.5:3b"
    timeout: int = 180

class ChatRequest(BaseModel):
    model: str = "qwen2.5:3b"
    messages: list
    stream: bool = False
    options: dict = None

# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.get("/")
def root():
    return {
        "service": "CtrlChecks AI Backend",
        "status": "running",
        "endpoints": {
            "/": "Root",
            "/health": "Health check",
            "/run": "Direct LLM prompt",
            "/process": "Task-based processing",
            "/api/chat": "Ollama Chat Proxy",
            "/api/tags": "List models",
            "/api/generate": "Generate endpoint"
        }
    }

@app.get("/health")
def health():
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=10.0)
        ollama_status = "running" if response.status_code == 200 else "down"
    except:
        ollama_status = "down"
    
    return {
        "status": "healthy",
        "ollama": ollama_status,
        "timestamp": time.time()
    }

# -------------------------------------------------
# OLLAMA PROXY ENDPOINTS
# -------------------------------------------------
@app.get("/api/tags")
async def list_models_proxy():
    """Proxy for ollama list"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama proxy error: {str(e)}")

@app.get("/models")
async def list_models_alias():
    return await list_models_proxy()

@app.post("/api/chat")
async def chat_proxy(request: Request):
    """Proxy for ollama chat"""
    try:
        body = await request.json()
        print(f"Received chat request for model: {body.get('model')}")
        
        # Set longer timeout for generation
        timeout = 120.0 if body.get('stream', False) else 180.0
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=body)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

@app.post("/api/generate")
async def generate_proxy(request: Request):
    """Proxy for ollama generate"""
    try:
        body = await request.json()
        print(f"Received generate request for model: {body.get('model')}")
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json=body)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

# -------------------------------------------------
# LEGACY ENDPOINTS (for compatibility)
# -------------------------------------------------
@app.post("/run")
async def run(req: RunRequest):
    """Legacy endpoint - use /api/generate instead"""
    try:
        async with httpx.AsyncClient(timeout=req.timeout) as client:
            payload = {
                "model": req.model,
                "prompt": req.prompt,
                "stream": False
            }
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            
            result = resp.json()
            return {
                "success": True,
                "model": req.model,
                "response": result.get("response", ""),
                "latency": result.get("total_duration", 0) / 1_000_000_000  # Convert ns to seconds
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process(req: ProcessRequest):
    """Legacy task-based endpoint"""
    try:
        # Build prompt from task
        prompt = f"""
Task: {req.task}

Input:
{req.input}

Please provide the requested output.
"""
        
        async with httpx.AsyncClient(timeout=req.timeout) as client:
            payload = {
                "model": req.model,
                "prompt": prompt,
                "stream": False
            }
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            
            result = resp.json()
            return {
                "success": True,
                "task": req.task,
                "output": result.get("response", ""),
                "model_used": req.model,
                "processing_time": result.get("total_duration", 0) / 1_000_000_000
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
