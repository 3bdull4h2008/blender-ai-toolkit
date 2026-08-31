"""Apply HDRI Operator — applies HDRI environment lighting."""
import os
import base64
import bpy
from bpy.types import Operator


class AIApplyHDRIOperator(Operator):
    """Apply an HDRI environment to the scene."""
    bl_idname = "ai.apply_hdri"
    bl_label = "Apply HDRI"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.hdri_prompt.strip():
            self.report({'WARNING'}, "Please describe the environment")
            return {'CANCELLED'}

        prefs = context.preferences.addons.get("blender_ai_toolkit")
        if not prefs:
            self.report({'ERROR'}, "AI Toolkit preferences not found")
            return {'CANCELLED'}

        from ...api.hdri import get_hdri_provider
        provider = get_hdri_provider(props.hdri_provider, prefs.preferences)
        if not provider or not provider.is_configured:
            self.report({'WARNING'}, f"Provider {props.hdri_provider} not configured")
            return {'CANCELLED'}

        props.is_generating = True
        props.status_message = "Generating HDRI environment..."

        from ...core.task_queue import get_task_queue
        from ...api.base import GenerationRequest
        from ...utils.file_utils import generate_model_id

        model_id = generate_model_id()
        request = GenerationRequest(
            prompt=props.hdri_prompt,
            model_id=model_id,
            provider_id=props.hdri_provider,
            params={
                "style": props.hdri_style,
                "negative_prompt": props.hdri_negative_prompt,
                "seed": props.hdri_seed,
            },
        )

        def work_func(task_info):
            result = provider.generate(request)
            return {
                "success": result.success,
                "output_files": result.output_files,
                "error": result.error,
                "params": result.params if hasattr(result, 'params') else {},
            }

        def on_complete(task_info):
            bpy.app.timers.register(
                lambda: self._on_complete(context, task_info),
                first_interval=0.1,
            )

        get_task_queue().submit(
            task_id=f"hdri_{model_id}",
            task_type="hdri",
            provider_id=props.hdri_provider,
            prompt=props.hdri_prompt,
            model_id=model_id,
            work_func=work_func,
            on_complete=on_complete,
        )

        self.report({'INFO'}, "Generating HDRI environment...")
        return {'FINISHED'}

    def _on_complete(self, context, task_info):
        props = context.scene.ai_toolkit
        props.is_generating = False

        if task_info.result and task_info.result.get("success"):
            # Create or get world
            world = bpy.context.scene.world
            if not world:
                world = bpy.data.worlds.new("AI_World")
                bpy.context.scene.world = world

            world.use_nodes = True
            node_tree = world.node_tree

            # Clear existing nodes
            for node in node_tree.nodes:
                node_tree.nodes.remove(node)

            output_files = task_info.result.get("output_files", [])
            params = task_info.result.get("params", {})
            base64_img = params.get("base64_image")

            if output_files or base64_img:
                # Load the generated HDRI image
                img_name = f"AI_HDRI_{task_info.model_id[:8]}"
                img = bpy.data.images.new(name=img_name, width=2048, height=1024, is_data=False)

                if base64_img:
                    try:
                        img_data = base64.b64decode(base64_img)
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=".exr", delete=False) as f:
                            f.write(img_data)
                            temp_path = f.name
                        img.filepath_raw = temp_path
                        img.reload()
                    except Exception as e:
                        print(f"[AI Toolkit] Failed to decode HDRI: {e}")
                elif output_files and output_files[0].startswith("http"):
                    from ...api.http_client import get_http_client
                    from ...utils.file_utils import get_addon_storage_path

                    storage = os.path.join(get_addon_storage_path(), "hdri")
                    os.makedirs(storage, exist_ok=True)
                    filepath = os.path.join(storage, f"{task_info.model_id}.exr")

                    client = get_http_client()
                    if client.download(output_files[0], filepath):
                        img.filepath_raw = filepath
                        img.reload()

                # Environment texture node
                env_node = node_tree.nodes.new("ShaderNodeTexEnvironment")
                env_node.image = img
                env_node.location = (-300, 0)

                # Background node
                bg_node = node_tree.nodes.new("ShaderNodeBackground")
                bg_node.inputs["Strength"].default_value = 1.0
                bg_node.location = (0, 0)

                # Output node
                output_node = node_tree.nodes.new("ShaderNodeOutputWorld")
                output_node.location = (300, 0)

                # Connect
                node_tree.links.new(env_node.outputs["Color"], bg_node.inputs["Color"])
                node_tree.links.new(bg_node.outputs["Background"], output_node.inputs["Surface"])

            else:
                # Fallback: procedural based on prompt keywords
                bg_node = node_tree.nodes.new("ShaderNodeBackground")
                bg_node.location = (0, 0)

                prompt_lower = task_info.prompt.lower()
                if any(w in prompt_lower for w in ["sunset", "evening", "dusk"]):
                    bg_node.inputs["Color"].default_value = (0.9, 0.4, 0.1, 1.0)
                    bg_node.inputs["Strength"].default_value = 2.0
                elif any(w in prompt_lower for w in ["night", "dark", "moon"]):
                    bg_node.inputs["Color"].default_value = (0.05, 0.05, 0.15, 1.0)
                    bg_node.inputs["Strength"].default_value = 0.5
                elif any(w in prompt_lower for w in ["studio", "bright", "white"]):
                    bg_node.inputs["Color"].default_value = (0.95, 0.95, 0.95, 1.0)
                    bg_node.inputs["Strength"].default_value = 3.0
                elif any(w in prompt_lower for w in ["forest", "nature", "green"]):
                    bg_node.inputs["Color"].default_value = (0.3, 0.5, 0.2, 1.0)
                    bg_node.inputs["Strength"].default_value = 1.5
                else:
                    bg_node.inputs["Color"].default_value = (0.5, 0.6, 0.7, 1.0)
                    bg_node.inputs["Strength"].default_value = 1.0

                output_node = node_tree.nodes.new("ShaderNodeOutputWorld")
                output_node.location = (300, 0)
                node_tree.links.new(bg_node.outputs["Background"], output_node.inputs["Surface"])

            props.status_message = "HDRI environment applied"
            self.report({'INFO'}, "HDRI environment applied")
        else:
            error = task_info.result.get("error", "Unknown error") if task_info.result else "Task failed"
            props.status_message = f"HDRI generation failed: {error[:100]}"
            self.report({'ERROR'}, error)

        return None
