"""Transcript loader for VideoMind AI."""
import re
from typing import Dict, List, Optional
from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptLoader:
    def __init__(self):
        self.api = YouTubeTranscriptApi()

    def extract_video_id(self, url: str) -> Optional[str]:
        if not url:
            return None
        value = url.strip()
        patterns = [
            r"(?:v=)([A-Za-z0-9_-]{11})",
            r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
            r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",
            r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
            r"(?:youtube\.com/live/)([A-Za-z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, value)
            if match:
                return match.group(1)
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
            return value
        return None

    def get_transcript(self, video_url: str, languages: Optional[List[str]] = None) -> List[Dict]:
        video_id = self.extract_video_id(video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL. Please provide a valid YouTube video link.")
        languages = languages or ["en", "en-US", "en-GB"]
        try:
            transcript_list = self.api.list(video_id)
            transcript = None
            try:
                transcript = transcript_list.find_manually_created_transcript(languages)
            except Exception:
                pass
            if transcript is None:
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                except Exception:
                    pass
            if transcript is None:
                available = list(transcript_list)
                if not available:
                    raise ValueError("This video has no available caption tracks.")
                transcript = available[0]
            fetched = transcript.fetch()
            results = []
            for item in fetched:
                if hasattr(item, "text"):
                    results.append({"text": item.text, "start": item.start, "duration": item.duration})
                else:
                    results.append({"text": item.get("text", ""), "start": item.get("start", 0), "duration": item.get("duration", 0)})
            if not results:
                raise ValueError("The transcript was empty.")
            return results
        except Exception as e:
            error_type = type(e).__name__
            error_details = str(e).strip() or "No additional details were provided."
            print(f"Transcript error: {error_type}: {error_details}")
            raise ValueError(
                f"Transcript request failed ({error_type}): {error_details}\n\n"
                "If this video has captions and works locally, YouTube may be blocking "
                "transcript requests from the deployed server. Please try again later "
                "or use another captioned video."
            ) from e

    def get_transcript_text(self, video_url: str) -> str:
        transcript = self.get_transcript(video_url)
        return "\n".join(item["text"] for item in transcript if item.get("text"))
