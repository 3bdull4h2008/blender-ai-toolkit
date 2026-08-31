"""Tripo3D API client for text-to-3D and image-to-3D generation."""
import time
import json
from ..base import GenerationRequest, GenerationResult
from ..http_client import get_http_client


class Tripo3DProvider:
    """Tripo3D API provider for 3D model generation."""

    API_BASE = "https://api.tripo3d.ai/v2/openapi"

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.is_configured = bool(self.config.get("api_key"))
        self._http = get_http_client()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Submit a 3D generation task and poll until completion."""
        if not self.is_configured:
            return GenerationResult(success=False, error="Tripo API key not configured")

        # Create task
        task_type = "text_to_model" if not request.params.get("image_url") else "image_to_model"
        payload = {"type": task_type}
        if task_type == "text_to_model":
            payload["prompt"] = request.prompt
        else:
            payload["file"] = {"type": "jpg", "file_id": request.params["image_file_id"]}

        resp = self._http.post(f"{self.API_BASE}/task", data=payload, headers=self._headers())
        if resp.get("error"):
            return GenerationResult(success=False, error=resp.get("message", "Task creation failed"))

        task_id = resp.get("data", {}).get("task_id")
        if not task_id:
            return GenerationResult(success=False, error="No task_id returned")

        # Poll for completion
        max_wait = request.params.get("timeout", 300)
        poll_interval = 3
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_resp = self._http.get(
                f"{self.API_BASE}/task/{task_id}",
                headers=self._headers()
            )
            if status_resp.get("error"):
                continue

            status = status_resp.get("data", {}).get("status")
            if status == "success":
                output = status_resp.get("data", {}).get("output", {})
                model_url = output.get("model")
                if model_url:
                    return GenerationResult(
                        success=True,
                        text_response=f"Model generated successfully",
                        output_files=[model_url]
                    )
                return GenerationResult(success=False, error="No model URL in response")
            elif status == "failed":
                error_msg = status_resp.get("data", {}).get("error", {}).get("message", "Unknown error")
                return GenerationResult(success=False, error=error_msg)

        return GenerationResult(success=False, error=f"Timeout after {max_wait}s")

    def check_balance(self) -> dict:
        """Check API credit balance."""
        resp = self._http.get(f"{self.API_BASE}/user/balance", headers=self._headers())
        if resp.get("error"):
            return {"error": resp.get("message", "Balance check failed")}
        return resp.get("data", {})


class MeshyProvider:
    """Meshy.ai API provider for 3D model generation."""

    API_BASE = "https://api.meshy.ai/v2"

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.is_configured = bool(self.config.get("api_key"))
        self._http = get_http_client()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Submit a 3D generation task and poll until completion."""
        if not self.is_configured:
            return GenerationResult(success=False, error="Meshy API key not configured")

        # Create task
        image_url = request.params.get("image_url")
        if image_url:
            payload = {
                "mode": "image_to_3d",
                "image_url": image_url,
                "enable_pbr": True,
            }
        else:
            payload = {
                "mode": "text_to_3d",
                "prompt": request.prompt,
                "negative_prompt": request.params.get("negative_prompt", ""),
                "art_style": request.params.get("art_style", "realistic"),
                "enable_pbr": True,
            }

        resp = self._http.post(f"{self.API_BASE}/text-to-3d", data=payload, headers=self._headers())
        if resp.get("error"):
            return GenerationResult(success=False, error=resp.get("message", "Task creation failed"))

        task_id = resp.get("result")
        if not task_id:
            return GenerationResult(success=False, error="No task ID returned")

        # Poll for completion
        max_wait = request.params.get("timeout", 300)
        poll_interval = 5
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_resp = self._http.get(
                f"{self.API_BASE}/text-to-3d/{task_id}",
                headers=self._headers()
            )
            if status_resp.get("error"):
                continue

            status = status_resp.get("status")
            if status == "SUCCEEDED":
                model_urls = status_resp.get("model_urls", {})
                glb_url = model_urls.get("glb")
                if glb_url:
                    return GenerationResult(
                        success=True,
                        text_response="Model generated successfully",
                        output_files=[glb_url]
                    )
                return GenerationResult(success=False, error="No GLB URL in response")
            elif status == "FAILED":
                error_msg = status_resp.get("message", "Unknown error")
                return GenerationResult(success=False, error=error_msg)

        return GenerationResult(success=False, error=f"Timeout after {max_wait}s")

    def get_models(self) -> list:
        """List available models."""
        resp = self._http.get(f"{self.API_BASE}/model-versions", headers=self._headers())
        if resp.get("error"):
            return []
        return resp.get("results", [])
