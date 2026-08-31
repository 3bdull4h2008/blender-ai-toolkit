"""
Generate 3D Model Operators — handle 3D model generation from text or images.
Supports Tripo3D and Meshy providers with async job queue.
"""
import os
import bpy
from bpy.types import Operator


def get_3d_provider(provider_id: str, prefs=None):
    """Get 3D provider instance by ID."""
    from ...api.model_3d import Tripo3DProvider, MeshyProvider

    providers = {
        "tripo": Tripo3DProvider,
        "meshy": MeshyProvider,
    }
    cls = providers.get(provider_id)
    if cls:
        config = prefs.get_provider_config(provider_id) if prefs else {}
        return cls(config)
    return None


def _import_glb(filepath: str, location=(0, 0, 0)):
    """Import a GLB/GLTF file into the scene."""
    try:
        bpy.ops.import_scene.gltf(filepath=filepath)
        obj = bpy.context.active_object
        if obj:
            obj.location = location
        return obj
    except Exception as e:
        print(f"[AI Toolkit] GLB import failed: {e}")
        return None


def _download_model(url: str, filename: str) -> str:
    """Download a model file to addon storage."""
    from ...utils.file_utils import get_addon_storage_path

    storage = os.path.join(get_addon_storage_path(), "models")
    os.makedirs(storage, exist_ok=True)
    dest = os.path.join(storage, filename)

    from ...api.http_client import get_http_client
    client = get_http_client()
    if client.download(url, dest):
        return dest
    return ""


class AIGenerate3DOperator(Operator):
    """Generate a 3D model from a text prompt."""
    bl_idname = "ai.generate_3d"
    bl_label = "Generate 3D Model"
    bl_description = "Generate a 3D model from text description using selected AI provider"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.model_3d_prompt.strip():
            self.report({'WARNING'}, "Please enter a prompt to generate")
            return {'CANCELLED'}

        prefs = context.preferences.addons.get("blender_ai_toolkit")
        if not prefs:
            self.report({'ERROR'}, "AI Toolkit preferences not found")
            return {'CANCELLED'}

        provider = get_3d_provider(props.model_3d_provider, prefs.preferences)
        if not provider or not provider.is_configured:
            self.report({'WARNING'}, f"Provider {props.model_3d_provider} not configured")
            return {'CANCELLED'}

        props.is_generating = True
        props.status_message = f"Generating: {props.model_3d_prompt[:40]}..."
        props.generation_progress = 0.1

        # Use task queue for async generation
        from ...core.task_queue import get_task_queue
        from ...api.base import GenerationRequest
        from ...utils.file_utils import generate_model_id

        model_id = generate_model_id()
        request = GenerationRequest(
            prompt=props.model_3d_prompt,
            model_id=model_id,
            provider_id=props.model_3d_provider,
            params={
                "negative_prompt": props.model_3d_negative_prompt,
                "art_style": props.model_3d_art_style,
                "seed": props.model_3d_seed,
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
            task_id=f"3d_{model_id}",
            task_type="model_3d",
            provider_id=props.model_3d_provider,
            prompt=props.model_3d_prompt,
            model_id=model_id,
            work_func=work_func,
            on_complete=on_complete,
        )

        self.report({'INFO'}, f"Generating 3D model: {props.model_3d_prompt[:50]}...")
        return {'FINISHED'}

    def _on_complete(self, context, task_info):
        props = context.scene.ai_toolkit
        props.is_generating = False

        if task_info.result and task_info.result.get("success"):
            urls = task_info.result.get("output_files", [])
            if urls:
                # Download and import the first model
                filename = f"{task_info.model_id}.glb"
                filepath = _download_model(urls[0], filename)
                if filepath:
                    obj = _import_glb(filepath)
                    if obj:
                        props.status_message = f"Imported: {obj.name}"
                        self.report({'INFO'}, f"Imported model: {obj.name}")
                    else:
                        props.status_message = "Import failed"
                else:
                    props.status_message = "Download failed"
            else:
                props.status_message = "No output files"
        else:
            error = task_info.result.get("error", "Unknown error") if task_info.result else "Task failed"
            props.status_message = f"Error: {error[:100]}"
            self.report({'ERROR'}, error)

        return None


class AIGenerate3DRefImageOperator(Operator):
    """Generate a 3D model from a reference image."""
    bl_idname = "ai.generate_3d_ref_image"
    bl_label = "Generate from Reference"
    bl_description = "Generate a 3D model from an uploaded reference image"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.model_3d_reference_image:
            self.report({'INFO'}, "Select a reference image first")
            return {'CANCELLED'}

        prefs = context.preferences.addons.get("blender_ai_toolkit")
        if not prefs:
            self.report({'ERROR'}, "AI Toolkit preferences not found")
            return {'CANCELLED'}

        provider = get_3d_provider(props.model_3d_provider, prefs.preferences)
        if not provider or not provider.is_configured:
            self.report({'WARNING'}, f"Provider {props.model_3d_provider} not configured")
            return {'CANCELLED'}

        props.is_generating = True
        props.status_message = "Generating 3D from reference image..."

        from ...core.task_queue import get_task_queue
        from ...api.base import GenerationRequest
        from ...utils.file_utils import generate_model_id

        model_id = generate_model_id()
        request = GenerationRequest(
            prompt=props.model_3d_prompt or "3D model from reference",
            model_id=model_id,
            provider_id=props.model_3d_provider,
            params={
                "image_url": props.model_3d_reference_image,
                "art_style": props.model_3d_art_style,
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
            task_id=f"3d_ref_{model_id}",
            task_type="model_3d",
            provider_id=props.model_3d_provider,
            prompt="Image-to-3D",
            model_id=model_id,
            work_func=work_func,
            on_complete=on_complete,
        )

        self.report({'INFO'}, "Generating 3D from reference image...")
        return {'FINISHED'}

    def _on_complete(self, context, task_info):
        props = context.scene.ai_toolkit
        props.is_generating = False

        if task_info.result and task_info.result.get("success"):
            urls = task_info.result.get("output_files", [])
            if urls:
                filename = f"{task_info.model_id}.glb"
                filepath = _download_model(urls[0], filename)
                if filepath:
                    obj = _import_glb(filepath)
                    if obj:
                        props.status_message = f"Imported: {obj.name}"
                    else:
                        props.status_message = "Import failed"
                else:
                    props.status_message = "Download failed"
            else:
                props.status_message = "No output files"
        else:
            error = task_info.result.get("error", "Unknown error") if task_info.result else "Task failed"
            props.status_message = f"Error: {error[:100]}"

        return None


# =============================================================================
# Registration
# =============================================================================

classes = (
    AIGenerate3DOperator,
    AIGenerate3DRefImageOperator,
)


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
