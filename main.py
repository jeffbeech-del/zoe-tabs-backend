import os
import tempfile
import subprocess
from typing import Optional, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow GitHub Pages frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Data models
# ----------------------------

class YouTubeRequest(BaseModel):
    youtube_url: str

class TabResponse(BaseModel):
    tab: str
    chords: List[str]
    message: Optional[str] = None

# ----------------------------
# Download YouTube Audio (yt-dlp)
# ----------------------------

def download_youtube_audio(youtube_url: str) -> str:
    """
    Download WAV audio from YouTube using yt-dlp + cookies.
    Uses Android client (2025 stable) and skip-web workaround.
    """

    tmp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(tmp_dir, "audio.%(ext)s")

    cookie_path = os.path.join(os.path.dirname(__file__), "www.youtube.com_cookies.txt")

    cmd = [
        "yt-dlp",

        # cookie handling
        "--cookies", cookie_path,

        # 2025 working settings
        "--extractor-args", "youtube:player_client=android,player_skip=web",
        "--compat-options", "no-youtube-unavailable-videos",

        # stabilizers for buggy videos
        "--no-check-certificate",
        "--no-overwrites",
        "--no-mtime",

        # extract WAV
        "-x",
        "--audio-format", "wav",
        "-o", out_tmpl,

        youtube_url,
    ]

    # run with 30 second limit
    subprocess.run(cmd, check=True, timeout=30)

    # find wav file
    for fname in os.listdir(tmp_dir):
        if fname.endswith(".wav"):
            return os.path.join(tmp_dir, fname)

    raise RuntimeError("yt-dlp completed but no .wav produced")

# ----------------------------
# Fake TAB generator (placeholder)
# ----------------------------

def fake_generate_tabs(audio_path: str) -> tuple[List[str], str]:
    """
    Placeholder until we add real AI transcription.
    """
    chords = ["C", "G", "Am", "F"]
    tab = (
        "A|-----0-----------0-----------|\n"
        "E|---3---3-------3---3---------|\n"
        "C|-0-------0---2-------2-------|\n"
        "G|-----------------------------|\n"
    )
    return chords, tab

# ----------------------------
# API Routes
# ----------------------------

@app.get("/")
def home():
    return {"status": "ok", "message": "Zoë Tabs Backend Running"}

@app.post("/api/youtube-to-tabs", response_model=TabResponse)
def youtube_to_tabs(req: YouTubeRequest) -> TabResponse:

    # Step 1: attempt yt-dlp download
    try:
        wav = download_youtube_audio(req.youtube_url)

    except subprocess.TimeoutExpired:
        return TabResponse(
            tab="",
            chords=[],
            message="ERROR: yt-dlp timed out (>30s). Try shorter video."
        )

    except subprocess.CalledProcessError as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR: yt-dlp failed (exit code {e.returncode})."
        )

    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR: {str(e)}"
        )

    # Step 2: generate fake tabs
    try:
        chords, tab = fake_generate_tabs(wav)
        return TabResponse(tab=tab, chords=chords, message="OK")
    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR generating tabs: {str(e)}"
        )
