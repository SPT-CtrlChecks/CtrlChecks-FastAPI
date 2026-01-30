import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import httpx
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    port: int = 8000
    allowed_origins: str = "*"
    timeout_seconds: float = 180.0
    worker_url: str = "http://localhost:3001"  # Worker service URL
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# OpenAPI tags metadata
tags_metadata = [
    {
        "name": "health",
        "description": "Health check endpoints to verify service and Ollama connectivity.",
    },
    {
        "name": "models",
        "description": "Operations for listing and managing Ollama models.",
    },
    {
        "name": "chat",
        "description": "Chat with Ollama models using conversational interface.",
    },
    {
        "name": "generate",
        "description": "Generate text completions using Ollama models.",
    },
    {
        "name": "legacy",
        "description": "Legacy endpoints for backward compatibility.",
    },
]

app = FastAPI(
    title="CtrlChecks AI Backend",
    description="""
    FastAPI proxy service for Ollama models.
    
    This service provides a REST API interface to interact with local Ollama instances.
    It handles model management, chat interactions, and text generation.
    
    ## Features
    
    * **Model Management**: List and query available Ollama models
    * **Chat Interface**: Conversational AI interactions
    * **Text Generation**: Direct text completion
    * **Health Monitoring**: Service and Ollama connectivity checks
    
    ## Authentication
    
    Currently, this service does not require authentication for local development.
    For production, consider adding API key authentication.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "CtrlChecks Support",
        "url": "https://ctrlchecks.ai",
    },
    license_info={
        "name": "Proprietary",
    },
)

# -------------------------------------------------
# CORS CONFIG
# -------------------------------------------------
origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# CONSTANTS
# -------------------------------------------------
OLLAMA_URL = settings.ollama_url.rstrip("/")
WORKER_URL = settings.worker_url.rstrip("/")

# -------------------------------------------------
# REQUEST MODELS
# -------------------------------------------------
class RunRequest(BaseModel):
    prompt: str
    model: str = "llama3.1:8b"  # Production model for general tasks
    timeout: int = 180

class ProcessRequest(BaseModel):
    task: str
    input: str = None
    image: str = None  # Base64 encoded image for image processing tasks
    model: str = "llama3.1:8b"  # Production model for general tasks
    timeout: int = 180
    sentence_count: int = 5  # For story generation
    steps: int = 2  # For text-to-image (not supported, but kept for compatibility)
    guidance_scale: float = 1.0  # For text-to-image (not supported, but kept for compatibility)

class ChatRequest(BaseModel):
    model: str = "llama3.1:8b"  # Production model for general tasks
    messages: list
    stream: bool = False
    options: dict = None

# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.get(
    "/",
    tags=["health"],
    summary="Service Information",
    description="Get information about the service and available endpoints.",
    response_description="Service information and endpoint list",
)
def root():
    """
    Get service information and available endpoints.
    
    Returns basic information about the service and a list of all available endpoints.
    """
    return {
        "service": "CtrlChecks AI Backend",
        "status": "running",
        "version": "1.0.0",
        "ollama_url": OLLAMA_URL,
        "endpoints": {
            "/": "Root - Service information",
            "/health": "Health check - Verify service and Ollama connectivity",
            "/api/tags": "List models - Get available Ollama models",
            "/api/chat": "Chat - Conversational AI interface",
            "/api/generate": "Generate - Text completion",
            "/run": "Legacy - Direct LLM prompt",
            "/process": "Legacy - Task-based processing",
            "/chatbot": "Proxy - Chatbot endpoint (forwards to worker service)",
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        }
    }

@app.get(
    "/health",
    tags=["health"],
    summary="Health Check",
    description="Check service health and Ollama connectivity.",
    response_description="Health status including Ollama connection status",
)
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
@app.get(
    "/api/tags",
    tags=["models"],
    summary="List Available Models",
    description="Get a list of all available Ollama models installed on the server.",
    response_description="List of models with metadata",
)
async def list_models_proxy():
    """
    List all available Ollama models.
    
    This endpoint proxies the Ollama `/api/tags` endpoint to retrieve
    a list of all models that are currently available for use.
    """
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

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "llama3.1:8b"  # Production model for general tasks
    messages: list[ChatMessage]
    stream: bool = False
    options: dict | None = None


@app.post(
    "/api/chat",
    tags=["chat"],
    summary="Chat with Model",
    description="Send a chat message to an Ollama model and receive a response.",
    response_description="Model response with message content",
)
async def chat_proxy(request: Request):
    """
    Chat with an Ollama model.
    
    Send conversational messages to an Ollama model and receive responses.
    Supports streaming and non-streaming modes.
    
    **Request Body:**
    - `model`: Model name (e.g., "llama3.1:8b" for general tasks, "qwen2.5-coder:7b" for code tasks)
    - `messages`: List of message objects with `role` and `content`
    - `stream`: Whether to stream the response (default: false)
    - `options`: Additional model options (optional)
    
    **Example:**
    ```json
    {
        "model": "llama3.1:8b",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "stream": false
    }
    ```
    """
    try:
        body = await request.json()
        print(f"Received chat request for model: {body.get('model')}")
        
        # Ensure stream is explicitly set to False if not provided
        if 'stream' not in body:
            body['stream'] = False
        
        # Set longer timeout for generation
        timeout = 120.0 if body.get('stream', False) else 180.0
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=body)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            
            # Handle JSON parsing more carefully
            # Read response as text first to handle potential issues
            response_text = resp.text.strip()
            
            try:
                # Try to parse as JSON
                return json.loads(response_text)
            except json.JSONDecodeError as json_err:
                # Log the error for debugging
                logger.warning(f"JSON decode error: {json_err}")
                logger.debug(f"Response text (first 1000 chars): {response_text[:1000]}")
                
                # Try to extract the first valid JSON object if multiple objects exist
                # This can happen if Ollama returns streaming-like data even with stream=false
                try:
                    # Find the first complete JSON object
                    brace_count = 0
                    json_end = -1
                    for i, char in enumerate(response_text):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end > 0:
                        # Extract just the first JSON object
                        first_json = response_text[:json_end]
                        return json.loads(first_json)
                    else:
                        # If we can't find a complete JSON object, raise the original error
                        raise json_err
                except Exception as parse_err:
                    # If all parsing attempts fail, return a more helpful error
                    error_detail = f"Failed to parse Ollama response: {str(json_err)}"
                    if len(response_text) > 0:
                        error_detail += f". Response preview: {response_text[:200]}"
                    raise HTTPException(status_code=500, detail=error_detail)
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(f"Chat proxy error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

@app.post(
    "/api/generate",
    tags=["generate"],
    summary="Generate Text",
    description="Generate text completion using an Ollama model.",
    response_description="Generated text response",
)
async def generate_proxy(request: Request):
    """
    Generate text using an Ollama model.
    
    Send a prompt to an Ollama model and receive a text completion.
    This is a direct text generation endpoint, not conversational.
    
    **Request Body:**
    - `model`: Model name (e.g., "llama3.1:8b" for general tasks, "qwen2.5-coder:7b" for code tasks)
    - `prompt`: Text prompt to generate from
    - `stream`: Whether to stream the response (default: false)
    - `options`: Additional model options (optional)
    
    **Example:**
    ```json
    {
        "model": "llama3.1:8b",
        "prompt": "Write a short story about",
        "stream": false
    }
    ```
    """
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
    """
    Task-based endpoint supporting both text and image processing.
    
    Supports:
    - Text tasks: summarize, translate, extract, sentiment, generate, qa, chat
    - Image tasks: image_caption, story, image_prompt (requires 'image' field)
    """
    try:
        start_time = time.time()
        
        # Image processing tasks require an image
        image_tasks = ["image_caption", "story", "image_prompt"]
        if req.task in image_tasks:
            if not req.image:
                raise HTTPException(status_code=400, detail=f"Image data required for task: {req.task}")
            
            # Vision models not supported - return error
            raise HTTPException(
                status_code=501, 
                detail="Image processing functionality has been removed. Multimodal features are no longer supported. Please use text-based models: llama3.1:8b (general) or qwen2.5-coder:7b (code)."
            )
            
            # Prepare image (remove data URL prefix if present)
            image_base64 = req.image
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            
            # Build prompt based on task
            if req.task == "image_caption":
                prompt = "Describe this image in a short, concise caption."
            elif req.task == "story":
                prompt = f"Describe this image in detail. Include what you see, the mood, colors, atmosphere, and any interesting details. Use {req.sentence_count or 5} sentences."
            elif req.task == "image_prompt":
                prompt = "Describe this image in detail for image generation. Include style, composition, colors, lighting, mood, and technical details. Format as a Stable Diffusion prompt with keywords."
            else:
                prompt = f"Analyze this image and provide information about: {req.task}"
            
            # Prepare messages for vision model
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_base64]
                }
            ]
            
            # Call Ollama vision API
            async with httpx.AsyncClient(timeout=req.timeout) as client:
                payload = {
                    "model": vision_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 300 if req.task == "story" else 150
                    }
                }
                
                resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                
                result = resp.json()
                
                # Extract response from Ollama format
                if "message" in result and "content" in result["message"]:
                    output = result["message"]["content"]
                elif "response" in result:
                    output = result["response"]
                else:
                    output = str(result)
                
                # For image_prompt, enhance with keywords
                if req.task == "image_prompt":
                    output = f"{output}, ultra realistic, cinematic lighting, high detail, sharp focus, 4k, professional photography"
                
                processing_time = time.time() - start_time
                
                return {
                    "success": True,
                    "task": req.task,
                    "output": output.strip(),
                    "model_used": vision_model,
                    "processing_time": round(processing_time, 2)
                }
        
        # Text processing tasks
        else:
            if not req.input:
                raise HTTPException(status_code=400, detail=f"Input text required for task: {req.task}")
            
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
                processing_time = time.time() - start_time
                
                return {
                    "success": True,
                    "task": req.task,
                    "output": result.get("response", ""),
                    "model_used": req.model,
                    "processing_time": round(processing_time, 2)
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing task {req.task}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chatbot")
async def chatbot_proxy(request: Request):
    """
    Proxy endpoint for chatbot - forwards requests to worker service.
    This allows the frontend to call /chatbot on port 8000 (FastAPI)
    and it will be forwarded to the worker service on port 3001.
    """
    try:
        body = await request.json()
        logger.info(f"Proxying chatbot request to worker service at {WORKER_URL}/chatbot")
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{WORKER_URL}/chatbot",
                json=body,
                headers={
                    "Content-Type": "application/json",
                }
            )
            
            if resp.status_code != 200:
                logger.error(f"Worker service error: {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            
            return resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to worker service at {WORKER_URL}. Please ensure the worker service is running."
        )
    except Exception as e:
        logger.error(f"Chatbot proxy error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting CtrlChecks AI Backend on port {settings.port}")
    logger.info(f"Ollama URL: {OLLAMA_URL}")
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
