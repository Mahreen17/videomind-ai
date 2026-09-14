"""
Transcript loader for VideoMind AI.

Supports:
- YouTube transcripts
- Uploaded TXT transcripts
- Uploaded VTT transcripts
"""

import re
from typing import Dict, Optional

from youtube_transcript_api import YouTubeTranscriptApi


_uploaded_transcripts: Dict[str, str] = {}


class TranscriptLoader:
    """Loads transcripts from YouTube or uploaded transcript files."""

    def extract_video_id(self, video_url: str) -> Optional[str]:
        return extract_video_id(video_url)

    def get_transcript(self, video_url: str) -> dict:
        return get_transcript(video_url)

    def register_uploaded_transcript(
        self,
        video_id: str,
        text: str
    ) -> None:
        register_uploaded_transcript(video_id, text)


def extract_video_id(video_url: str) -> Optional[str]:
    """
    Extract an 11-character YouTube video ID from a URL or direct ID.
    """

    if not video_url:
        return None

    value = video_url.strip()

    # Direct video ID
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


def register_uploaded_transcript(
    video_id: str,
    text: str
) -> None:
    """
    Store an uploaded transcript temporarily using the video ID.
    """

    if not video_id:
        raise ValueError("A valid video ID is required.")

    if not text or not text.strip():
        raise ValueError("The uploaded transcript is empty.")

    _uploaded_transcripts[video_id] = text.strip()


def _clean_text(items) -> str:
    """
    Convert YouTube transcript snippets into plain text.
    """

    parts = []

    for item in items:
        if isinstance(item, dict):
            text = item.get("text", "")
        else:
            text = getattr(item, "text", "")

        if text:
            parts.append(
                str(text)
                .replace("\n", " ")
                .strip()
            )

    return " ".join(parts).strip()


def get_transcript(video_url: str) -> dict:
    """
    Retrieve a transcript from YouTube.

    If YouTube blocks the cloud server, an informative error is raised
    and the user can upload a TXT or VTT transcript instead.
    """

    video_id = extract_video_id(video_url)

    if not video_id:
        raise ValueError(
            "Invalid YouTube URL or video ID."
        )

    # Check whether a transcript was uploaded previously.
    if video_id in _uploaded_transcripts:
        return {
            "video_id": video_id,
            "text": _uploaded_transcripts[video_id],
            "source": "uploaded",
        }

    try:
        api = YouTubeTranscriptApi()

        transcript_list = api.list(video_id)

        transcript = None

        # Prefer English captions.
        for item in transcript_list:
            if getattr(item, "language_code", "") == "en":
                transcript = item
                break

        # Otherwise use the first available caption.
        if transcript is None:
            transcript = next(
                iter(transcript_list),
                None
            )

        if transcript is None:
            raise ValueError(
                "No captions are available for this video."
            )

        fetched = transcript.fetch()

        text = _clean_text(fetched)

        if not text:
            raise ValueError(
                "The transcript is empty."
            )

        return {
            "video_id": video_id,
            "text": text,
            "source": "youtube",
        }

    except Exception as error:
        raise ValueError(
            f"Transcript request failed ({type(error).__name__}): "
            f"{error}. "
            "YouTube may block cloud servers. "
            "Upload a .txt or .vtt transcript instead."
        ) from error


def get_transcript_text(video_url: str) -> str:
    """
    Return only the transcript text.
    """

    return get_transcript(video_url)["text"]


def parse_uploaded_transcript(
    file_name: str,
    content: bytes
) -> str:
    """
    Convert TXT or VTT file content into plain transcript text.
    """

    text = content.decode(
        "utf-8-sig",
        errors="replace"
    )

    # Remove WebVTT metadata and timestamps.
    if file_name.lower().endswith(".vtt"):
        lines = []

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            if line == "WEBVTT":
                continue

            if "-->" in line:
                continue

            if line.isdigit():
                continue

            # Remove simple VTT tags.
            line = re.sub(
                r"<[^>]+>",
                "",
                line
            )

            lines.append(line)

        text = " ".join(lines)

    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text