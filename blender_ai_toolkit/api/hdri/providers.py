"""HDRI generation providers — Stability AI and ComfyUI."""
import os
import time
from ..base import GenerationRequest, GenerationResult
from ..http_client import get_http_client


class StabilityHDRIProvider:
    """Stability AI HDRI/environment generation provider."""

    API_BASE = "https://api.stability.ai/v2beta"

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.is_configured = bool(self.config.get("api_key"))
        self._http = get_http_client()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Accept": "application/json",
        }

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate an HDRI environment map."""
        if not self.is_configured:
            return GenerationResult(success=False, error="Stability API key not configured")

        # Generate a panoramic image for HDRI
        prompt = f"360 degree panoramic {request.prompt}, environment map, HDR lighting, seamless"

        payload = {
            "prompt": prompt,
            "negative_prompt": request.params.get("negative_prompt", "seams, artifacts, text"),
            "width": 2048,
            "height": 1024,
            "steps": 30,
            "cfg_scale": 7.0,
        }

        try:
            result = self._http.post(
                f"{self.API_BASE}/stable-image/generate/sd3",
                data=payload,
                headers=self._headers(),
            )

            if result.get("error"):
                return GenerationResult(success=False, error=result.get("message", "Generation failed"))

            image_data = result.get("image")
            if not image_data:
                return GenerationResult(success=False, error="No image in response")

            return GenerationResult(
                success=True,
                text_response="HDRI environment generated",
                output_files=[image_data] if image_data.startswith("http") else [],
                params={"base64_image": image_data if not image_data.startswith("http") else None},
            )
        except Exception as e:
            return GenerationResult(success=False, error=str(e))


class ComfyUIHDRIProvider:
    """ComfyUI HDRI generation via workflow execution."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.base_url = config.get("base_url", "http://127.0.0.1:8188") if config else "http://127.0.0.1:8188"
        self.is_configured = True
        self._http = get_http_client()

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Execute an HDRI workflow in ComfyUI."""
        try:
            workflow = self._build_hdri_workflow(request)
            resp = self._http.post(
                f"{self.base_url}/prompt",
                data={"prompt": workflow},
            )

            if resp.get("error"):
                return GenerationResult(success=False, error=resp.get("message", "ComfyUI request failed"))

            prompt_id = resp.get("prompt_id")
            if not prompt_id:
                return GenerationResult(success=False, error="No prompt_id returned")

            max_wait = 120
            elapsed = 0
            while elapsed < max_wait:
                time.sleep(2)
                elapsed += 2

                history = self._http.get(f"{self.base_url}/history/{prompt_id}")
                if history.get("error"):
                    continue

                outputs = history.get(prompt_id, {}).get("outputs", {})
                if outputs:
                    for node_id, node_output in outputs.items():
                        images = node_output.get("images", [])
                        if images:
                            img = images[0]
                            filename = img.get("filename")
                            subfolder = img.get("subfolder", "")
                            img_type = img.get("type", "output")
                            url = f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                            return GenerationResult(
                                success=True,
                                text_response="HDRI generated via ComfyUI",
                                output_files=[url],
                            )

            return GenerationResult(success=False, error="ComfyUI timeout")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    def _build_hdri_workflow(self, request: GenerationRequest) -> dict:
        """Build a panoramic image workflow for HDRI."""
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": request.params.get("seed", 42),
                    "steps": 25,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 2048, "height": 1024, "batch_size": 1},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": f"360 degree panoramic {request.prompt}, environment map, HDR, seamless",
                    "clip": ["4", 1],
                },
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": request.params.get("negative_prompt", "seams, artifacts, text, watermark"),
                    "clip": ["4", 1],
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "ai_hdri", "images": ["8", 0]},
            },
        }


def get_hdri_provider(provider_id: str, prefs=None):
    """Get HDRI provider by ID."""
    providers = {
        "stability_hdri": StabilityHDRIProvider,
        "comfy_hdri": ComfyUIHDRIProvider,
    }
    cls = providers.get(provider_id)
    if cls:
        config = prefs.get_provider_config(provider_id) if prefs else {}
        return cls(config)
    return None
