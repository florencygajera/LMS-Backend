import aiohttp
import json

class LLMService:
    def __init__(self):
        # Native local Ollama architecture binding
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3"

    async def generate_response(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.ollama_url, json=payload) as response:
                    if response.status != 200:
                        return f"Local LLM initialization failed. Ensure Localhost Ollama node is active."
                    
                    data = await response.json()
                    return data.get("response", "Could not generate response.")
                    
        except aiohttp.ClientError:
            return "Connection refused: Local Ollama AI generation instance is offline or unreachable."

llm_service = LLMService()
