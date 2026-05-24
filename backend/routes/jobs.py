from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services.job_manager import get_job

router = APIRouter()

MIME_MAP = {".mp4": "video/mp4", ".gif": "image/gif", ".webm": "video/webm"}


@router.get("/jobs/{job_id}/status")
async def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": job.status, "progress": job.progress, "error": job.error}


@router.get("/jobs/{job_id}/download")
async def download_output(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "done":
        raise HTTPException(status_code=400, detail="Job not complete")
    if not job.output_path:
        raise HTTPException(status_code=404, detail="Output file not found")

    path = Path(job.output_path)
    if not path.is_file():  # is_file() rejects directories and non-existent paths
        raise HTTPException(status_code=404, detail="Output file not found")

    media_type = MIME_MAP.get(path.suffix, "application/octet-stream")
    return FileResponse(path, media_type=media_type, filename=path.name)
