"""ComfyUI client with WebSocket progress and file upload."""
import json
import os
import time
import uuid
import urllib.request
import urllib.error
import ssl
from typing import Any, Dict, Optional, Callable
from ..http_client import get_http_client


class ComfyUIClient:
    """ComfyUI HTTP + WebSocket client for workflow execution."""

    def __init__(self, base_url: str = "http://127.0.0.1:8188"):
        self.base_url = base_url.rstrip("/")
        self._http = get_http_client()
        self._client_id = str(uuid.uuid4())
        self._ssl_ctx = ssl.create_default_context()

    def is_alive(self) -> bool:
        """Check if ComfyUI server is running."""
        try:
            resp = self._http.get(f"{self.base_url}/system_stats", timeout=5)
            return not resp.get("error")
        except Exception:
            return False

    def get_system_stats(self) -> Dict:
        """Get system stats including VRAM usage."""
        try:
            resp = self._http.get(f"{self.base_url}/system_stats")
            if resp.get("error"):
                return {}
            devices = resp.get("devices", [])
            if devices:
                dev = devices[0]
                return {
                    "vram_free": dev.get("vram_free", 0) / (1024 * 1024),
                    "vram_total": dev.get("vram_total", 0) / (1024 * 1024),
                    "cpu_usage": resp.get("cpu_usage", 0),
                }
            return {}
        except Exception:
            return {}

    def get_models(self, model_type: str) -> list:
        """Get available models by type (checkpoints, loras, etc.)."""
        try:
            resp = self._http.get(f"{self.base_url}/models/{model_type}")
            if resp.get("error"):
                return []
            return resp
        except Exception:
            return []

    def upload_image(self, filepath: str, subfolder: str = "", image_type: str = "input") -> Optional[str]:
        """Upload an image to ComfyUI server."""
        try:
            import mimetypes
            filename = os.path.basename(filepath)
            content_type = mimetypes.guess_type(filepath)[0] or "image/png"

            # Build multipart form data
            boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"

            body = b""
            # File field
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode()
            body += f"Content-Type: {content_type}\r\n\r\n".encode()
            with open(filepath, "rb") as f:
                body += f.read()
            body += b"\r\n"

            # Subfolder field
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="subfolder"\r\n\r\n'.encode()
            body += subfolder.encode()
            body += b"\r\n"

            # Type field
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="type"\r\n\r\n'.encode()
            body += image_type.encode()
            body += b"\r\n"

            body += f"--{boundary}--\r\n".encode()

            req = urllib.request.Request(
                f"{self.base_url}/upload/image",
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=30, context=self._ssl_ctx)
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("name")
        except Exception as e:
            print(f"[AI Toolkit] Upload failed: {e}")
            return None

    def queue_prompt(self, workflow: Dict, on_progress: Callable = None) -> Optional[str]:
        """Queue a workflow for execution. Returns prompt_id."""
        payload = {
            "prompt": workflow,
            "client_id": self._client_id,
        }

        try:
            resp = self._http.post(f"{self.base_url}/prompt", data=payload)
            if resp.get("error"):
                print(f"[AI Toolkit] Queue failed: {resp.get('message')}")
                return None
            return resp.get("prompt_id")
        except Exception as e:
            print(f"[AI Toolkit] Queue error: {e}")
            return None

    def poll_history(self, prompt_id: str) -> Optional[Dict]:
        """Poll for workflow completion via history endpoint."""
        try:
            resp = self._http.get(f"{self.base_url}/history/{prompt_id}")
            if resp.get("error"):
                return None
            return resp.get(prompt_id)
        except Exception:
            return None

    def wait_for_completion(self, prompt_id: str, timeout: int = 300,
                           on_progress: Callable = None) -> Optional[Dict]:
        """Wait for a workflow to complete by polling history."""
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(2)
            history = self.poll_history(prompt_id)
            if history:
                return history

            if on_progress:
                elapsed = time.time() - start
                on_progress(elapsed / timeout * 100)

        return None

    def get_images_from_history(self, history: Dict) -> list:
        """Extract image filenames from completed workflow history."""
        images = []
        outputs = history.get("outputs", {})
        for node_id, node_output in outputs.items():
            # Check for image outputs
            if "images" in node_output:
                for img in node_output["images"]:
                    images.append({
                        "filename": img.get("filename"),
                        "subfolder": img.get("subfolder", ""),
                        "type": img.get("type", "output"),
                    })
        return images

    def get_image_url(self, filename: str, subfolder: str = "", img_type: str = "output") -> str:
        """Get URL for a generated image."""
        return f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"

    def download_image(self, filename: str, dest_path: str, subfolder: str = "", img_type: str = "output") -> bool:
        """Download a generated image to disk."""
        url = self.get_image_url(filename, subfolder, img_type)
        return self._http.download(url, dest_path)

    def free_vram(self) -> bool:
        """Free VRAM on the ComfyUI server."""
        try:
            payload = {"unload_models": True, "free_memory": True}
            self._http.post(f"{self.base_url}/free", data=payload)
            time.sleep(1)
            # Second pass to clear CUDA cache
            self._http.post(f"{self.base_url}/free", data=payload)
            return True
        except Exception:
            return False

    def clear_queue(self) -> bool:
        """Clear the execution queue."""
        try:
            self._http.post(f"{self.base_url}/queue", data={"clear": True})
            return True
        except Exception:
            return False

    def interrupt(self) -> bool:
        """Interrupt current execution."""
        try:
            self._http.post(f"{self.base_url}/interrupt")
            return True
        except Exception:
            return False


# Workflow presets for common tasks
WORKFLOW_PRESETS = {
    "txt2img_sdxl": {
        "name": "SDXL Text to Image",
        "description": "Generate image from text using SDXL",
        "workflow": {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 42,
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
                "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "", "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "blurry, low quality", "clip": ["4", 1]},
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "ai_gen", "images": ["8", 0]},
            },
        },
    },
    "material_pbr": {
        "name": "PBR Material Generation",
        "description": "Generate PBR material textures",
        "workflow": {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 42,
                    "steps": 30,
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
                "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "seamless tileable PBR material texture", "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "blurry, seams, artifacts, text", "clip": ["4", 1]},
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "ai_material", "images": ["8", 0]},
            },
        },
    },
    "hdri_panoramic": {
        "name": "HDRI Panoramic",
        "description": "Generate panoramic HDRI environment",
        "workflow": {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 42,
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
                    "text": "360 degree panoramic environment map, HDR lighting, seamless",
                    "clip": ["4", 1],
                },
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "seams, artifacts, text, watermark", "clip": ["4", 1]},
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "ai_hdri", "images": ["8", 0]},
            },
        },
    },
}


def get_comfyui_client(base_url: str = None) -> ComfyUIClient:
    """Get or create ComfyUI client."""
    if base_url is None:
        base_url = "http://127.0.0.1:8188"
    return ComfyUIClient(base_url)


def get_workflow_preset(preset_id: str) -> Optional[Dict]:
    """Get a workflow preset by ID."""
    return WORKFLOW_PRESETS.get(preset_id)


def get_all_workflow_presets() -> list:
    """Get all workflow presets."""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in WORKFLOW_PRESETS.items()
    ]
