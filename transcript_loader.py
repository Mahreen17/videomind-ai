"""
Handles extraction of transcripts from YouTube videos, Shorts, and playlists.
"""

import re
from typing import Optional, List, Dict

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound
)


class TranscriptLoader:
    """Extract and manage YouTube transcripts."""

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.

        Handles:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID
        """

        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([A-Za-z0-9_-]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)

            if match:
                return match.group(1)

        return None

    @staticmethod
    def get_transcript(
        video_id: str,
        language: str = 'en'
    ) -> Optional[str]:
        """
        Retrieve transcript for a single video.

        Args:
            video_id: YouTube video ID
            language: Language code (default: 'en' for English)

        Returns:
            Concatenated transcript text, or None if unavailable.
        """

        try:
            # Fetch transcript list for the video
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to get transcript in requested language
            try:
                transcript = transcripts.find_transcript([language])

            except NoTranscriptFound:
                # Fallback to English transcript
                transcript = transcripts.find_transcript(['en'])

            # Extract text from transcript entries
            transcript_text = ' '.join(
                [entry['text'] for entry in transcript.fetch()]
            )

            return transcript_text

        except TranscriptsDisabled:
            raise Exception(
                f"Transcripts are disabled for video {video_id}"
            )

        except NoTranscriptFound:
            raise Exception(
                f"No transcript found for video {video_id} "
                f"in language '{language}'"
            )

        except Exception as e:
            raise Exception(
                f"Error fetching transcript: {str(e)}"
            )

    @staticmethod
    def process_url(url: str) -> Dict[str, Optional[str]]:
        """
        Process a single YouTube URL and return transcript.

        Returns:
            Dictionary with keys:
            'status', 'video_id', 'transcript', 'error'
        """

        video_id = TranscriptLoader.extract_video_id(url)

        if not video_id:
            return {
                'status': 'error',
                'video_id': None,
                'transcript': None,
                'error': 'Invalid YouTube URL'
            }

        try:
            transcript = TranscriptLoader.get_transcript(video_id)

            return {
                'status': 'success',
                'video_id': video_id,
                'transcript': transcript,
                'error': None
            }

        except Exception as e:
            return {
                'status': 'error',
                'video_id': video_id,
                'transcript': None,
                'error': str(e)
            }


# Testing (for development only)
if __name__ == '__main__':

    # Example: Try to fetch a transcript
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    result = TranscriptLoader.process_url(test_url)

    print("Status:", result['status'])
    print("Video ID:", result['video_id'])

    if result['status'] == 'success':
        print("Transcript preview:")
        print(result['transcript'][:500])

    else:
        print("Error:", result['error'])