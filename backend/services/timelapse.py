import re
import subprocess
import threading
from pathlib import Path
from typing import Literal

from .job_manager import update_job

OutputFormat = Literal["mp4", "gif", "webm"]


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
        return 0


def _build_cmd(
    input_path: str,
    output_path: str,
    multiplier: float,
    fmt: OutputFormat,
) -> list[str]:
    vf = f"setpts=PTS/{multiplier}"

    if fmt == "gif":
        palette_path = output_path.replace(".gif", "_palette.png")
        pass1 = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"{vf},fps=15,scale=640:-1:flags=lanczos,palettegen",
            palette_path,
        ]
        pass2 = [
            "ffmpeg", "-y", "-i", input_path, "-i", palette_path,
            "-lavfi", f"{vf},fps=15,scale=640:-1:flags=lanczos[x];[x][1:v]paletteuse",
            "-an", output_path,
        ]
        return (pass1, pass2)

    if fmt == "mp4":
        codec_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23"]
    else:  # webm — VP9, CPU fallback (NVENC doesn't support VP9)
        codec_args = ["-c:v", "libvpx-vp9", "-crf", "33", "-b:v", "0"]

    return [
        "ffmpeg", "-y",
        "-hwaccel", "cuda",
        "-i", input_path,
        "-vf", vf,
        "-af", f"atempo={min(multiplier, 2.0)}",  # audio: capped at 2x; high-speed drops audio in caller
        *codec_args,
        output_path,
    ]


def _run_with_progress(cmd: list[str], job_id: str, total_frames: int, offset: float = 0.0, weight: float = 1.0):
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
            update_job(job_id, status="processing", progress=0)

            duration = _get_duration(input_path)
            multiplier = value if mode == "multiplier" else duration / max(value, 0.1)
            multiplier = max(multiplier, 1.0)

            total_frames = _get_frame_count(input_path)

            cmd = _build_cmd(input_path, output_path, multiplier, fmt)

            if fmt == "gif":
                pass1, pass2 = cmd
                rc = _run_with_progress(pass1, job_id, total_frames, offset=0.0, weight=0.4)
                if rc != 0:
                    raise RuntimeError("Palette generation failed")
                rc = _run_with_progress(pass2, job_id, total_frames, offset=0.4, weight=0.6)
            else:
                if multiplier > 2.0:
                    # Drop audio for high speeds — atempo only supports up to 2x per stage
                    idx_af = cmd.index("-af") if "-af" in cmd else -1
                    if idx_af != -1:
                        cmd = cmd[:idx_af] + cmd[idx_af + 2:]
                    cmd.extend(["-an"])
                rc = _run_with_progress(cmd, job_id, total_frames)

            if rc != 0:
                raise RuntimeError(f"FFmpeg exited with code {rc}")

            update_job(job_id, status="done", progress=100, output_path=output_path)
        except Exception as e:
            update_job(job_id, status="error", error=str(e))

    threading.Thread(target=_run, daemon=True).start()
