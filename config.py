"""Application configuration loaded from environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "user_uploads"
REELS_FOLDER = BASE_DIR / "static" / "reels"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
FFMPEG_BINARY = os.getenv("FFMPEG_BINARY", "ffmpeg")
MAX_CONTENT_LENGTH = 100 * 1024 * 1024
