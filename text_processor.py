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
        - Common artifacts
        """

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove common artifacts (timestamps like "[00:12:34]")
        text = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', text)

        # Remove email addresses and URLs (optional)
        # text = re.sub(r'http\S+|www\.\S+|[\w\.-]+@[\w\.-]+', '', text)

        return text.strip()

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 300,
        overlap: int = 50
    ) -> List[Dict]:
        """
        Split text into overlapping chunks.

        Args:
            text: Full transcript text
            chunk_size: Target words per chunk (default 300)
            overlap: Words to repeat in next chunk (default 50)

        Returns:
            List of dictionaries containing chunk information.
        """

        words = text.split()
        chunks = []
        chunk_id = 0
        start_idx = 0

        # Prevent invalid overlap values
        if overlap >= chunk_size:
            raise ValueError("Overlap must be smaller than chunk_size.")

        while start_idx < len(words):

            # Determine end position
            end_idx = min(start_idx + chunk_size, len(words))

            # Extract words for current chunk
            chunk_words = words[start_idx:end_idx]
            current_chunk_text = ' '.join(chunk_words)

            # Store chunk information
            chunks.append({
                'chunk_id': chunk_id,
                'text': current_chunk_text,
                'start_word_idx': start_idx,
                'end_word_idx': end_idx
            })

            # Stop when the final chunk is reached
            if end_idx == len(words):
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
        Full pipeline: clean and chunk a transcript.

        Returns:
            List of processed chunks ready for embedding.
        """

        # Step 1: Clean the transcript
        cleaned = TextProcessor.clean_text(transcript)

        # Step 2: Split into chunks
        chunks = TextProcessor.chunk_text(
            cleaned,
            chunk_size=chunk_size,
            overlap=overlap
        )

        return chunks


# Testing
if __name__ == '__main__':

    sample_text = """
    This is a sample transcript from a video about machine learning.
    Machine learning is a subset of AI. It involves training algorithms
    on data. The model learns patterns. We can then use it for predictions.
    There are many types: supervised, unsupervised, reinforcement learning.
    Each has different use cases and challenges.
    """

    chunks = TextProcessor.process_transcript(
        sample_text,
        chunk_size=30,
        overlap=5
    )

    print(f"Total chunks generated: {len(chunks)}\n")

    for chunk in chunks:
        print(f"Chunk {chunk['chunk_id']}:")
        print(chunk['text'])
        print("-" * 50)