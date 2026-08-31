"""
Scene Composer Operator - Generate entire scenes from text descriptions.
"""

import bpy
from bpy.types import Operator

from ...core.scene_composer import get_scene_composer, ObjectType
from ...api.llm import get_llm_provider, get_or_create_llm_provider
from ...api.base import GenerationRequest
from ...core.task_queue import get_task_queue, TaskStatus
from ...core.notifications.notification_manager import get_notification_manager
from ...utils.file_utils import generate_model_id


class AIComposeSceneOperator(Operator):
    """Compose a Blender scene from a text description."""
    bl_idname = "ai.compose_scene"
    bl_label = "Compose Scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.scene_prompt:
            self.report({'ERROR'}, "Please enter a scene description")
            return {'CANCELLED'}

        # Get preferences safely
        prefs = context.preferences.addons.get("blender_ai_toolkit")
        if not prefs:
            self.report({'ERROR'}, "AI Toolkit preferences not found")
            return {'CANCELLED'}
        
        prefs_obj = prefs.preferences
        
        # First, use LLM to expand the scene description into structured JSON
        provider = get_or_create_llm_provider(props.llm_provider, prefs_obj)

        if not provider or not provider.is_configured:
            # Fallback to keyword-based composition
            composer = get_scene_composer()
            scene_desc = composer.compose_from_text(props.scene_prompt)
            collection = composer.build_scene(scene_desc)
            self.report({'INFO'}, f"Scene composed with {len(scene_desc.objects)} objects")
            return {'FINISHED'}

        # Use LLM to generate structured scene description
        props.is_generating = True
        props.status_message = "Composing scene with AI..."

        scene_prompt = props.scene_prompt
        model_id = generate_model_id()

        request = GenerationRequest(
            prompt=self._build_scene_prompt(scene_prompt),
            model_id=model_id,
            provider_id=props.llm_provider,
            params={
                "system_prompt": self._get_scene_system_prompt(),
                "temperature": 0.7,
                "max_tokens": 8192,
                "json_mode": True,
            },
        )

        task_queue = get_task_queue()

        def work_func(task_info):
            result = provider.generate(request)
            return {
                "success": result.success,
                "text_response": result.text_response,
                "error": result.error,
                "scene_prompt": scene_prompt,
            }

        def on_complete(task_info):
            bpy.app.timers_register(
                lambda: self._on_complete(context, task_info),
                first_interval=0.1,
            )

        task_queue.submit(
            task_id=f"scene_{model_id}",
            task_type="scene",
            provider_id=props.llm_provider,
            prompt=scene_prompt,
            model_id=model_id,
            work_func=work_func,
            on_complete=on_complete,
        )

        self.report({'INFO'}, "Composing scene...")
        return {'FINISHED'}

    def _on_complete(self, context, task_info):
        props = context.scene.ai_toolkit
        props.is_generating = False

        if task_info.status == TaskStatus.COMPLETED and task_info.result.get("success"):
            llm_response = task_info.result.get("text_response", "")
            scene_prompt = task_info.result.get("scene_prompt", "")

            composer = get_scene_composer()
            scene_desc = composer.compose_from_text(scene_prompt, llm_response)
            collection = composer.build_scene(scene_desc)

            get_notification_manager().success(
                "Scene Composed",
                f"Created scene with {len(scene_desc.objects)} objects",
            )
            props.status_message = f"Scene composed: {len(scene_desc.objects)} objects"
            self.report({'INFO'}, f"Scene composed with {len(scene_desc.objects)} objects")
        else:
            error = task_info.result.get("error", "Unknown error")
            props.status_message = f"Scene composition failed: {error}"
            get_notification_manager().error("Scene Failed", error)

        return None

    def _build_scene_prompt(self, user_prompt: str) -> str:
        return (
            f"Create a detailed 3D scene description for: {user_prompt}\n\n"
            f"Respond with a JSON object with this structure:\n"
            f'```json\n'
            f'{{\n'
            f'  "name": "Scene Name",\n'
            f'  "background_color": [r, g, b],\n'
            f'  "ambient_light": 0.2,\n'
            f'  "fog_enabled": false,\n'
            f'  "camera_location": [x, y, z],\n'
            f'  "camera_target": [x, y, z],\n'
            f'  "objects": [\n'
            f'    {{\n'
            f'      "name": "Object Name",\n'
            f'      "type": "primitive",\n'
            f'      "primitive": "cube|sphere|cylinder|cone|plane|torus|monkey",\n'
            f'      "location": [x, y, z],\n'
            f'      "rotation": [rx, ry, rz],\n'
            f'      "scale": [sx, sy, sz],\n'
            f'      "color": [r, g, b, a],\n'
            f'      "metalness": 0.0,\n'
            f'      "roughness": 0.5,\n'
            f'      "ai_prompt": ""\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n'
            f'```\n\n'
            f'Use "type": "primitive" for simple shapes, "type": "ai_generated" with "ai_prompt" '
            f'for objects that need AI 3D generation, "type": "light" for lights, '
            f'and "type": "camera" for the camera. Be creative with composition and lighting!'
        )

    def _get_scene_system_prompt(self) -> str:
        return (
            "You are a 3D scene composition expert for Blender. Create detailed, well-lit scenes "
            "with proper object placement, materials, and lighting. Always respond with valid JSON. "
            "Use realistic positions and scales. Include at least one camera and one key light. "
            "For complex objects, use ai_generated type with descriptive prompts."
        )


class AIGenerateSceneAIObjectsOperator(Operator):
    """Generate 3D models for all AI-placeholder objects in the current scene."""
    bl_idname = "ai.generate_scene_ai_objects"
    bl_label = "Generate AI Scene Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Find all AI placeholder objects
        ai_objects = [
            obj for obj in context.scene.objects
            if obj.get("ai_generate") and obj.get("ai_prompt")
        ]

        if not ai_objects:
            self.report({'WARNING'}, "No AI placeholder objects found in scene")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Found {len(ai_objects)} AI objects to generate")

        # Queue generation for each object
        from ...operators.generate_3d import get_3d_provider
        
        # Get preferences safely
        addon_prefs = context.preferences.addons.get("blender_ai_toolkit")
        if not addon_prefs:
            self.report({'ERROR'}, "AI Toolkit preferences not found")
            return {'CANCELLED'}
        
        prefs = addon_prefs.preferences
        props = context.scene.ai_toolkit

        for obj in ai_objects:
            prompt = obj.get("ai_prompt", "")
            if not prompt:
                continue

            provider = get_3d_provider(props.model_3d_provider, prefs)
            if not provider or not provider.is_configured:
                continue

            request = GenerationRequest(
                prompt=prompt,
                model_id=generate_model_id(),
                provider_id=props.model_3d_provider,
                params={"art_style": props.model_3d_art_style},
            )

            task_queue = get_task_queue()

            def work_func(task_info, p=provider, r=request, o=obj):
                result = p.generate(r)
                return {
                    "success": result.success,
                    "output_files": result.output_files,
                    "error": result.error,
                    "object_name": o.name,
                    "location": list(o.location),
                    "scale": list(o.scale),
                }

            task_queue.submit(
                task_id=f"scene_obj_{obj.name}",
                task_type="model_3d",
                provider_id=props.model_3d_provider,
                prompt=prompt,
                model_id=request.model_id,
                work_func=work_func,
            )

        self.report({'INFO'}, f"Queued {len(ai_objects)} objects for generation")
        return {'FINISHED'}
