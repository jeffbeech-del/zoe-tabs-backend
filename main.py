import os
import tempfile
import subprocess
from typing import Optional, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow GitHub Pages frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Models
# ----------------------------

class YouTubeRequest(BaseModel):
    youtube_url: str

class TabResponse(BaseModel):
    tab: str
    chords: List[str]
    message: Optional[str] = None


# ----------------------------
# YouTube Downloader (yt-dlp)
# ----------------------------

def download_youtube_audio(youtube_url: str) -> str:
    """
    Downloads YouTube audio as WAV using yt-dlp + cookies.
    Uses the iOS YouTube client (the only one still working as of Nov 2025).
    """

    tmp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(tmp_dir, "audio.%(ext)s")

    cookie_path = os.path.join(os.path.dirname(__file__), "www.youtube.com_cookies.txt")

    cmd = [
        "yt-dlp",

        # Cookie handling
        "--cookies", cookie_path,

        # Working YouTube client (as of Nov 2025)
        "--extractor-args", "youtube:player_client=ios,player_skip=web",

        # Pretend to be the real iOS YouTube app
        "--user-agent", "com.google.ios.youtube/19.45.3 (iPhone14,2; U; CPU iOS 17_5 like Mac OS X)",
        "--add-header", "X-YouTube-Client-Name:5",
        "--add-header", "X-YouTube-Client-Version:19.45.3",

        # Anti-429 stability flags
        "--compat-options", "no-youtube-unavailable-videos",
        "--force-ipv4",
        "--no-check-certificate",
        "--no-overwrites",
        "--no-mtime",

        # Extract audio → WAV
        "-x",
        "--audio-format", "wav",
        "-o", out_tmpl,

        youtube_url,
    ]

    # Run yt-dlp with 30 second timeout
    subprocess.run(cmd, check=True, timeout=30)

    # Find resulting WAV file
    for fname in os.listdir(tmp_dir):
        if fname.endswith(".wav"):
            return os.path.join(tmp_dir, fname)

    raise RuntimeError("yt-dlp completed but no WAV file was produced.")


# ----------------------------
# Fake TAB generator
# ----------------------------

def fake_generate_tabs(audio_path: str) -> tuple[List[str], str]:
    """
    Placeholder tab generator.
    Replace later with your actual AI model.
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
# Routes
# ----------------------------

@app.get("/")
def home():
    return {"status": "ok", "message": "Zoë Tabs Backend Running"}


@app.post("/api/youtube-to-tabs", response_model=TabResponse)
def youtube_to_tabs(req: YouTubeRequest):
    """
    1. Downloads YouTube audio
    2. Generates (fake) TAB + chords
    3. Returns result
    """

    # Step 1 — Attempt yt-dlp download
    try:
        wav_path = download_youtube_audio(req.youtube_url)

    except subprocess.TimeoutExpired:
        return TabResponse(
            tab="",
            chords=[],
            message="ERROR: yt-dlp timeout (>30s). Try a shorter video."
        )

    except subprocess.CalledProcessError as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR: yt-dlp failed (exit {e.returncode})."
        )

    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR: {str(e)}"
        )

    # Step 2 — Generate demo ukulele tabs
    try:
        chords, tab = fake_generate_tabs(wav_path)
        return TabResponse(
            tab=tab,
            chords=chords,
            message="OK"
        )

    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR (tab generator): {str(e)}"
        )
