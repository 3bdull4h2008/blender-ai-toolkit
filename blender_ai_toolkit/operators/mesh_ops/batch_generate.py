"""Batch Generate Operator — generates multiple variations of a prompt."""
import bpy
from bpy.types import Operator


class AIBatchGenerateOperator(Operator):
    """Batch generate multiple variants of a prompt."""
    bl_idname = "ai.batch_generate"
    bl_label = "Batch Generate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit
        count = props.batch_count

        # Get the prompt and provider from the active tab
        prompt = ""
        provider_id = ""
        generation_type = ""

        if props.active_tab == "MODEL_3D":
            prompt = props.model_3d_prompt
            provider_id = props.model_3d_provider
            generation_type = "model_3d"
        elif props.active_tab == "IMAGE":
            prompt = props.image_prompt
            provider_id = props.image_provider
            generation_type = "image"
        elif props.active_tab == "MATERIAL":
            prompt = props.material_prompt
            provider_id = props.material_provider
            generation_type = "material"

        if not prompt.strip():
            self.report({'WARNING'}, "No prompt to batch generate")
            return {'CANCELLED'}

        prefs = context.preferences.addons.get("blender_ai_toolkit")
        if not prefs:
            self.report({'ERROR'}, "AI Toolkit preferences not found")
            return {'CANCELLED'}

        # Get the appropriate provider
        provider = None
        if generation_type == "model_3d":
            from ...operators.generate_3d import get_3d_provider
            provider = get_3d_provider(provider_id, prefs.preferences)
        elif generation_type == "image":
            from ...api.image import get_image_provider
            provider = get_image_provider(provider_id, prefs.preferences)
        elif generation_type == "material":
            from ...api.material import get_material_provider
            provider = get_material_provider(provider_id, prefs.preferences)

        if not provider or not provider.is_configured:
            self.report({'WARNING'}, f"Provider {provider_id} not configured")
            return {'CANCELLED'}

        props.is_generating = True
        props.status_message = f"Batch generating {count} variants..."

        from ...core.task_queue import get_task_queue
        from ...api.base import GenerationRequest
        from ...utils.file_utils import generate_model_id

        submitted = 0
        for i in range(count):
            model_id = generate_model_id()
            request = GenerationRequest(
                prompt=prompt,
                model_id=model_id,
                provider_id=provider_id,
                params={"variant_index": i},
            )

            def work_func(task_info, p=provider, r=request):
                result = p.generate(r)
                return {
                    "success": result.success,
                    "output_files": result.output_files,
                    "error": result.error,
                    "variant": r.params.get("variant_index", 0),
                }

            def on_complete(task_info):
                bpy.app.timers.register(
                    lambda t=task_info: self._on_variant_complete(context, t),
                    first_interval=0.1,
                )

            get_task_queue().submit(
                task_id=f"batch_{model_id}",
                task_type=generation_type,
                provider_id=provider_id,
                prompt=prompt,
                model_id=model_id,
                work_func=work_func,
                on_complete=on_complete,
            )
            submitted += 1

        props.status_message = f"Batch submitted: {submitted} variants"
        self.report({'INFO'}, f"Submitted {submitted} batch generation tasks")
        return {'FINISHED'}

    def _on_variant_complete(self, context, task_info):
        props = context.scene.ai_toolkit
        if task_info.result and task_info.result.get("success"):
            variant = task_info.result.get("variant", 0)
            props.status_message = f"Variant {variant + 1} completed"
        # Check if all done
        from ...core.task_queue import get_task_queue
        queue = get_task_queue()
        if not queue._tasks:
            props.is_generating = False
            props.status_message = "Batch generation complete"
        return None
