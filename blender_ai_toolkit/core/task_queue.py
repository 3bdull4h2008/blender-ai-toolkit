"""Task Queue for managing async generation tasks with bpy.app.timers integration."""
import threading
from enum import Enum
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    task_id: str
    task_type: str
    provider_id: str
    prompt: str
    model_id: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: str = ""
    work_func: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    _thread: Optional[threading.Thread] = field(default=None, repr=False)


class TaskQueue:
    """Thread-based task queue with bpy.app.timers dispatch for Blender."""

    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}
        self._lock = threading.Lock()
        self._poll_timer = None
        self._started = False

    def start(self):
        """Start the timer-based result dispatcher."""
        if self._started:
            return
        self._started = True
        try:
            import bpy
            self._poll_timer = bpy.app.timers.register(
                self._poll_results, first_interval=0.5, persistent=True
            )
        except (ImportError, AttributeError):
            pass

    def shutdown(self):
        """Shutdown the task queue."""
        self._started = False
        try:
            import bpy
            if self._poll_timer and bpy.app.timers.is_registered(self._poll_timer):
                bpy.app.timers.unregister(self._poll_timer)
        except (ImportError, AttributeError):
            pass
        self._tasks.clear()

    def submit(self, task_id: str, task_type: str, provider_id: str,
               prompt: str, model_id: str, work_func: Callable,
               on_complete: Callable = None):
        """Submit a new task. Runs work_func in a background thread."""
        task = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            provider_id=provider_id,
            prompt=prompt,
            model_id=model_id,
            work_func=work_func,
            on_complete=on_complete,
        )
        with self._lock:
            self._tasks[task_id] = task

        thread = threading.Thread(
            target=self._run_task, args=(task,), daemon=True
        )
        task._thread = thread
        thread.start()

    def cancel(self, task_id: str):
        """Cancel a task by ID."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                return True
        return False

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        with self._lock:
            return self._tasks.get(task_id)

    def _run_task(self, task: TaskInfo):
        """Execute the task's work function in a background thread."""
        with self._lock:
            if task.status == TaskStatus.CANCELLED:
                return
            task.status = TaskStatus.RUNNING

        try:
            result = task.work_func(task)
            with self._lock:
                if task.status == TaskStatus.CANCELLED:
                    return
                task.status = TaskStatus.COMPLETED
                task.result = result
        except Exception as e:
            with self._lock:
                if task.status == TaskStatus.CANCELLED:
                    return
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.result = {"success": False, "error": str(e)}

    def _poll_results(self):
        """Timer callback: dispatch completed tasks on main thread."""
        import bpy

        completed = []
        with self._lock:
            for task_id, task in list(self._tasks.items()):
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    completed.append(task)
                    del self._tasks[task_id]

        for task in completed:
            if task.status != TaskStatus.CANCELLED and task.on_complete:
                try:
                    task.on_complete(task)
                except Exception as e:
                    print(f"[AI Toolkit] on_complete error for {task.task_id}: {e}")

        return 0.5  # Re-register timer with 0.5s interval


# Global singleton
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
