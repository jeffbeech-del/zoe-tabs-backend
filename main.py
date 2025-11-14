import os
import tempfile
import subprocess
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow your GitHub Pages site to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # You can lock this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# DATA MODELS
# ----------------------------

class YouTubeRequest(BaseModel):
    youtube_url: str

class TabResponse(BaseModel):
    tab: str
    chords: list[str]
    message: Optional[str] = None

# ----------------------------
# YOUTUBE AUDIO DOWNLOAD
# ----------------------------

def download_youtube_audio(youtube_url: str) -> str:
    """
    Downloads YouTube audio using yt-dlp as WAV.
    Returns filepath to the WAV file.
    """

    # Temporary folder for output
    tmp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(tmp_dir, "audio.%(ext)s")

    # Absolute path to cookies file
    cookie_path = os.path.join(os.path.dirname(__file__), "www.youtube.com_cookies.txt")

    # yt-dlp command
    cmd = [
        "yt-dlp",
        "--cookies", cookie_path,
        "--extractor-args", "youtube:player_client=default",
        "--no-check-certificate",
        "-x",
        "--audio-format", "wav",
        "-o", out_tmpl,
        youtube_url,
    ]

    # Run downloader
    subprocess.run(cmd, check=True, timeout=25)

    # Find the resulting WAV file
    for fname in os.listdir(tmp_dir):
        if fname.endswith(".wav"):
            return os.path.join(tmp_dir, fname)

    raise RuntimeError("No wav file produced by yt-dlp")

# ----------------------------
# (FAKE) TAB GENERATOR
# ----------------------------

def fake_generate_tabs(wav_path: str):
    """
    Placeholder TAB generator.
    Replace later with a real model.
    """
    chords = ["C", "G", "Am", "F"]
    tab = "(fake ukulele tab here)"
    return chords, tab

# ----------------------------
# API ROUTES
# ----------------------------

@app.get("/")
def home():
    return {"status": "OK", "message": "Zoë Tabs Backend Running"}

@app.post("/api/youtube-to-tabs", response_model=TabResponse)
def youtube_to_tabs(req: YouTubeRequest):

    try:
        wav_file = download_youtube_audio(req.youtube_url)
    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR (downloader): {str(e)}"
        )

    try:
        chords, tab = fake_generate_tabs(wav_file)
        return TabResponse(tab=tab, chords=chords, message="OK")

    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR (tab generator): {str(e)}"
        )

# ----------------------------
# END OF FILE
# ----------------------------
