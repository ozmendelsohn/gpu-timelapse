import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from services.job_manager import create_job

router = APIRouter()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv", ".m4v"}
@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    safe_name = Path(file.filename or "").name  # strip any directory components
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix or '(none)'}")

    content = await file.read()

    # Generate the ID and write the file BEFORE registering the job so a disk
    # failure never leaves an orphaned job record with an empty input_path.
    job_id = str(uuid.uuid4())
    dest = UPLOAD_DIR / f"{job_id}{suffix}"

    try:
        await asyncio.to_thread(dest.write_bytes, content)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    create_job(str(dest), job_id=job_id)

    return JSONResponse({"job_id": job_id, "filename": safe_name, "size": len(content)})
