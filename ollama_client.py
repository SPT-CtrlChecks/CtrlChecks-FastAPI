import subprocess
import json
import time

class OllamaClient:
    def __init__(self):
        # Production models for AWS g4dn.xlarge (16GB GPU)
        self.models = {
            "llama3.1:8b": "llama3.1:8b",  # General purpose (4.9GB)
            "qwen2.5-coder:7b": "qwen2.5-coder:7b"  # Code generation (4.5GB)
        }
        
    def list_models(self):
        """List available models"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error listing models: {str(e)}"
    
    def generate(self, model: str, prompt: str, options: dict = None) -> dict:
        """
        Generate response from specified model
        
        Args:
            model: Model name (llama3.1:8b for general tasks, qwen2.5-coder:7b for code tasks)
            prompt: Input prompt
            options: Additional options like temperature, max_tokens
            
        Returns:
            Dictionary with response and metadata
        """
        if model not in self.models:
            return {"error": f"Model {model} not available"}
        
        # Build command
        cmd = ["ollama", "run", model]
        
        # Add options if provided
        if options:
            options_str = json.dumps(options)
            cmd.extend(["--options", options_str])
        
        # Add prompt
        cmd.append(prompt)
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout
            )
            
            end_time = time.time()
            latency = end_time - start_time
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "response": result.stdout.strip(),
                    "latency": round(latency, 2),
                    "model": model
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "latency": round(latency, 2)
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Request timeout (180s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def warm_up(self, model: str = None):
        """
        Warm up model to avoid cold start
        """
        if model:
            models_to_warm = [model]
        else:
            models_to_warm = list(self.models.keys())
        
        for model_name in models_to_warm:
            print(f"Warming up {model_name}...")
            self.generate(model_name, "warmup")
            print(f"✓ {model_name} warmed up")
