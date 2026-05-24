import uuid
from dataclasses import dataclass
from typing import Literal

JobStatus = Literal["pending", "processing", "done", "error"]


@dataclass
class JobState:
    job_id: str
    status: JobStatus = "pending"
    progress: float = 0.0
    input_path: str = ""
    output_path: str = ""
    error: str = ""


_jobs: dict[str, JobState] = {}


def create_job(input_path: str, job_id: str | None = None) -> str:
    if job_id is None:
        job_id = str(uuid.uuid4())
    _jobs[job_id] = JobState(job_id=job_id, input_path=input_path)
    return job_id


def get_job(job_id: str) -> JobState | None:
    return _jobs.get(job_id)


def update_job(job_id: str, **kwargs) -> None:
    job = _jobs.get(job_id)
    if job is None:
        return
    for k, v in kwargs.items():
        setattr(job, k, v)
