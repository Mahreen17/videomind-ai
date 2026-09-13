"""
Vector store management using ChromaDB.
"""

import chromadb
import os
from typing import List, Dict


class VectorStore:
    """Manage embeddings storage and retrieval with ChromaDB."""

    def __init__(self, db_path: str = 'data/chromadb'):
        """
        Initialize ChromaDB.

        Args:
            db_path: Path to store ChromaDB files locally.

        Note:
            ChromaDB creates a persistent database on disk.
            Data persists between runs.
        """

        os.makedirs(db_path, exist_ok=True)

        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_path
        )

        self.db_path = db_path

        print(f"ChromaDB initialized at: {db_path}")

    def create_collection(self, collection_name: str):
        """
        Create or get a collection for a specific video or playlist.

        Args:
            collection_name: Unique collection name.

        Returns:
            ChromaDB collection object.
        """

        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        return collection

    def add_chunks(
        self,
        collection_name: str,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ) -> None:
        """
        Store chunks and their embeddings in ChromaDB.

        Args:
            collection_name: Name of the collection.
            chunks: List of chunk dictionaries.
            embeddings: List of embedding vectors.

        Example chunk:
            {
                'chunk_id': 0,
                'text': 'The video talks about...',
                'start_word_idx': 0
            }
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must be the same."
            )

        collection = self.create_collection(collection_name)

        # Prepare data for ChromaDB
        ids = [
            f"{collection_name}_chunk_{chunk['chunk_id']}"
            for chunk in chunks
        ]

        texts = [
            chunk['text']
            for chunk in chunks
        ]

        metadatas = [
            {
                'chunk_id': str(chunk['chunk_id']),
                'collection': collection_name,
                'start_word_idx': str(
                    chunk.get('start_word_idx', 0)
                )
            }
            for chunk in chunks
        ]

        # Upsert instead of add to avoid duplicate ID errors
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        print(
            f"Added {len(chunks)} chunks to collection "
            f"'{collection_name}'"
        )

    def query(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve the most similar chunks.

        Args:
            collection_name: Collection to search.
            query_embedding: Embedding vector for the question.
            top_k: Number of results to return.

        Returns:
            List of dictionaries containing chunk information.
        """

        try:
            collection = self.client.get_collection(
                name=collection_name
            )

        except Exception:
            print(
                f"Collection '{collection_name}' does not exist."
            )
            return []

        # Prevent requesting more results than available chunks
        total_chunks = collection.count()
        top_k = min(top_k, total_chunks)

        if top_k == 0:
            return []

        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Format results
        retrieved = []

        if results['documents'] and results['documents'][0]:

            for i, doc in enumerate(results['documents'][0]):

                retrieved.append({
                    'chunk_id': results['metadatas'][0][i]['chunk_id'],
                    'text': doc,
                    'distance': results['distances'][0][i]
                })

        return retrieved

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.

        Useful for cleanup or re-processing videos.
        """

        try:
            self.client.delete_collection(
                name=collection_name
            )

            print(
                f"Deleted collection '{collection_name}'"
            )

        except Exception as e:
            print(f"Error deleting collection: {e}")

    def list_collections(self) -> List[str]:
        """
        List all stored collections.
        """

        collections = self.client.list_collections()

        return [
            collection.name
            for collection in collections
        ]


# Testing
if __name__ == '__main__':

    from embeddings import EmbeddingsGenerator

    print("=" * 50)
    print("Testing Vector Store")
    print("=" * 50)

    # Initialize vector store and embeddings generator
    vs = VectorStore(db_path='data/chromadb')
    gen = EmbeddingsGenerator()

    # Test sample chunks
    sample_chunks = [
        {
            'chunk_id': 0,
            'text': 'Machine learning is a subset of AI that learns from data.'
        },
        {
            'chunk_id': 1,
            'text': 'Deep learning uses neural networks with multiple layers.'
        },
        {
            'chunk_id': 2,
            'text': 'Natural language processing helps computers understand human language.'
        },
    ]

    # Generate embeddings
    chunk_texts = [
        chunk['text']
        for chunk in sample_chunks
    ]

    print("\nGenerating embeddings...")

    embeddings = gen.embed_chunks(chunk_texts)

    # Store embeddings in ChromaDB
    collection_name = "test_video"

    vs.add_chunks(
        collection_name,
        sample_chunks,
        embeddings
    )

    # Test query
    question = "What is machine learning?"

    print(f"\nQuery: '{question}'")

    question_embedding = gen.embed_text(question)

    results = vs.query(
        collection_name,
        question_embedding,
        top_k=2
    )

    print("\nRetrieved chunks:")

    for result in results:

        print(
            f"  - Chunk {result['chunk_id']}: "
            f"{result['text'][:60]}... "
            f"(distance: {result['distance']:.3f})"
        )

    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)