"""Texture to Material Operator — converts a texture to a PBR material."""
import bpy
from bpy.types import Operator


class AITextureToMaterialOperator(Operator):
    """Convert a texture image to a PBR material with generated maps."""
    bl_idname = "ai.texture_to_material"
    bl_label = "Texture to Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        # Find the active texture/image
        img = None
        if context.area.spaces.active and hasattr(context.area.spaces.active, "image"):
            img = context.area.spaces.active.image

        if not img:
            self.report({'WARNING'}, "No texture image selected")
            return {'CANCELLED'}

        # Create material from texture
        mat_name = f"Mat_{img.name}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.location = (200, 0)

        # Image texture node for diffuse
        tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        tex_node.location = (-400, 0)

        # Connect texture to Base Color
        mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

        # Add UV mapping if not present
        uv_node = mat.node_tree.nodes.new("ShaderNodeTexCoord")
        uv_node.location = (-600, 0)

        mapping_node = mat.node_tree.nodes.new("ShaderNodeMapping")
        mapping_node.location = (-500, 0)

        mat.node_tree.links.new(uv_node.outputs["UV"], mapping_node.inputs["Vector"])
        mat.node_tree.links.new(mapping_node.outputs["Vector"], tex_node.inputs["Vector"])

        # Generate bump map from texture for normal effect
        if props.material_gen_normal:
            # Convert to bump
            bump_node = mat.node_tree.nodes.new("ShaderNodeBump")
            bump_node.location = (0, -200)
            bump_node.inputs["Strength"].default_value = 0.5

            # Use the same texture as height input (grayscale conversion)
            mat.node_tree.links.new(tex_node.outputs["Color"], bump_node.inputs["Height"])
            mat.node_tree.links.new(bump_node.outputs["Normal"], bsdf.inputs["Normal"])

        # Apply to selected object
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    obj.data.materials.append(mat)

        props.status_message = f"Created material: {mat_name}"
        self.report({'INFO'}, f"Created material from texture: {img.name}")
        return {'FINISHED'}
