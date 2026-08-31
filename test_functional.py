"""Functional test — call Ollama LLM provider if available."""
import sys
import os
sys.path.insert(0, r"E:\blender ai addon")
sys.path.insert(0, r"E:\blender ai addon\blender_ai_toolkit")

from api.llm.openai_llm import OllamaLLMProvider
from api.base import GenerationRequest

print("=" * 60)
print("FUNCTIONAL TEST — Ollama LLM")
print("=" * 60)

# Test with Ollama (local, no API key needed)
provider = OllamaLLMProvider({"base_url": "http://127.0.0.1:11434"})
print(f"\nOllama configured: {provider.is_configured}")

# Check if Ollama is running
from api.http_client import get_http_client
client = get_http_client()
try:
    result = client.get("http://127.0.0.1:11434/api/tags", timeout=5)
    if "models" in result:
        models = [m["name"] for m in result["models"]]
        print(f"Ollama running. Models: {models[:5]}")
    else:
        print(f"Ollama response: {result}")
        print("Ollama may not be running. Skipping generation test.")
        sys.exit(0)
except Exception as e:
    print(f"Ollama not reachable: {e}")
    print("Skipping generation test (start Ollama to test)")
    sys.exit(0)

# Test generation
print("\nGenerating response...")
request = GenerationRequest(
    prompt="Write 3 lines of Blender Python code to create a red cube",
    model_id="test",
    provider_id="ollama",
    params={
        "system_prompt": "You are a Blender expert. Respond with Python code in ```python blocks.",
        "model": "llama3.2",
        "temperature": 0.7,
        "max_tokens": 256,
    },
)

result = provider.generate(request)
print(f"\nSuccess: {result.success}")
if result.success:
    print(f"Response:\n{result.text_response[:500]}")
else:
    print(f"Error: {result.error}")

print("\n" + "=" * 60)
print("FUNCTIONAL TEST COMPLETE")
print("=" * 60)
