"""Mesh Cleanup Operator — cleans up mesh data with multiple operations."""
import bpy
from bpy.types import Operator


class AIMeshCleanupOperator(Operator):
    """Clean up selected mesh (remove doubles, fix normals, fill holes, etc.)."""
    bl_idname = "ai.mesh_cleanup"
    bl_label = "Clean Up Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit
        cleaned = 0

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            mesh = obj.data

            # Ensure we're in object mode
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            # Enter edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')

            # Remove doubles (merge by distance)
            bpy.ops.mesh.remove_doubles(threshold=0.0001)

            # Fix normals
            bpy.ops.mesh.normals_make_consistent(inside=False)

            # Fill holes
            bpy.ops.mesh.fill_holes(sides=24)

            # Remove loose vertices
            bpy.ops.mesh.delete_loose()

            # Triangulate if requested
            if props.mesh_cleanup_triangulate:
                bpy.ops.mesh.quads_convert_to_tris()

            # Back to object mode
            bpy.ops.object.mode_set(mode='OBJECT')

            cleaned += 1

        if cleaned:
            props.status_message = f"Cleaned {cleaned} mesh(es)"
            self.report({'INFO'}, f"Cleaned {cleaned} mesh(es)")
        else:
            self.report({'WARNING'}, "No mesh objects selected")

        return {'FINISHED'}
