from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.job_manager import get_job, update_job
from services.timelapse import process_timelapse, OutputFormat, MAX_MULTIPLIER

router = APIRouter()
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

EXT_MAP = {"mp4": ".mp4", "gif": ".gif", "webm": ".webm"}


class ProcessRequest(BaseModel):
    job_id: str
    mode: Literal["multiplier", "duration"]
    value: float = Field(gt=0, le=MAX_MULTIPLIER)
    format: OutputFormat = "mp4"


@router.post("/process")
async def start_processing(req: ProcessRequest):
    job = get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "processing":
        raise HTTPException(status_code=409, detail="Job already processing")
    if not job.input_path:
        raise HTTPException(status_code=400, detail="Upload incomplete — please upload again")

    # Set status synchronously before the thread starts to close the TOCTOU window.
    update_job(req.job_id, status="processing", progress=0)

    ext = EXT_MAP.get(req.format, ".mp4")
    output_path = str(OUTPUT_DIR / f"{req.job_id}_out{ext}")

    process_timelapse(
        job_id=req.job_id,
        input_path=job.input_path,
        output_path=output_path,
        mode=req.mode,
        value=req.value,
        fmt=req.format,
    )

    return {"job_id": req.job_id, "status": "processing"}
