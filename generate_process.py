"""Background worker that turns queued image jobs into vertical MP4 reels."""
import json
from pathlib import Path
import shutil
import subprocess
import time

import config
from text_to_audio import text_to_speech_file


def set_status(job_dir: Path, status: str, detail: str = "") -> None:
    (job_dir / "status.json").write_text(json.dumps({"status": status, "detail": detail}), encoding="utf-8")


def create_silent_audio(job_dir: Path) -> None:
    subprocess.run(
        [config.FFMPEG_BINARY, "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono", "-t", "300", str(job_dir / "audio.mp3")],
        check=True, capture_output=True, text=True,
    )


def create_reel(job_dir: Path) -> None:
    output = config.REELS_FOLDER / f"{job_dir.name}.mp4"
    subprocess.run(
        [
            config.FFMPEG_BINARY, "-y", "-f", "concat", "-safe", "0", "-i", str(job_dir / "input.txt"),
            "-i", str(job_dir / "audio.mp3"), "-vf",
            "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fps=30",
            "-c:v", "libx264", "-c:a", "aac", "-shortest", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
        ],
        check=True, capture_output=True, text=True,
    )


def process_job(job_dir: Path) -> None:
    if not shutil.which(config.FFMPEG_BINARY) and not Path(config.FFMPEG_BINARY).is_file():
        raise RuntimeError("FFmpeg was not found. Install FFmpeg or set FFMPEG_BINARY.")
    narration = (job_dir / "desc.txt").read_text(encoding="utf-8")
    try:
        text_to_speech_file(narration, job_dir.name)
    except Exception as exc:
        print(f"Narration unavailable for {job_dir.name}; using silent audio: {exc}")
        create_silent_audio(job_dir)
    create_reel(job_dir)


def queued_jobs():
    for job_dir in config.UPLOAD_FOLDER.iterdir():
        if not job_dir.is_dir():
            continue
        try:
            status = json.loads((job_dir / "status.json").read_text(encoding="utf-8")).get("status")
        except (FileNotFoundError, json.JSONDecodeError):
            # Preserve completed jobs created by the legacy worker instead of remaking them.
            status = "complete" if (config.REELS_FOLDER / f"{job_dir.name}.mp4").is_file() else "queued"
        if status == "queued":
            yield job_dir


if __name__ == "__main__":
    config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    config.REELS_FOLDER.mkdir(parents=True, exist_ok=True)
    while True:
        for job_dir in queued_jobs():
            set_status(job_dir, "processing")
            try:
                process_job(job_dir)
            except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
                detail = exc.stderr[-1000:] if isinstance(exc, subprocess.CalledProcessError) and exc.stderr else str(exc)
                set_status(job_dir, "failed", detail)
                print(f"Failed to process {job_dir.name}: {detail}")
            else:
                set_status(job_dir, "complete")
                print(f"Created reel for {job_dir.name}")
        time.sleep(4)
