"""Preview gallery for generating multiple candidates and picking the best."""
import bpy
import os
from typing import List, Dict, Optional
from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty


class AIPreviewItem(PropertyGroup):
    """Single preview item in the gallery."""
    preview_id: StringProperty(name="ID", default="")
    image_path: StringProperty(name="Image Path", subtype='FILE_PATH', default="")
    prompt: StringProperty(name="Prompt", default="")
    seed: IntProperty(name="Seed", default=0)
    provider: StringProperty(name="Provider", default="")
    selected: BoolProperty(name="Selected", default=False)


class PreviewGallery:
    """Manages preview images for generation candidates."""

    def __init__(self):
        self._previews: Dict[str, bpy.types.Image] = {}

    def create_preview(self, preview_id: str, filepath: str) -> Optional[bpy.types.Image]:
        """Load a preview image from disk."""
        if not os.path.exists(filepath):
            return None

        try:
            img = bpy.data.images.load(filepath, check_existing=False)
            img.name = f"AI_Preview_{preview_id}"
            self._previews[preview_id] = img
            return img
        except Exception as e:
            print(f"[AI Toolkit] Failed to load preview: {e}")
            return None

    def get_preview(self, preview_id: str) -> Optional[bpy.types.Image]:
        """Get a preview image by ID."""
        return self._previews.get(preview_id)

    def remove_preview(self, preview_id: str):
        """Remove a preview image."""
        img = self._previews.pop(preview_id, None)
        if img:
            bpy.data.images.remove(img)

    def clear(self):
        """Remove all preview images."""
        for img in self._previews.values():
            bpy.data.images.remove(img)
        self._previews.clear()

    def get_all_previews(self) -> List[str]:
        """Get all preview IDs."""
        return list(self._previews.keys())


class AIGeneratePreviewsOperator(bpy.types.Operator):
    """Generate multiple preview candidates for a prompt."""
    bl_idname = "ai.generate_previews"
    bl_label = "Generate Previews"
    bl_description = "Generate multiple preview images to choose from"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit
        count = props.batch_count

        if not props.image_prompt.strip():
            self.report({'WARNING'}, "Enter a prompt first")
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
        props.status_message = f"Generating {count} previews..."

        from ...core.task_queue import get_task_queue
        from ...api.base import GenerationRequest
        from ...utils.file_utils import generate_model_id, get_addon_storage_path

        gallery = PreviewGallery()
        submitted = 0

        for i in range(count):
            model_id = generate_model_id()
            seed = props.image_seed + i if props.image_seed else i * 1000

            request = GenerationRequest(
                prompt=props.image_prompt,
                model_id=model_id,
                provider_id=props.image_provider,
                params={
                    "negative_prompt": props.image_negative_prompt,
                    "size": props.image_size,
                    "quality": props.image_quality,
                    "style": props.image_style_preset if props.image_style_preset != "none" else "vivid",
                    "seed": seed,
                },
            )

            def work_func(task_info, req=request, idx=i):
                result = provider.generate(req)
                return {
                    "success": result.success,
                    "output_files": result.output_files,
                    "error": result.error,
                    "preview_index": idx,
                    "seed": req.params.get("seed", 0),
                }

            get_task_queue().submit(
                task_id=f"preview_{model_id}",
                task_type="preview",
                provider_id=props.image_provider,
                prompt=props.image_prompt,
                model_id=model_id,
                work_func=work_func,
            )
            submitted += 1

        props.status_message = f"Generating {submitted} previews..."
        self.report({'INFO'}, f"Generating {submitted} previews")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(AIPreviewItem)
    bpy.utils.register_class(AIGeneratePreviewsOperator)


def unregister():
    bpy.utils.unregister_class(AIGeneratePreviewsOperator)
    bpy.utils.unregister_class(AIPreviewItem)
