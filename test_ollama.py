import asyncio
from app.services.llm.ollama_client import OllamaClient

async def test():
    client = OllamaClient()
    result = await client.is_available(timeout=3.0)
    print(f'Ollama server available: {result}')
    
    if result:
        models = await client.list_models(timeout=5.0)
        print(f'Available models: {models}')
        
        # Test generation with short timeout
        gen_result = await client.generate(
            prompt="Hello, how are you?",
            model="llama3" if "llama3" in models else models[0] if models else "llama3",
            timeout=5.0
        )
        print(f'Generation result: {gen_result.get("status")}')
        if gen_result.get("status") == "success":
            print(f'Response: {gen_result.get("result")}')
        else:
            print(f'Error: {gen_result.get("message")}')

if __name__ == "__main__":
    asyncio.run(test())