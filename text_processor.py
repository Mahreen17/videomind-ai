"""
Text cleaning and chunking for transcript processing.
"""

import re
from typing import List, Dict


class TextProcessor:
    """Clean and chunk transcript text."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean raw transcript text.

        Removes:
        - Extra whitespace and newlines
        - Redundant spacing
        - Common timestamp artifacts
        """

        if not text:
            return ""

        # Remove extra whitespace and newlines
        text = " ".join(text.split())

        # Remove timestamps such as [00:12:34]
        text = re.sub(
            r"\[\d{2}:\d{2}:\d{2}\]",
            "",
            text
        )

        return text.strip()

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 300,
        overlap: int = 50
    ) -> List[Dict]:
        """
        Split text into overlapping word-based chunks.

        Args:
            text: Full transcript text.
            chunk_size: Number of words per chunk.
            overlap: Number of overlapping words.

        Returns:
            List of dictionaries containing chunk information.
        """

        if not text or not text.strip():
            return []

        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0."
            )

        if overlap < 0:
            raise ValueError(
                "overlap cannot be negative."
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size."
            )

        words = text.split()
        chunks = []

        chunk_id = 0
        start_idx = 0

        while start_idx < len(words):

            end_idx = min(
                start_idx + chunk_size,
                len(words)
            )

            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)

            if chunk_text:
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "start_word_idx": start_idx,
                    "end_word_idx": end_idx
                })

            # Stop after reaching the final chunk
            if end_idx >= len(words):
                break

            # Move forward while maintaining overlap
            start_idx = end_idx - overlap
            chunk_id += 1

        return chunks

    @staticmethod
    def process_transcript(
        transcript: str,
        chunk_size: int = 300,
        overlap: int = 50
    ) -> List[Dict]:
        """
        Clean and chunk a transcript.

        Returns:
            List of processed chunks ready for embedding.
        """

        # Step 1: Clean transcript
        cleaned_text = TextProcessor.clean_text(transcript)

        # Step 2: Split transcript into chunks
        chunks = TextProcessor.chunk_text(
            cleaned_text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        return chunks


if __name__ == "__main__":

    sample_text = """
    This is a sample transcript from a video about machine learning.

    Machine learning is a subset of artificial intelligence. It involves
    training algorithms on data. The model learns patterns and uses them
    to make predictions.

    There are three major types of machine learning: supervised learning,
    unsupervised learning, and reinforcement learning.
    """

    chunks = TextProcessor.process_transcript(
        sample_text,
        chunk_size=30,
        overlap=5
    )

    print(f"Total chunks generated: {len(chunks)}\n")

    for chunk in chunks:
        print(f"Chunk {chunk['chunk_id']}:")
        print(chunk["text"])
        print("-" * 50)