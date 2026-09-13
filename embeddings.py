"""
Generate embeddings for text chunks using Sentence Transformers.
"""

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np


class EmbeddingsGenerator:
    """Generate vector embeddings for text chunks."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embeddings model.

        Args:
            model_name: HuggingFace model identifier.

        Note:
            On first run, this downloads the model (~100MB).
            It is then cached locally for reuse.
        """

        print(f"Loading embeddings model: {model_name}...")

        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

        print("Model loaded successfully.")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text string.

        Args:
            text: Text to embed.

        Returns:
            List of floating-point numbers representing the embedding.
        """

        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        embedding = self.model.encode(
            text,
            convert_to_tensor=False
        )

        return embedding.tolist()

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text chunks efficiently.

        Args:
            chunks: List of text strings.

        Returns:
            List of embedding vectors in the same order as input.
        """

        if not chunks:
            return []

        embeddings = self.model.encode(
            chunks,
            convert_to_tensor=False,
            show_progress_bar=True
        )

        return embeddings.tolist()

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Returns:
            Similarity score between -1 and 1.
            Higher values indicate greater similarity.
        """

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(vec1, vec2) / (norm1 * norm2)

        return float(similarity)


# Testing
if __name__ == '__main__':

    print("=" * 50)
    print("Testing Embeddings Generator")
    print("=" * 50)

    # Initialize generator
    gen = EmbeddingsGenerator()

    # Test: Embed a single sentence
    sentence = "Machine learning is a subset of artificial intelligence."

    embedding = gen.embed_text(sentence)

    print(f"\nEmbedding for: '{sentence}'")
    print(f"Vector length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

    # Test: Embed multiple sentences
    sentences = [
        "Machine learning uses algorithms to learn from data.",
        "Dogs are animals that live on land.",
        "AI and machine learning are related concepts."
    ]

    print("\nGenerating embeddings for multiple sentences...")

    embeddings = gen.embed_chunks(sentences)

    # Compute similarity between first and last sentence
    sim = gen.compute_similarity(
        embeddings[0],
        embeddings[2]
    )

    print(f"\nSimilarity between sentences 1 and 3: {sim:.3f}")
    print("(Higher = more similar. ~1.0 means identical topic.)")

    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)