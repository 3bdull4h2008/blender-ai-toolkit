"""
AI Chat Operators — real LLM integration with conversation memory,
scene context injection, and safe code execution.
"""
import re
import ast
import bpy
from bpy.types import Operator


def _get_scene_context() -> str:
    """Build a text summary of the current scene for LLM context."""
    scene = bpy.context.scene
    lines = [f"Scene: {scene.name}"]

    objects = []
    for obj in scene.objects:
        info = f"  - {obj.name} (type={obj.type}"
        if obj.type == 'MESH':
            mesh = obj.data
            info += f", verts={len(mesh.vertices)}, faces={len(mesh.polygons)}"
        info += f", loc=({obj.location.x:.1f}, {obj.location.y:.1f}, {obj.location.z:.1f}))"
        objects.append(info)

    if objects:
        lines.append("Objects:")
        lines.extend(objects[:30])  # Limit to 30 objects for context length
        if len(scene.objects) > 30:
            lines.append(f"  ... and {len(scene.objects) - 30} more objects")

    materials = [m.name for m in bpy.data.materials]
    if materials:
        lines.append(f"Materials: {', '.join(materials[:15])}")

    cameras = [c.name for c in bpy.data.cameras]
    if cameras:
        lines.append(f"Cameras: {', '.join(cameras)}")

    lights = [l.name for l in bpy.data.lights]
    if lights:
        lines.append(f"Lights: {', '.join(lights)}")

    return "\n".join(lines)


def _extract_python_blocks(text: str) -> list:
    """Extract ```python ... ``` code blocks from text."""
    pattern = r"```(?:python)?\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [m.strip() for m in matches]


def _validate_code(code: str) -> tuple:
    """Validate Python code with AST. Returns (is_valid, error_message)."""
    try:
        tree = ast.parse(code)
        # Block dangerous imports/operations
        dangerous = {"subprocess", "shutil", "ctypes", "importlib", "socket", "http"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in dangerous:
                        return False, f"Blocked import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in dangerous:
                    return False, f"Blocked import: {node.module}"
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e}"


def _execute_code(code: str) -> tuple:
    """Execute Python code in Blender context. Returns (success, output/error)."""
    is_valid, err = _validate_code(code)
    if not is_valid:
        return False, err

    try:
        exec_globals = {"bpy": bpy, "__builtins__": __builtins__}
        exec(code, exec_globals)
        return True, "Code executed successfully"
    except Exception as e:
        import traceback
        return False, traceback.format_exc()


