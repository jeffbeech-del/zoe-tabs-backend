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
    allow_origins=["*"],  # you can lock this down later to just your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class YouTubeRequest(BaseModel):
    youtube_url: str

class TabResponse(BaseModel):
    tab: str
    chords: list[str]
    message: Optional[str] = None


def fake_transcribe_to_uke_tab(audio_path: str) -> TabResponse:
    """
    PLACEHOLDER "AI" FUNCTION.
    ------------------------------------------------
    This is where a real ML pipeline would go:
      1. Load audio
      2. Separate stems (e.g. Demucs)
      3. Transcribe pitches (BasicPitch / Onsets & Frames)
      4. Convert notes to uke D–G–B–E
      5. Format into string lines of TAB

    For now, we'll return a dummy TAB + chords so the app is fully wired up.
    """
    demo_tab = (
        "E|-----3-----3-----2-----0-------|\n"
        "B|---0-----0-----3-----1---------|\n"
        "G|-0-----0-----2-----0-----------|\n"
        "D|-------------------------2-----|\n"
        "\n"
        "E|-----0-----0-----3-----2-------|\n"
        "B|---1-----1-----0-----3---------|\n"
        "G|-0-----0-----0-----2-----------|\n"
        "D|-------------------------0-----|\n"
    )

    demo_chords = ["G", "D", "Em", "C"]

    return TabResponse(
        tab=demo_tab,
        chords=demo_chords,
        message="Demo AI stub: wiring is working. Swap in a real transcription model when ready."
    )


def download_youtube_audio(youtube_url: str) -> str:
    """
    Download YouTube audio as a wav file using yt-dlp.
    Returns path to the downloaded wav file.
    """
    tmp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(tmp_dir, "audio.%(ext)s")

    # Use yt-dlp to get best audio as wav
   cmd = [
    "yt-dlp",
    "--cookies", "www.youtube.com_cookies.txt",
    "--extractor-args", "youtube:player_client=default",
    "--no-check-certificate",
    "-x",
    "--audio-format", "wav",
    "-o", out_tmpl,
    youtube_url,
    ]
subprocess.run(cmd, check=True, timeout=25)


    # Find the resulting wav file
    for fname in os.listdir(tmp_dir):
        if fname.endswith(".wav"):
            return os.path.join(tmp_dir, fname)

    raise RuntimeError("No wav file produced by yt-dlp")


@app.get("/")
def root():
    return {"status": "ok", "message": "Zoë Tabs AI backend is running."}


@app.post("/api/youtube-to-tabs", response_model=TabResponse)
def youtube_to_tabs(payload: YouTubeRequest):
    """
    Main endpoint:
    - Downloads audio from YouTube
    - Runs (fake) AI transcription
    - Returns uke-style TAB text + chord list
    """
    url = payload.youtube_url.strip()
    if not url:
        return TabResponse(tab="", chords=[], message="Missing YouTube URL")

    try:
        audio_path = download_youtube_audio(url)
        result = fake_transcribe_to_uke_tab(audio_path)
        return result
    except subprocess.CalledProcessError as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"yt-dlp error while fetching audio: {e}"
        )
    except Exception as e:
        return TabResponse(
            tab="",
            chords=[],
            message=f"Server error: {e}"
        )

