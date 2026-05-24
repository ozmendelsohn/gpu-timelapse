import re
import subprocess
import threading
from pathlib import Path
from typing import Literal

from .job_manager import update_job

OutputFormat = Literal["mp4", "gif", "webm"]

MAX_MULTIPLIER = 1000.0


def _get_duration(input_path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "no output"
        raise RuntimeError(f"ffprobe could not read video duration: {detail}")
    return float(result.stdout.strip())


def _get_frame_count(input_path: str) -> int:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-count_packets",
            "-show_entries", "stream=nb_read_packets",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path,
        ],
        capture_output=True,
        text=True,
    )
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0  # progress bar will stay indeterminate if frame count is unavailable


def _build_video_cmd(
    input_path: str,
    output_path: str,
    multiplier: float,
    fmt: Literal["mp4", "webm"],
    drop_audio: bool,
) -> list[str]:
    vf = f"setpts=PTS/{multiplier}"

    if fmt == "mp4":
        # -pix_fmt yuv420p forces 8-bit — required for h264_nvenc which doesn't support 10-bit input
        codec_args = ["-pix_fmt", "yuv420p", "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23"]
    else:  # webm — VP9, CPU fallback (NVENC doesn't support VP9)
        codec_args = ["-pix_fmt", "yuv420p", "-c:v", "libvpx-vp9", "-crf", "33", "-b:v", "0"]

    audio_args = ["-an"] if drop_audio else ["-af", f"atempo={min(multiplier, 2.0)}"]

    return [
        "ffmpeg", "-y",
        "-hwaccel", "cuda",
        "-i", input_path,
        "-vf", vf,
        *audio_args,
        *codec_args,
        output_path,
    ]


def _build_gif_cmds(
    input_path: str,
    output_path: str,
    multiplier: float,
) -> tuple[list[str], list[str], Path]:
    vf = f"setpts=PTS/{multiplier}"
    p = Path(output_path)
    palette_path = p.parent / (p.stem + "_palette.png")

    pass1 = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"{vf},fps=15,scale=640:-1:flags=lanczos,palettegen",
        str(palette_path),
    ]
    pass2 = [
        "ffmpeg", "-y", "-i", input_path, "-i", str(palette_path),
        "-lavfi", f"{vf},fps=15,scale=640:-1:flags=lanczos[x];[x][1:v]paletteuse",
        "-an", output_path,
    ]
    return pass1, pass2, palette_path


def _run_with_progress(
    cmd: list[str],
    job_id: str,
    total_frames: int,
    offset: float = 0.0,
    weight: float = 1.0,
) -> int:
    proc = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True,
    )
    for line in proc.stderr:
        m = re.search(r"frame=\s*(\d+)", line)
        if m and total_frames:
            done = int(m.group(1))
            progress = offset + weight * min(done / total_frames, 1.0)
            update_job(job_id, progress=round(progress * 100, 1))
    proc.wait()
    return proc.returncode


def process_timelapse(
    job_id: str,
    input_path: str,
    output_path: str,
    mode: Literal["multiplier", "duration"],
    value: float,
    fmt: OutputFormat,
) -> None:
    def _run():
        try:
            duration = _get_duration(input_path)
            multiplier = value if mode == "multiplier" else duration / max(value, 0.1)
            multiplier = max(multiplier, 1.0)

            if multiplier > MAX_MULTIPLIER:
                raise ValueError(
                    f"Computed speed {multiplier:.1f}× exceeds maximum {MAX_MULTIPLIER}×"
                )

            total_frames = _get_frame_count(input_path)

            if fmt == "gif":
                pass1, pass2, palette_path = _build_gif_cmds(input_path, output_path, multiplier)
                try:
                    rc = _run_with_progress(pass1, job_id, total_frames, offset=0.0, weight=0.4)
                    if rc != 0:
                        raise RuntimeError("Palette generation failed")
                    rc = _run_with_progress(pass2, job_id, total_frames, offset=0.4, weight=0.6)
                finally:
                    palette_path.unlink(missing_ok=True)
            else:
                drop_audio = multiplier > 2.0
                cmd = _build_video_cmd(input_path, output_path, multiplier, fmt, drop_audio)
                rc = _run_with_progress(cmd, job_id, total_frames)

            if rc != 0:
                raise RuntimeError(f"FFmpeg exited with code {rc}")

            update_job(job_id, status="done", progress=100, output_path=output_path)
        except Exception as e:
            update_job(job_id, status="error", error=str(e))

    threading.Thread(target=_run, daemon=True).start()
