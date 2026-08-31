"""
Generate Image Operators — handle image generation from text prompts.
Supports DALL-E 3 and Stability AI providers.
"""
import os
import bpy
from bpy.types import Operator


class AIGenerateImageOperator(Operator):
    """Generate an image from a text prompt."""
    bl_idname = "ai.generate_image"
    bl_label = "Generate Image"
    bl_description = "Generate an image from text description using selected AI provider"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.image_prompt.strip():
            self.report({'WARNING'}, "Please enter a prompt to generate")
            return {'CANCELLED'}

        prefs = context.preferences.addons.get("blender_ai_toolkit")
        if not prefs:
            self.report({'ERROR'}, "AI Toolkit preferences not found")
            return {'CANCELLED'}

        from ...api.image import get_image_provider
        provider = get_image_provider(props.image_provider, prefs.preferences)
        if not provider or not provider.is_configured:
            self.report({'WARNING'}, f"Provider {props.image_provider} not configured")
            return {'CANCELLED'}

        props.is_generating = True
        props.status_message = f"Generating: {props.image_prompt[:40]}..."
        props.generation_progress = 0.1

        from ...core.task_queue import get_task_queue
        from ...api.base import GenerationRequest
        from ...utils.file_utils import generate_model_id

        model_id = generate_model_id()
        request = GenerationRequest(
            prompt=props.image_prompt,
            model_id=model_id,
            provider_id=props.image_provider,
            params={
                "negative_prompt": props.image_negative_prompt,
                "size": props.image_size,
                "quality": props.image_quality,
                "style": props.image_style_preset if props.image_style_preset != "none" else "vivid",
            },
        )

        def work_func(task_info):
            result = provider.generate(request)
            return {
                "success": result.success,
                "output_files": result.output_files,
                "error": result.error,
            }

        def on_complete(task_info):
            bpy.app.timers.register(
                lambda: self._on_complete(context, task_info),
                first_interval=0.1,
            )

        get_task_queue().submit(
            task_id=f"img_{model_id}",
            task_type="image",
            provider_id=props.image_provider,
            prompt=props.image_prompt,
            model_id=model_id,
            work_func=work_func,
            on_complete=on_complete,
        )

        self.report({'INFO'}, f"Generating image: {props.image_prompt[:50]}...")
        return {'FINISHED'}

    def _on_complete(self, context, task_info):
        props = context.scene.ai_toolkit
        props.is_generating = False

        if task_info.result and task_info.result.get("success"):
            urls = task_info.result.get("output_files", [])
            if urls:
                url = urls[0]
                # Download the image
                from ...utils.file_utils import get_addon_storage_path
                from ...api.http_client import get_http_client

                storage = os.path.join(get_addon_storage_path(), "images")
                os.makedirs(storage, exist_ok=True)
                filepath = os.path.join(storage, f"{task_info.model_id}.png")

                client = get_http_client()
                if client.download(url, filepath):
                    # Import as image plane
                    try:
                        bpy.ops.image.open(filepath=filepath)
                        img = bpy.data.images.get(os.path.basename(filepath))
                        if img:
                            props.status_message = f"Image saved: {filepath}"
                        else:
                            props.status_message = f"Image saved to: {filepath}"
                    except Exception:
                        props.status_message = f"Image saved to: {filepath}"
                else:
                    props.status_message = "Download failed"
            else:
                props.status_message = "No output files"
        else:
            error = task_info.result.get("error", "Unknown error") if task_info.result else "Task failed"
            props.status_message = f"Error: {error[:100]}"
            self.report({'ERROR'}, error)

        return None


# =============================================================================
# Registration
# =============================================================================

classes = (AIGenerateImageOperator,)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" in str(e):
                print(f"[AI Toolkit] {cls.__name__} already registered")


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except (ValueError, RuntimeError):
            pass
