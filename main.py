import os
import tempfile
import subprocess
from typing import Optional, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow GitHub Pages frontend to call our backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # you can lock down later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------
# Models
# -----------------------------------------------------------

class YouTubeRequest(BaseModel):
    youtube_url: str

class TabResponse(BaseModel):
    tab: str
    chords: List[str]
    message: Optional[str] = None


# -----------------------------------------------------------
# YouTube Audio Downloader using yt-dlp + cookies
# -----------------------------------------------------------

def download_youtube_audio(youtube_url: str) -> str:
    """
    Downloads YouTube audio as WAV using yt-dlp and cookies.
    Returns the path to the WAV file.
    """
    tmp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(tmp_dir, "audio.%(ext)s")

    cmd = [
        "yt-dlp",
        "--cookies", "www.youtube.com_cookies.txt",  # your uploaded cookie file
        "--extractor-args", "youtube:player_client=default",
        "--no-check-certificate",
        "-x",
        "--audio-format", "wav",
        "-o", out_tmpl,
        youtube_url,
    ]

    # Run with timeout to prevent freezing
    subprocess.run(cmd, check=True, timeout=25)

    # Find resulting WAV file
    for fname in os.listdir(tmp_dir):
        if fname.endswith(".wav"):
            return os.path.join(tmp_dir, fname)

    raise RuntimeError("yt-dlp failed to produce WAV output")


# -----------------------------------------------------------
# Dummy TAB Generator (replace with real AI later)
# -----------------------------------------------------------

def generate_tabs_from_audio(audio_path: str):
    """
    TEMPORARY:
    Dummy tab & chord generator until real AI is added.
    """

    sample_tab = """
    A|-------0-----------0--------|
    E|---2-------2---2-------2----|
    C|-1---1---1---1---1---1------|
    G|-----------------------------|
    """

    sample_chords = ["C", "Em", "G", "D"]

    return sample_tab, sample_chords


# -----------------------------------------------------------
# API ROUTES
# -----------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "Zoë Tabs AI backend is running."}


@app.post("/api/youtube-to-tabs", response_model=TabResponse)
def youtube_to_tabs(req: YouTubeRequest):
    """
    Main endpoint: fetch YouTube audio → generate Tabs → return
    """
    try:
        wav_path = download_youtube_audio(req.youtube_url)
        tab, chords = generate_tabs_from_audio(wav_path)

        return TabResponse(
            tab=tab,
            chords=chords,
            message="Success (demo output — AI coming soon!)"
        )

    except subprocess.TimeoutExpired:
        return TabResponse(
            tab="",
            chords=[],
            message="ERROR: yt-dlp timed out. Try another video."
        )

    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"ERROR: {str(e)}"
        )
