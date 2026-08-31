"""Image generation providers — DALL-E 3 and Stability AI."""
import json
import os
import time
from ..base import GenerationRequest, GenerationResult
from ..http_client import get_http_client


class DallEProvider:
    """DALL-E 3 image generation provider."""

    API_BASE = "https://api.openai.com/v1"

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.is_configured = bool(self.config.get("api_key"))
        self._http = get_http_client()

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.is_configured:
            return GenerationResult(success=False, error="OpenAI API key not configured")

        url = f"{self.API_BASE}/images/generations"
        size = request.params.get("size", "1024x1024")
        quality = request.params.get("quality", "standard")
        style = request.params.get("style", "vivid")

        payload = {
            "model": "dall-e-3",
            "prompt": request.prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "style": style,
            "response_format": "url",
        }

        try:
            result = self._http.post(url, data=payload, headers={
                "Authorization": f"Bearer {self.config['api_key']}"
            })
            if result.get("error"):
                msg = result.get("message", str(result.get("error", "Unknown error")))
                return GenerationResult(success=False, error=msg)

            image_url = result["data"][0]["url"]
            return GenerationResult(
                success=True,
                text_response=f"Image generated ({size}, {quality})",
                output_files=[image_url]
            )
        except Exception as e:
            return GenerationResult(success=False, error=str(e))


class StabilityProvider:
    """Stability AI image generation provider."""

    API_BASE = "https://api.stability.ai/v2beta/stable-image/generate"

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.is_configured = bool(self.config.get("api_key"))
        self._http = get_http_client()

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.is_configured:
            return GenerationResult(success=False, error="Stability API key not configured")

        # Use multipart form for Stability API
        import urllib.request
        import ssl

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += b'Content-Disposition: form-data; name="prompt"\r\n\r\n'
        body += request.prompt.encode()
        body += f"\r\n--{boundary}\r\n".encode()

        size = request.params.get("size", "1024x1024")
        w, h = size.split("x")
        body += f'Content-Disposition: form-data; name="width"\r\n\r\n{w}'.encode()
        body += f"\r\n--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="height"\r\n\r\n{h}'.encode()
        body += f"\r\n--{boundary}--\r\n".encode()

        try:
            req = urllib.request.Request(
                self.API_BASE + "/sd3",
                data=body,
                headers={
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Accept": "application/json",
                },
                method="POST",
            )
            ctx = ssl.create_default_context()
            resp = urllib.request.urlopen(req, timeout=120, context=ctx)
            result = json.loads(resp.read().decode("utf-8"))

            image_url = result.get("image") or result.get("artifacts", [{}])[0].get("base64")
            if image_url:
                return GenerationResult(
                    success=True,
                    text_response="Image generated via Stability AI",
                    output_files=[image_url]
                )
            return GenerationResult(success=False, error="No image in response")
        except Exception as e:
            return GenerationResult(success=False, error=str(e))


def get_image_provider(provider_id: str, prefs=None):
    """Get image provider by ID."""
    providers = {
        "dalle": DallEProvider,
        "stability": StabilityProvider,
    }
    cls = providers.get(provider_id)
    if cls:
        config = prefs.get_provider_config(provider_id) if prefs else {}
        return cls(config)
    return None
