"""Async job manager with history tracking and re-download capability."""
import os
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobInfo:
    """Information about a generation job."""
    job_id: str
    job_type: str  # model_3d, image, material, hdri
    provider: str
    prompt: str
    status: str = "pending"
    created_at: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0
    duration: float = 0.0
    output_files: List[str] = None
    error: str = ""
    params: Dict = None

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []
        if self.params is None:
            self.params = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'JobInfo':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class JobManager:
    """Manages async generation jobs with history tracking."""

    def __init__(self, storage_path: str = ""):
        self.storage_path = storage_path
        self._jobs: Dict[str, JobInfo] = {}
        self._history: List[JobInfo] = []
        self._load_history()

    def create_job(self, job_id: str, job_type: str, provider: str,
                   prompt: str, params: Dict = None) -> JobInfo:
        """Create a new job."""
        job = JobInfo(
            job_id=job_id,
            job_type=job_type,
            provider=provider,
            prompt=prompt,
            status=JobStatus.PENDING.value,
            params=params or {},
        )
        self._jobs[job_id] = job
        self._history.append(job)
        self._save_history()
        return job

    def start_job(self, job_id: str):
        """Mark a job as started."""
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.RUNNING.value
            job.started_at = time.time()
            self._save_history()

    def complete_job(self, job_id: str, output_files: List[str] = None):
        """Mark a job as completed."""
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED.value
            job.completed_at = time.time()
            job.duration = job.completed_at - job.started_at if job.started_at else 0
            if output_files:
                job.output_files = output_files
            self._save_history()

    def fail_job(self, job_id: str, error: str):
        """Mark a job as failed."""
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED.value
            job.completed_at = time.time()
            job.duration = job.completed_at - job.started_at if job.started_at else 0
            job.error = error
            self._save_history()

    def cancel_job(self, job_id: str):
        """Cancel a job."""
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.CANCELLED.value
            job.completed_at = time.time()
            self._save_history()

    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def get_active_jobs(self) -> List[JobInfo]:
        """Get all active (pending/running) jobs."""
        return [
            j for j in self._jobs.values()
            if j.status in (JobStatus.PENDING.value, JobStatus.RUNNING.value)
        ]

    def get_history(self, limit: int = 50) -> List[JobInfo]:
        """Get job history, most recent first."""
        return sorted(self._history, key=lambda j: j.created_at, reverse=True)[:limit]

    def get_completed_jobs(self) -> List[JobInfo]:
        """Get all completed jobs."""
        return [j for j in self._history if j.status == JobStatus.COMPLETED.value]

    def get_failed_jobs(self) -> List[JobInfo]:
        """Get all failed jobs."""
        return [j for j in self._history if j.status == JobStatus.FAILED.value]

    def clear_history(self):
        """Clear job history."""
        self._history.clear()
        self._jobs.clear()
        self._save_history()

    def _load_history(self):
        """Load history from disk."""
        if not self.storage_path:
            return

        filepath = os.path.join(self.storage_path, "job_history.json")
        if not os.path.exists(filepath):
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for item in data:
                job = JobInfo.from_dict(item)
                self._history.append(job)
                self._jobs[job.job_id] = job
        except (json.JSONDecodeError, IOError) as e:
            print(f"[AI Toolkit] Failed to load job history: {e}")

    def _save_history(self):
        """Save history to disk."""
        if not self.storage_path:
            return

        filepath = os.path.join(self.storage_path, "job_history.json")
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            data = [j.to_dict() for j in self._history[-100:]]  # Keep last 100
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[AI Toolkit] Failed to save job history: {e}")

    def re_download(self, job_id: str, dest_dir: str) -> List[str]:
        """Re-download files from a completed job."""
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.COMPLETED.value:
            return []

        if not job.output_files:
            return []

        from ..api.http_client import get_http_client
        client = get_http_client()

        downloaded = []
        os.makedirs(dest_dir, exist_ok=True)

        for i, url in enumerate(job.output_files):
            if url.startswith("http"):
                ext = ".glb" if job.job_type == "model_3d" else ".png"
                filename = f"{job.job_id}_{i}{ext}"
                filepath = os.path.join(dest_dir, filename)
                if client.download(url, filepath):
                    downloaded.append(filepath)

        return downloaded


# Global singleton
_job_manager: Optional[JobManager] = None


def get_job_manager(storage_path: str = "") -> JobManager:
    """Get or create the global JobManager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager(storage_path)
    return _job_manager
