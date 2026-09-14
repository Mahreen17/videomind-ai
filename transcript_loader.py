"""
Transcript loader for VideoMind AI.

Retrieves YouTube transcripts using youtube-transcript-api.
"""

import re
from typing import List, Dict, Optional

from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptLoader:
    """Loads transcripts from YouTube videos."""

    def __init__(self):
        self.api = YouTubeTranscriptApi()

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract a YouTube video ID from different URL formats.
        """

        if not url:
            return None

        patterns = [
            r"(?:v=)([A-Za-z0-9_-]{11})",
            r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
            r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",
            r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
            r"(?:youtube\.com/live/)([A-Za-z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)

            if match:
                return match.group(1)

        # Allow users to enter the video ID directly
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
            return url.strip()

        return None

    def get_transcript(
        self,
        video_url: str,
        languages: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Retrieve a transcript from YouTube.

        Returns:
            List of transcript segments.
        """

        video_id = self.extract_video_id(video_url)

        if not video_id:
            raise ValueError(
                "Invalid YouTube URL. Please provide a valid YouTube video link."
            )

        languages = languages or ["en", "en-US", "en-GB"]

        try:
            # Current youtube-transcript-api interface
            transcript_list = self.api.list(video_id)

            transcript = None

            # First try manually created transcripts
            try:
                transcript = transcript_list.find_manually_created_transcript(
                    languages
                )
            except Exception:
                pass

            # Then try generated transcripts
            if transcript is None:
                try:
                    transcript = transcript_list.find_generated_transcript(
                        languages
                    )
                except Exception:
                    pass

            if transcript is None:
                available = list(transcript_list)

                if not available:
                    raise ValueError(
                        "This video does not have any available captions."
                    )

                # Use the first available transcript as a fallback
                transcript = available[0]

            fetched = transcript.fetch()

            # Convert fetched transcript segments into dictionaries
            results = []

            for item in fetched:
                if hasattr(item, "text"):
                    results.append({
                        "text": item.text,
                        "start": item.start,
                        "duration": item.duration
                    })
                else:
                    results.append({
                        "text": item.get("text", ""),
                        "start": item.get("start", 0),
                        "duration": item.get("duration", 0)
                    })

            if not results:
                raise ValueError(
                    "The transcript was empty or could not be read."
                )

            return results

        except Exception as e:
            error_message = str(e).lower()

            if "disabled" in error_message:
                raise ValueError(
                    "This video has captions disabled. "
                    "Please try another video with subtitles."
                )

            if "not found" in error_message or "no transcript" in error_message:
                raise ValueError(
                    "No transcript or captions are available for this video."
                )

            if (
                "blocked" in error_message
                or "requestblocked" in error_message
                or "ip" in error_message
                or "429" in error_message
            ):
                raise ValueError(
                    "YouTube temporarily blocked transcript requests from "
                    "the deployed server. Please wait and try again later, "
                    "or try another video."
                )

            raise ValueError(
                "A transcript could not be retrieved for this video. "
                "The video may not have captions, or YouTube may be "
                "temporarily blocking transcript requests."
            ) from e

    def get_transcript_text(self, video_url: str) -> str:
        """
        Return the complete transcript as plain text.
        """

        transcript = self.get_transcript(video_url)

        return "\n".join(
            item["text"] for item in transcript
            if item.get("text")
        )
