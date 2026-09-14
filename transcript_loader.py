import re
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptLoader:

    @staticmethod
    def extract_video_id(video_url):
        """
        Extract YouTube video ID from different YouTube URL formats.
        """

        if not video_url or not isinstance(video_url, str):
            raise ValueError("Please provide a valid YouTube URL.")

        video_url = video_url.strip()

        # Direct video ID
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_url):
            return video_url

        parsed_url = urlparse(video_url)
        hostname = parsed_url.netloc.lower().replace("www.", "")
        path = parsed_url.path.strip("/")

        # Standard YouTube URL
        if hostname in ["youtube.com", "m.youtube.com"]:
            if parsed_url.path == "/watch":
                video_id = parse_qs(
                    parsed_url.query
                ).get("v", [None])[0]

                if video_id:
                    return video_id[:11]

            # Shorts URL
            if path.startswith("shorts/"):
                video_id = path.split("/")[1]
                return video_id[:11]

            # Embed URL
            if path.startswith("embed/"):
                video_id = path.split("/")[1]
                return video_id[:11]

        # youtu.be URL
        if hostname == "youtu.be":
            video_id = path.split("/")[0]
            return video_id[:11]

        raise ValueError(
            "Invalid YouTube URL."
        )

    @staticmethod
    def get_transcript(video_url):
        """
        Fetch transcript using the latest youtube-transcript-api.
        """

        try:
            video_id = TranscriptLoader.extract_video_id(video_url)

            print(f"Extracted video ID: {video_id}")

            api = YouTubeTranscriptApi()

            transcript = api.fetch(
                video_id,
                languages=["en", "hi"]
            )

            transcript_text = " ".join(
                snippet.text for snippet in transcript
            )

            if not transcript_text.strip():
                raise ValueError("The transcript is empty.")

            return {
                "video_id": video_id,
                "text": transcript_text,
                "language": getattr(transcript, "language", "unknown"),
                "language_code": getattr(
                    transcript,
                    "language_code",
                    "unknown"
                )
            }

        except Exception as e:
            error_message = str(e)

            if "Subtitles are disabled" in error_message:
                raise Exception(
                    "This video does not have an accessible transcript. "
                    "Please try another video with captions enabled."
                )

            if "Could not retrieve a transcript" in error_message:
                raise Exception(
                    "A transcript could not be retrieved for this video. "
                    "The video may not have captions, or YouTube may be "
                    "temporarily blocking transcript requests."
                )

            raise Exception(
                f"Error fetching transcript: {error_message}"
            )


if __name__ == "__main__":

    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

    try:
        video_id = TranscriptLoader.extract_video_id(test_url)

        print("Extracted video ID:", video_id)

        result = TranscriptLoader.get_transcript(test_url)

        print("\nTranscript fetched successfully.")
        print("Video ID:", result["video_id"])
        print("Language:", result["language"])
        print("Transcript length:", len(result["text"]))

        print("\nFirst 300 characters:")
        print(result["text"][:300])

    except Exception as e:
        print("Error:", e)