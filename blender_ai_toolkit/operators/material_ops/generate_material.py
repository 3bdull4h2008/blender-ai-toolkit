"""Generate Material Operator — creates PBR materials from AI generation."""
import os
import base64
import bpy
from bpy.types import Operator


class AIGenerateMaterialOperator(Operator):
    """Generate a PBR material from a text prompt."""
    bl_idname = "ai.generate_material"
    bl_label = "Generate Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.material_prompt.strip():
            self.report({'WARNING'}, "Please enter a material description")
            return {'CANCELLED'}

        prefs = context.preferences.addons.get("blender_ai_toolkit")
        if not prefs:
            self.report({'ERROR'}, "AI Toolkit preferences not found")
            return {'CANCELLED'}

        from ...api.material import get_material_provider
        provider = get_material_provider(props.material_provider, prefs.preferences)
        if not provider or not provider.is_configured:
            self.report({'WARNING'}, f"Provider {props.material_provider} not configured")
            return {'CANCELLED'}

        props.is_generating = True
        props.status_message = f"Generating material: {props.material_prompt[:40]}..."

        from ...core.task_queue import get_task_queue
        from ...api.base import GenerationRequest
        from ...utils.file_utils import generate_model_id

        model_id = generate_model_id()
        request = GenerationRequest(
            prompt=props.material_prompt,
            model_id=model_id,
            provider_id=props.material_provider,
            params={
                "negative_prompt": props.material_negative_prompt,
                "resolution": props.material_resolution,
                "seamless": props.material_seamless,
                "maps": {
                    "diffuse": props.material_gen_diffuse,
                    "normal": props.material_gen_normal,
                    "roughness": props.material_gen_roughness,
                    "metallic": props.material_gen_metallic,
                    "displacement": props.material_gen_displacement,
                    "ao": props.material_gen_ao,
                },
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
            task_id=f"mat_{model_id}",
            task_type="material",
            provider_id=props.material_provider,
            prompt=props.material_prompt,
            model_id=model_id,
            work_func=work_func,
            on_complete=on_complete,
        )

        self.report({'INFO'}, "Generating material...")
        return {'FINISHED'}

    def _on_complete(self, context, task_info):
        props = context.scene.ai_toolkit
        props.is_generating = False

        if task_info.result and task_info.result.get("success"):
            mat_name = f"AI_Mat_{task_info.model_id[:8]}"
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")

            if bsdf:
                output_files = task_info.result.get("output_files", [])
                params = task_info.result.get("params", {})
                base64_img = params.get("base64_image")

                if output_files or base64_img:
                    # Create image texture from generated image
                    img_name = f"{mat_name}_diffuse"
                    img = bpy.data.images.new(name=img_name, width=1024, height=1024)

                    if base64_img:
                        # Decode base64 image
                        try:
                            img_data = base64.b64decode(base64_img)
                            import tempfile
                            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                                f.write(img_data)
                                temp_path = f.name
                            img.filepath_raw = temp_path
                            img.reload()
                        except Exception as e:
                            print(f"[AI Toolkit] Failed to decode base64 image: {e}")
                    elif output_files and output_files[0].startswith("http"):
                        # Download from URL
                        from ...api.http_client import get_http_client
                        from ...utils.file_utils import get_addon_storage_path

                        storage = os.path.join(get_addon_storage_path(), "materials")
                        os.makedirs(storage, exist_ok=True)
                        filepath = os.path.join(storage, f"{task_info.model_id}.png")

                        client = get_http_client()
                        if client.download(output_files[0], filepath):
                            img.filepath_raw = filepath
                            img.reload()

                    # Connect image to BSDF
                    tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
                    tex_node.image = img
                    tex_node.location = (-400, 0)

                    bsdf.location = (0, 0)
                    mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

                else:
                    # Fallback: procedural based on prompt keywords
                    prompt_lower = task_info.prompt.lower()
                    if any(w in prompt_lower for w in ["wood", "oak", "pine"]):
                        bsdf.inputs["Base Color"].default_value = (0.55, 0.35, 0.15, 1.0)
                        bsdf.inputs["Roughness"].default_value = 0.7
                    elif any(w in prompt_lower for w in ["metal", "steel", "iron"]):
                        bsdf.inputs["Base Color"].default_value = (0.7, 0.7, 0.7, 1.0)
                        bsdf.inputs["Metallic"].default_value = 1.0
                        bsdf.inputs["Roughness"].default_value = 0.3
                    elif any(w in prompt_lower for w in ["glass", "crystal"]):
                        bsdf.inputs["Base Color"].default_value = (0.9, 0.95, 1.0, 1.0)
                        bsdf.inputs["Roughness"].default_value = 0.05
                    elif any(w in prompt_lower for w in ["brick", "stone", "concrete"]):
                        bsdf.inputs["Base Color"].default_value = (0.6, 0.4, 0.35, 1.0)
                        bsdf.inputs["Roughness"].default_value = 0.85
                    else:
                        bsdf.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
                        bsdf.inputs["Roughness"].default_value = 0.5

            # Apply to selected object if enabled
            if props.material_apply_to_selected and context.selected_objects:
                for obj in context.selected_objects:
                    if obj.type == 'MESH':
                        obj.data.materials.append(mat)

            props.status_message = f"Material created: {mat_name}"
            self.report({'INFO'}, f"Created material: {mat_name}")
        else:
            error = task_info.result.get("error", "Unknown error") if task_info.result else "Task failed"
            props.status_message = f"Material generation failed: {error[:100]}"
            self.report({'ERROR'}, error)

        return None
