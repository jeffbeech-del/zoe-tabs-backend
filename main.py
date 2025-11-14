import os
import tempfile
import subprocess
from typing import Optional, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI()

# Allow GitHub Pages frontend
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
# Download MP4 → Convert to WAV
# ----------------------------

def download_youtube_audio(youtube_url: str) -> str:
    """
    Downloads video (MP4) using yt-dlp + cookies.
    Then converts MP4 → WAV using ffmpeg.
    """

    tmp_dir = tempfile.mkdtemp()

    mp4_path = os.path.join(tmp_dir, "video.mp4")
    wav_path = os.path.join(tmp_dir, "audio.wav")

    cookie_path = os.path.join(os.path.dirname(__file__), "www.youtube.com_cookies.txt")

    # STEP 1 — download the MP4 video (NOT audio-only)
    cmd = [
        "yt-dlp",

        "--cookies", cookie_path,

        # iOS client (still semi-working with video)
        "--extractor-args", "youtube:player_client=ios",

        # mimic iOS app
        "--user-agent", "com.google.ios.youtube/19.45.3 (iPhone14,2; U; CPU iOS 17_5 like Mac OS X)",
        "--add-header", "X-YouTube-Client-Name:5",
        "--add-header", "X-YouTube-Client-Version:19.45.3",

        "--force-ipv4",
        "--no-check-certificate",
        "--no-mtime",
        "--no-overwrites",

        "-f", "mp4",
        "-o", mp4_path,

        youtube_url,
    ]

    subprocess.run(cmd, check=True, timeout=30)

    # STEP 2 — convert MP4 → WAV using ffmpeg
    convert_cmd = [
        "ffmpeg",
        "-i", mp4_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        wav_path,
    ]

    subprocess.run(convert_cmd, check=True)

    if os.path.exists(wav_path):
        return wav_path

    raise RuntimeError("ffmpeg failed to produce WAV")


# ----------------------------
# Demo TAB Generator
# ----------------------------

def fake_generate_tabs(audio_path: str) -> tuple[List[str], str]:
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
    return {"status": "ok", "message": "Zoë Tabs Backend Running (MP4 mode)"}


@app.post("/api/youtube-to-tabs", response_model=TabResponse)
def youtube_to_tabs(req: YouTubeRequest):

    # STEP 1 — Download MP4 → Convert to WAV
    try:
        wav_file = download_youtube_audio(req.youtube_url)
    except subprocess.TimeoutExpired:
        return TabResponse(tab="", chords=[], message="ERROR: yt-dlp timed out (>30s).")
    except subprocess.CalledProcessError as e:
        return TabResponse(tab="", chords=[], message=f"ERROR: yt-dlp exited {e.returncode}.")
    except Exception as e:
        return TabResponse(tab="", chords=[], message=f"ERROR: {str(e)}")

    # STEP 2 — Fake tab generator
    try:
        chords, tab = fake_generate_tabs(wav_file)
        return TabResponse(tab=tab, chords=chords, message="OK")
    except Exception as e:
        return TabResponse(tab="", chords=[], message=f"ERROR (tab gen): {str(e)}")
