"""
Template Operators - Apply, save, and refresh prompt templates.
"""

import uuid
import bpy
from bpy.types import Operator


class AIApplyTemplateOperator(Operator):
    """Apply a prompt template to the appropriate field."""
    bl_idname = "ai.apply_template"
    bl_label = "Apply Template"
    bl_options = {'REGISTER', 'UNDO'}

    template_id: bpy.props.StringProperty(
        name="Template ID",
        description="ID of the template to apply",
        default="",
    )

    def execute(self, context):
        if not self.template_id:
            self.report({'WARNING'}, "No template selected")
            return {'CANCELLED'}

        try:
            from ..core.templates.template_manager import get_template_manager, TemplateCategory
            from ..utils.file_utils import get_addon_storage_path

            tm = get_template_manager(get_addon_storage_path())
            template = tm.get(self.template_id)

            if not template:
                self.report({'WARNING'}, f"Template not found: {self.template_id}")
                return {'CANCELLED'}

            props = context.scene.ai_toolkit

            # Apply template based on category
            if template.category in (TemplateCategory.TEXTURE,):
                props.material_prompt = template.format_prompt()
                props.material_negative_prompt = template.negative_prompt or ""
                props.active_tab = "MATERIAL"
            elif template.category == TemplateCategory.HDRI:
                props.hdri_prompt = template.format_prompt()
                props.hdri_negative_prompt = template.negative_prompt or ""
                props.active_tab = "MATERIAL"
            else:
                # Default: 3D model prompt
                props.model_3d_prompt = template.format_prompt()
                props.model_3d_negative_prompt = template.negative_prompt or ""
                if template.default_params:
                    art_style = template.default_params.get("art_style")
                    if art_style and art_style in ["realistic", "cartoon", "low-poly"]:
                        props.model_3d_art_style = art_style
                props.active_tab = "MODEL_3D"

            context.window_manager.tag_redraw()
            self.report({'INFO'}, f"Applied template: {template.name}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to apply template: {str(e)}")
            return {'CANCELLED'}


class AIRefreshTemplatesOperator(Operator):
    """Refresh the template library from disk and defaults."""
    bl_idname = "ai.refresh_templates"
    bl_label = "Refresh Templates"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            from ..core.templates.template_manager import get_template_manager
            from ..utils.file_utils import get_addon_storage_path

            tm = get_template_manager(get_addon_storage_path())
            tm.refresh()

            self.report({'INFO'}, "Templates refreshed")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to refresh: {str(e)}")
            return {'CANCELLED'}


class AISaveTemplateOperator(Operator):
    """Save current prompt as a custom template."""
    bl_idname = "ai.save_template"
    bl_label = "Save as Template"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        # Get the active prompt based on current tab
        prompt = ""
        negative_prompt = ""

        if props.active_tab == "MODEL_3D":
            prompt = props.model_3d_prompt
            negative_prompt = props.model_3d_negative_prompt
        elif props.active_tab == "IMAGE":
            prompt = props.image_prompt
            negative_prompt = props.image_negative_prompt
        elif props.active_tab == "MATERIAL":
            prompt = props.material_prompt
            negative_prompt = props.material_negative_prompt
        elif props.active_tab == "SCENE":
            prompt = props.scene_prompt

        if not prompt or not prompt.strip():
            self.report({'WARNING'}, "No prompt to save. Enter a prompt first.")
            return {'CANCELLED'}

        try:
            from ..core.templates.template_manager import (
                get_template_manager,
                PromptTemplate,
                TemplateCategory,
            )
            from ..utils.file_utils import get_addon_storage_path

            tm = get_template_manager(get_addon_storage_path())

            template = PromptTemplate(
                template_id=f"custom_{uuid.uuid4().hex[:8]}",
                name=f"Custom: {prompt[:30]}{'...' if len(prompt) > 30 else ''}",
                category=TemplateCategory.CUSTOM,
                prompt=prompt.strip(),
                negative_prompt=negative_prompt.strip(),
            )

            tm.add_custom(template)
            self.report({'INFO'}, f"Template saved: {template.name}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to save template: {str(e)}")
            return {'CANCELLED'}


# Registration
classes = (
    AIApplyTemplateOperator,
    AIRefreshTemplatesOperator,
    AISaveTemplateOperator,
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
