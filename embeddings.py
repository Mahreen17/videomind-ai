from sentence_transformers import SentenceTransformer


class EmbeddingsGenerator:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

        print(f"Embeddings model loaded: {model_name}")

    def generate_embeddings(self, texts):
        """
        Generate embeddings for a list of text chunks.

        Args:
            texts: A list of strings.

        Returns:
            List of embedding vectors.
        """

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        return embeddings.tolist()

    def generate_embedding(self, text):
        """
        Generate an embedding for a single text.
        """

        if not text:
            return []

        embedding = self.model.encode(
            text,
            convert_to_numpy=True
        )

        return embedding.tolist()

    def get_embedding_dimension(self):
        """
        Return the size of each embedding vector.
        """

        return self.model.get_sentence_embedding_dimension()


if __name__ == "__main__":

    generator = EmbeddingsGenerator()

    test_texts = [
        "This is a test sentence.",
        "Artificial intelligence is useful."
    ]

    embeddings = generator.generate_embeddings(test_texts)

    print("\nEmbedding generation successful.")
    print("Number of embeddings:", len(embeddings))
    print("Embedding dimension:", len(embeddings[0]))