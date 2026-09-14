"""YouTube and uploaded transcript loader for VideoMind AI."""
import re
from typing import Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi

_uploaded_transcripts: Dict[str, str] = {}


def extract_video_id(video_url: str) -> Optional[str]:
    if not video_url:
        return None
    value = video_url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    patterns = [
        r"[?&]v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/(?:embed|shorts|live)/([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    return None


def register_uploaded_transcript(video_id: str, text: str) -> None:
    if not text or not text.strip():
        raise ValueError("The uploaded transcript is empty.")
    _uploaded_transcripts[video_id] = text.strip()


def _clean_text(items) -> str:
    parts = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text", "")
        else:
            text = getattr(item, "text", "")
        if text:
            parts.append(str(text).replace("\n", " ").strip())
    return " ".join(parts).strip()


def get_transcript(video_url: str) -> dict:
    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL or video ID.")

    if video_id in _uploaded_transcripts:
        return {"video_id": video_id, "text": _uploaded_transcripts[video_id], "source": "uploaded"}

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        transcript = None
        for item in transcript_list:
            if getattr(item, "language_code", "") == "en":
                transcript = item
                break
        if transcript is None:
            transcript = next(iter(transcript_list), None)
        if transcript is None:
            raise ValueError("No captions are available for this video.")
        fetched = transcript.fetch()
        text = _clean_text(fetched)
        if not text:
            raise ValueError("The transcript is empty.")
        return {"video_id": video_id, "text": text, "source": "youtube"}
    except Exception as error:
        raise ValueError(
            f"Transcript request failed ({type(error).__name__}): {error}. "
            "YouTube may block cloud servers. Upload a .txt or .vtt transcript instead."
        ) from error


def get_transcript_text(video_url: str) -> str:
    return get_transcript(video_url)["text"]


def parse_uploaded_transcript(file_name: str, content: bytes) -> str:
    text = content.decode("utf-8-sig", errors="replace")
    if file_name.lower().endswith(".vtt"):
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line == "WEBVTT" or "-->" in line or line.isdigit():
                continue
            lines.append(re.sub(r"<[^>]+>", "", line))
        text = " ".join(lines)
    return re.sub(r"\s+", " ", text).strip()