def _retry_with_llm(context, provider, original_prompt: str, code: str, error: str, max_retries: int = 2) -> tuple:
    """Send traceback back to LLM for correction. Returns (success, fixed_code)."""
    props = context.scene.ai_toolkit

    retry_prompt = f"""The previous code execution failed with this error:

```
{error}
```

The original code was:
```python
{code}
```

Please fix the code and provide the corrected version. Only output the fixed Python code in a ```python block."""

    from ...api.base import GenerationRequest

    request = GenerationRequest(
        prompt=retry_prompt,
        model_id="",
        provider_id=props.llm_provider,
        params={
            "system_prompt": "You are a Blender Python expert. Fix the code error and provide only the corrected code.",
            "history": [
                {"role": "user", "content": original_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        },
    )

    try:
        result = provider.generate(request)
        if result.success:
            blocks = _extract_python_blocks(result.text_response)
            if blocks:
                return True, blocks[-1]
    except Exception:
        pass

    return False, code


class AIChatOperator(Operator):
    """Send a message to the AI chat assistant."""
    bl_idname = "ai.chat"
    bl_label = "Send to AI"
    bl_description = "Send your message to the AI assistant"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.llm_prompt.strip():
            self.report({'WARNING'}, "Please enter a message")
            return {'CANCELLED'}

        # Get provider
        prefs = context.preferences.addons.get("blender_ai_toolkit")
        if not prefs:
            self.report({'ERROR'}, "AI Toolkit preferences not found")
            return {'CANCELLED'}

        from ...api.llm import get_or_create_llm_provider

        provider = get_or_create_llm_provider(props.llm_provider, prefs.preferences)
        if not provider or not provider.is_configured:
            self.report({'WARNING'}, f"Provider {props.llm_provider} not configured")
            return {'CANCELLED'}

        # Build conversation history
        history = []
        for item in props.history_list:
            history.append({"role": "user", "content": item.prompt})
            if item.model_id:  # model_id is repurposed as response field
                history.append({"role": "assistant", "content": item.model_id})

        # Scene context
        scene_ctx = _get_scene_context()

        from ...api.base import GenerationRequest

        request = GenerationRequest(
            prompt=props.llm_prompt,
            model_id="",
            provider_id=props.llm_provider,
            params={
                "system_prompt": props.llm_system_prompt + f"\n\nCurrent Blender Scene:\n{scene_ctx}",
                "history": history,
                "temperature": props.llm_temperature,
                "max_tokens": props.llm_max_tokens,
            },
        )

        # Store user message in history
        hist_item = props.history_list.add()
        hist_item.prompt = props.llm_prompt
        hist_item.task_type = "chat"
        hist_item.provider_id = props.llm_provider

        props.is_generating = True
        props.status_message = "Thinking..."

        try:
            result = provider.generate(request)

            if result.success:
                props.llm_response = result.text_response
                # Store response in history (using model_id as response storage)
                hist_item.model_id = result.text_response[:500]
                props.status_message = "Response received"

                # Auto-execute code if enabled
                if props.llm_execute_code:
                    blocks = _extract_python_blocks(result.text_response)
                    if blocks:
                        code = blocks[-1]  # Execute last code block
                        success, output = _execute_code(code)

                        # Error retry: send traceback back to LLM
                        if not success and props.llm_retry_on_error:
                            for attempt in range(2):
                                fixed_success, fixed_code = _retry_with_llm(
                                    context, provider, props.llm_prompt, code, output
                                )
                                if fixed_success:
                                    success, output = _execute_code(fixed_code)
                                    if success:
                                        break
                                    code = fixed_code
                                else:
                                    break

                        if success:
                            props.status_message = "Code executed successfully"
                        else:
                            props.status_message = f"Code error: {output[:100]}"
            else:
                props.llm_response = f"Error: {result.error}"
                props.status_message = f"Error: {result.error[:100]}"

            props.llm_prompt = ""
            props.is_generating = False
            self.report({'INFO'}, props.status_message)
            return {'FINISHED'}

        except Exception as e:
            props.is_generating = False
            props.status_message = f"Error: {str(e)}"
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}


class AIChatClearHistoryOperator(Operator):
    """Clear the chat history and response."""
    bl_idname = "ai.chat_clear_history"
    bl_label = "Clear History"
    bl_description = "Clear chat history and current response"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit
        props.llm_response = ""
        props.history_list.clear()
        props.history_list_index = 0
        self.report({'INFO'}, "Chat cleared")
        return {'FINISHED'}


class AIChatExecuteCodeOperator(Operator):
    """Execute Blender Python code from the last AI response."""
    bl_idname = "ai.chat_execute_code"
    bl_label = "Execute Code"
    bl_description = "Extract and execute Blender Python code from AI response"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.llm_response:
            self.report({'WARNING'}, "No response to extract code from")
            return {'CANCELLED'}

        blocks = _extract_python_blocks(props.llm_response)
        if not blocks:
            self.report({'WARNING'}, "No Python code blocks found in response")
            return {'CANCELLED'}

        # Execute the last code block
        code = blocks[-1]
        success, output = _execute_code(code)

        if success:
            self.report({'INFO'}, f"Code executed: {output}")
        else:
            self.report({'ERROR'}, f"Execution failed: {output}")

        return {'FINISHED'}


# =============================================================================
# Registration
# =============================================================================

classes = (
    AIChatOperator,
    AIChatClearHistoryOperator,
    AIChatExecuteCodeOperator,
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
