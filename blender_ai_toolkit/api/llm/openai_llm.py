"""LLM Providers — real implementations for OpenAI, Anthropic, Ollama, LM Studio."""
import json
import urllib.request
import urllib.error
from ..base import GenerationRequest, GenerationResult


class BaseLLMProvider:
    """Base class for LLM providers."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.is_configured = self._check_config()

    def _check_config(self) -> bool:
        return True

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate text from prompt — override in subclasses."""
        return GenerationResult(success=False, error="Not implemented")

    def _post_json(self, url: str, data: dict, headers: dict = None, timeout: int = 120) -> dict:
        """Helper: POST JSON and return parsed response."""
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        ctx = __import__("ssl").create_default_context()
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI GPT provider — supports GPT-4, GPT-4o, GPT-3.5."""

    def _check_config(self) -> bool:
        key = self.config.get("api_key", "")
        return bool(key and key.startswith("sk-"))

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.is_configured:
            return GenerationResult(success=False, error="OpenAI API key not configured")

        base_url = self.config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        system_prompt = request.params.get("system_prompt", "You are a helpful Blender expert.")
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided
        history = request.params.get("history", [])
        messages.extend(history)

        messages.append({"role": "user", "content": request.prompt})

        data = {
            "model": request.params.get("model", "gpt-4o"),
            "messages": messages,
            "temperature": request.params.get("temperature", 0.7),
            "max_tokens": request.params.get("max_tokens", 4096),
        }

        if request.params.get("json_mode"):
            data["response_format"] = {"type": "json_object"}

        try:
            result = self._post_json(url, data, headers={
                "Authorization": f"Bearer {self.config['api_key']}"
            })
            if "error" in result:
                return GenerationResult(success=False, error=result["error"].get("message", str(result["error"])))
            text = result["choices"][0]["message"]["content"]
            return GenerationResult(success=True, text_response=text)
        except Exception as e:
            return GenerationResult(success=False, error=str(e))


class AnthropicLLMProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

    def _check_config(self) -> bool:
        key = self.config.get("api_key", "")
        return bool(key and key.startswith("sk-ant-"))

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.is_configured:
            return GenerationResult(success=False, error="Anthropic API key not configured")

        url = "https://api.anthropic.com/v1/messages"
        system_prompt = request.params.get("system_prompt", "You are a helpful Blender expert.")

        messages = []
        history = request.params.get("history", [])
        messages.extend(history)
        messages.append({"role": "user", "content": request.prompt})

        data = {
            "model": request.params.get("model", "claude-sonnet-4-20250514"),
            "max_tokens": request.params.get("max_tokens", 4096),
            "system": system_prompt,
            "messages": messages,
        }

        try:
            result = self._post_json(url, data, headers={
                "x-api-key": self.config["api_key"],
                "anthropic-version": "2023-06-01",
            })
            if "error" in result:
                return GenerationResult(success=False, error=result["error"].get("message", str(result["error"])))
            text = result["content"][0]["text"]
            return GenerationResult(success=True, text_response=text)
        except Exception as e:
            return GenerationResult(success=False, error=str(e))


class OllamaLLMProvider(BaseLLMProvider):
    """Ollama local LLM provider."""

    def _check_config(self) -> bool:
        return True  # Local, always "configured"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        base_url = self.config.get("base_url", "http://127.0.0.1:11434").rstrip("/")
        url = f"{base_url}/api/chat"

        system_prompt = request.params.get("system_prompt", "You are a helpful Blender expert.")
        messages = [{"role": "system", "content": system_prompt}]

        history = request.params.get("history", [])
        messages.extend(history)
        messages.append({"role": "user", "content": request.prompt})

        data = {
            "model": request.params.get("model", "llama3.2"),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.params.get("temperature", 0.7),
                "num_predict": request.params.get("max_tokens", 4096),
            },
        }

        try:
            result = self._post_json(url, data)
            if "error" in result:
                return GenerationResult(success=False, error=result["error"])
            text = result["message"]["content"]
            return GenerationResult(success=True, text_response=text)
        except Exception as e:
            return GenerationResult(success=False, error=str(e))


class LMStudioLLMProvider(BaseLLMProvider):
    """LM Studio local LLM provider (OpenAI-compatible API)."""

    def _check_config(self) -> bool:
        return True  # Local, always "configured"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        base_url = self.config.get("base_url", "http://127.0.0.1:1234/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        system_prompt = request.params.get("system_prompt", "You are a helpful Blender expert.")
        messages = [{"role": "system", "content": system_prompt}]

        history = request.params.get("history", [])
        messages.extend(history)
        messages.append({"role": "user", "content": request.prompt})

        data = {
            "model": request.params.get("model", "default"),
            "messages": messages,
            "temperature": request.params.get("temperature", 0.7),
            "max_tokens": request.params.get("max_tokens", 4096),
        }

        try:
            result = self._post_json(url, data)
            if "error" in result:
                return GenerationResult(success=False, error=result["error"].get("message", str(result["error"])))
            text = result["choices"][0]["message"]["content"]
            return GenerationResult(success=True, text_response=text)
        except Exception as e:
            return GenerationResult(success=False, error=str(e))


def get_llm_provider(provider_id: str, prefs=None):
    """Get LLM provider by ID."""
    providers = {
        "openai": OpenAILLMProvider,
        "anthropic": AnthropicLLMProvider,
        "ollama": OllamaLLMProvider,
        "lmstudio": LMStudioLLMProvider,
    }
    cls = providers.get(provider_id)
    if cls:
        config = prefs.get_provider_config(provider_id) if prefs else {}
        return cls(config)
    return None


def get_or_create_llm_provider(provider_id: str, prefs):
    """Get or create an LLM provider, with fallback."""
    provider = get_llm_provider(provider_id, prefs)
    if provider is None:
        return BaseLLMProvider()
    return provider
