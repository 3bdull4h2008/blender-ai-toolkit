"""
Notification Manager for showing popup notifications in Blender.
Provides success, error, warning, and info notifications via console and UI.
"""

import bpy
from typing import Optional
from datetime import datetime


class NotificationManager:
    """
    Manages popup notifications in Blender.
    Outputs to console and syncs with bpy.types.Scene.ai_toolkit.notification_list.
    """

    def __init__(self):
        self._history: list = []

    def success(self, title: str, message: str) -> None:
        """Show success notification."""
        print(f"[AI Toolkit] SUCCESS | {title}: {message}")
        self._add_to_history("success", title, message)

    def error(self, title: str, message: str) -> None:
        """Show error notification."""
        print(f"[AI Toolkit] ERROR   | {title}: {message}")
        self._add_to_history("error", title, message)

    def warning(self, title: str, message: str) -> None:
        """Show warning notification."""
        print(f"[AI Toolkit] WARNING | {title}: {message}")
        self._add_to_history("warning", title, message)

    def info(self, title: str, message: str) -> None:
        """Show info notification."""
        print(f"[AI Toolkit] INFO    | {title}: {message}")
        self._add_to_history("info", title, message)

    def _add_to_history(self, notif_type: str, title: str, message: str) -> None:
        """Add notification to history for UI display."""
        entry = {
            "type": notif_type,
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self._history.append(entry)
        # Keep only last 50 notifications
        if len(self._history) > 50:
            self._history = self._history[-50:]

        # Sync to Blender UI if available
        try:
            scene = bpy.context.scene
            if scene and hasattr(scene, "ai_toolkit"):
                props = scene.ai_toolkit
                item = props.notification_list.add()
                item.title = title
                item.message = message
                item.notif_type = notif_type
                item.timestamp = entry["timestamp"]
                item.read = False
                props.unread_notifications += 1
                # Keep UI list in sync with history
                if len(props.notification_list) > 50:
                    props.notification_list.remove(0)
        except Exception:
            pass

    def get_history(self) -> list:
        """Get notification history."""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear notification history."""
        self._history.clear()
        try:
            scene = bpy.context.scene
            if scene and hasattr(scene, "ai_toolkit"):
                props = scene.ai_toolkit
                props.notification_list.clear()
                props.unread_notifications = 0
        except Exception:
            pass


# =============================================================================
# Global Singleton
# =============================================================================

_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get or create the global NotificationManager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
