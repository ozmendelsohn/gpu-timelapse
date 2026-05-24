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
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

    job_id = create_job("")  # create placeholder first to get id

    dest = UPLOAD_DIR / f"{job_id}{suffix}"
    content = await file.read()
    dest.write_bytes(content)

    # update job with real path
    from services.job_manager import update_job
    update_job(job_id, input_path=str(dest))

    return JSONResponse({"job_id": job_id, "filename": file.filename, "size": len(content)})
