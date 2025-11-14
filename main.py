import os
import tempfile
import subprocess
from typing import Optional, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow your GitHub Pages frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can lock this to your domain later
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
# YouTube audio download
# ----------------------------

def download_youtube_audio(youtube_url: str) -> str:
    """
    Download YouTube audio as a WAV file using yt-dlp and cookies.
    Returns path to the downloaded WAV file.
    """

    # Temporary folder for output
    tmp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(tmp_dir, "audio.%(ext)s")

    # Absolute path to cookies file in the same folder as this script
    cookie_path = os.path.join(os.path.dirname(__file__), "www.youtube.com_cookies.txt")

    cmd = [
        "yt-dlp",
        "--cookies", cookie_path,
        "--extractor-args", "youtube:player_client=tv,player_skip=web",
        "--no-check-certificate",
        "-x",
        "--audio-format", "wav",
        "-o", out_tmpl,
        youtube_url,
    ]

    # Run downloader with 30s timeout
    subprocess.run(cmd, check=True, timeout=30)

    # Find resulting WAV file
    for fname in os.listdir(tmp_dir):
        if fname.endswith(".wav"):
            return os.path.join(tmp_dir, fname)

    raise RuntimeError("No wav file produced by yt-dlp")


# ----------------------------
# Temporary fake TAB generator
# ----------------------------

def fake_generate_tabs(audio_path: str) -> tuple[List[str], str]:
    """
    Placeholder tab generator.
    Replace this with a real model later.
    """
    demo_chords = ["C", "G", "Am", "F"]
    demo_tab = (
        "A|-----0-----------0-----------|\n"
        "E|---3---3-------3---3---------|\n"
        "C|-0-------0---2-------2-------|\n"
        "G|-----------------------------|\n"
    )
    return demo_chords, demo_tab


# ----------------------------
# Routes
# ----------------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "Zoë Tabs AI backend is running."}


@app.post("/api/youtube-to-tabs", response_model=TabResponse)
def youtube_to_tabs(req: YouTubeRequest) -> TabResponse:
    """
    Main endpoint:
    1. Download YouTube audio with yt-dlp
    2. Generate (fake for now) ukulele tab + chords
    3. Return JSON
    """
    try:
        wav_path = download_youtube_audio(req.youtube_url)
    except subprocess.TimeoutExpired:
        return TabResponse(
            tab="",
            chords=[],
            message="ERROR (downloader): yt-dlp timed out (over 30s). Try a shorter video."
        )
    except subprocess.CalledProcessError as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR (downloader): yt-dlp failed with exit code {e.returncode}."
        )
    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR (downloader): {e}"
        )

    try:
        chords, tab = fake_generate_tabs(wav_path)
        return TabResponse(
            tab=tab,
            chords=chords,
            message="OK (demo TAB – AI transcription coming next)."
        )
    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR (tab generator): {e}"
        )
