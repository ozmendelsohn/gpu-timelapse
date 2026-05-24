from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.upload import router as upload_router
from routes.process import router as process_router
from routes.jobs import router as jobs_router

app = FastAPI(title="GPU Timelapse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(process_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
