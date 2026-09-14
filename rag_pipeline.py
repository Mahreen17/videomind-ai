"""
RAG pipeline for VideoMind AI.

Handles:
1. Transcript loading
2. Text cleaning and chunking
3. Embedding generation
4. Vector storage
5. Question answering
6. Summary generation
7. Study note generation
"""

import os
from typing import Dict

from dotenv import load_dotenv

from transcript_loader import TranscriptLoader
from text_processor import TextProcessor
from embeddings import EmbeddingsGenerator
from vector_store import VectorStore
from llm_client import LLMClient
from database import Database


load_dotenv()


class RAGPipeline:
    """Complete Retrieval-Augmented Generation pipeline."""

    def __init__(self):
        """Initialize all RAG components."""

        self.chunk_size = self._get_int_env(
            "CHUNK_SIZE",
            default=300,
            minimum=1
        )

        self.chunk_overlap = self._get_int_env(
            "CHUNK_OVERLAP",
            default=50,
            minimum=0
        )

        self.max_retrieved_chunks = self._get_int_env(
            "MAX_RETRIEVED_CHUNKS",
            default=5,
            minimum=1
        )

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "CHUNK_OVERLAP must be smaller than CHUNK_SIZE."
            )

        print("Initializing RAG Pipeline...")

        self.transcript_loader = TranscriptLoader()

        # Your TextProcessor uses static methods.
        self.text_processor = TextProcessor()

        self.embeddings_generator = EmbeddingsGenerator()

        self.vector_store = VectorStore()

        self.llm_client = LLMClient()

        self.database = Database()

        print("RAG Pipeline initialized successfully.")

    @staticmethod
    def _get_int_env(
        variable_name: str,
        default: int,
        minimum: int
    ) -> int:
        """Read and validate an integer environment variable."""

        value = os.getenv(variable_name)

        if value is None:
            return default

        try:
            value = int(value)
        except ValueError:
            raise ValueError(
                f"{variable_name} must be an integer."
            )

        if value < minimum:
            raise ValueError(
                f"{variable_name} must be at least {minimum}."
            )

        return value

    def process_video(self, video_url: str) -> Dict:
        """
        Process a YouTube video.

        Steps:
        1. Extract video ID.
        2. Fetch transcript.
        3. Clean and chunk transcript.
        4. Generate embeddings.
        5. Store vectors in ChromaDB.
        6. Save video metadata in SQLite.
        """

        if not video_url or not video_url.strip():
            raise ValueError("Please provide a valid YouTube URL.")

        video_url = video_url.strip()

        print("\nStep 1: Loading transcript...")

        transcript_result = self.transcript_loader.get_transcript(
            video_url
        )

        if not transcript_result:
            raise ValueError(
                "Could not fetch the transcript for this video."
            )

        if isinstance(transcript_result, dict):
            video_id = transcript_result.get("video_id")
            transcript_text = transcript_result.get("text", "")
        else:
            video_id = self.transcript_loader.extract_video_id(
                video_url
            )
            transcript_text = str(transcript_result)

        if not transcript_text.strip():
            raise ValueError("The transcript is empty.")

        if not video_id:
            video_id = self.transcript_loader.extract_video_id(
                video_url
            )

        if not video_id:
            raise ValueError("Could not extract the YouTube video ID.")

        print(f"Video ID: {video_id}")
        print(f"Transcript length: {len(transcript_text)} characters")

        print("\nStep 2: Cleaning and chunking transcript...")

        chunks = TextProcessor.process_transcript(
            transcript_text,
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap
        )

        if not chunks:
            raise ValueError(
                "No chunks were created from the transcript."
            )

        valid_chunks = []

        for chunk in chunks:
            if isinstance(chunk, dict):
                chunk_text = chunk.get("text", "").strip()

                if chunk_text:
                    valid_chunks.append(chunk)

        if not valid_chunks:
            raise ValueError("All generated chunks are empty.")

        chunk_texts = [
            chunk["text"]
            for chunk in valid_chunks
        ]

        print(f"Created {len(chunk_texts)} chunks.")

        print("\nStep 3: Generating embeddings...")

        embeddings = self.embeddings_generator.generate_embeddings(
            chunk_texts
        )

        if embeddings is None or len(embeddings) == 0:
            raise ValueError("Failed to generate embeddings.")

        print(f"Generated {len(embeddings)} embeddings.")

        print("\nStep 4: Storing vectors in ChromaDB...")

        self.vector_store.add_chunks(
            video_id=video_id,
            chunks=valid_chunks,
            embeddings=embeddings
        )

        print("\nStep 5: Saving video information in SQLite...")

        self.database.add_video(
            video_id=video_id,
            video_url=video_url,
            transcript=transcript_text,
            chunk_count=len(valid_chunks)
        )

        print("\nVideo processed successfully.")

        return {
            "success": True,
            "video_id": video_id,
            "video_url": video_url,
            "transcript_length": len(transcript_text),
            "chunk_count": len(valid_chunks)
        }

    def answer_question(
        self,
        video_id: str,
        question: str
    ) -> Dict:
        """
        Answer a question using relevant transcript chunks.
        """

        if not video_id or not video_id.strip():
            raise ValueError("Please provide a valid video ID.")

        if not question or not question.strip():
            raise ValueError("Please enter a question.")

        video_id = video_id.strip()
        question = question.strip()

        print("\nGenerating question embedding...")

        question_embedding = (
            self.embeddings_generator.generate_embeddings(
                [question]
            )
        )

        if question_embedding is None or len(question_embedding) == 0:
            raise ValueError(
                "Failed to generate the question embedding."
            )

        print("Retrieving relevant transcript chunks...")

        results = self.vector_store.query(
            query_embeddings=question_embedding,
            video_id=video_id,
            n_results=self.max_retrieved_chunks
        )

        if not results:
            raise ValueError(
                "No relevant information was found for this video."
            )

        retrieved_chunks = []

        if isinstance(results, dict):
            documents = results.get("documents", [])

            if documents and isinstance(documents[0], list):
                documents = documents[0]

            retrieved_chunks = documents

        elif isinstance(results, list):
            retrieved_chunks = results

        retrieved_chunks = [
            str(chunk).strip()
            for chunk in retrieved_chunks
            if str(chunk).strip()
        ]

        if not retrieved_chunks:
            raise ValueError(
                "No relevant transcript chunks were retrieved."
            )

        context = "\n\n".join(retrieved_chunks)

        print("Generating answer using Groq...")

        answer = self.llm_client.answer_question(
            question=question,
            context=context
        )

        if not answer:
            raise ValueError("The LLM returned an empty answer.")

        self.database.add_question(
            video_id=video_id,
            question=question,
            answer=answer
        )

        return {
            "success": True,
            "video_id": video_id,
            "question": question,
            "answer": answer,
            "retrieved_chunks": len(retrieved_chunks)
        }

    def generate_summary(self, video_id: str) -> Dict:
        """Generate a summary for a processed video."""

        if not video_id or not video_id.strip():
            raise ValueError("Please provide a valid video ID.")

        video_id = video_id.strip()

        video = self.database.get_video(video_id)

        if not video:
            raise ValueError(
                "Video not found. Please process the video first."
            )

        transcript = video.get("transcript", "")

        if not transcript:
            raise ValueError("Transcript not available.")

        print("Generating summary using groq...")

        summary = self.llm_client.generate_summary(
            transcript=transcript
        )

        if not summary:
            raise ValueError("The LLM returned an empty summary.")

        return {
            "success": True,
            "video_id": video_id,
            "summary": summary
        }

    def generate_study_notes(self, video_id: str) -> Dict:
        """Generate study notes for a processed video."""

        if not video_id or not video_id.strip():
            raise ValueError("Please provide a valid video ID.")

        video_id = video_id.strip()

        video = self.database.get_video(video_id)

        if not video:
            raise ValueError(
                "Video not found. Please process the video first."
            )

        transcript = video.get("transcript", "")

        if not transcript:
            raise ValueError("Transcript not available.")

        print("Generating study notes using Groq...")

        study_notes = self.llm_client.generate_study_notes(
            transcript=transcript
        )

        if not study_notes:
            raise ValueError(
                "The LLM returned empty study notes."
            )

        return {
            "success": True,
            "video_id": video_id,
            "study_notes": study_notes
        }


if __name__ == "__main__":
    print("=" * 60)
    print("VideoMind AI - RAG Pipeline Test")
    print("=" * 60)

    try:
        pipeline = RAGPipeline()

        print("\nRAG Pipeline is ready.")
        print("All components were initialized successfully.")

    except Exception as error:
        print("\nPipeline initialization failed.")
        print(f"Error: {error}")