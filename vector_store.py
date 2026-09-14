import os
from typing import Any, Dict, List, Optional

# Disable Chroma telemetry before importing chromadb
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        collection_name: str = "video_transcripts",
    ):
        """
        Initialize the ChromaDB vector store.

        Args:
            persist_directory: Folder where ChromaDB stores its data.
            collection_name: Name of the ChromaDB collection.
        """

        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Create the directory if it does not exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Load embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print(
            f"Vector store initialized. "
            f"Collection: {self.collection_name}"
        )

    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None,
        video_id: Optional[str] = None,
    ) -> None:
        """
        Add transcript chunks and embeddings to ChromaDB.

        Args:
            chunks: List of transcript chunk dictionaries.
            embeddings: Optional pre-generated embeddings.
            video_id: YouTube video ID used as metadata.
        """

        if not chunks:
            print("No chunks to add.")
            return

        # Generate embeddings if they were not provided
        if embeddings is None:
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedding_model.encode(
                texts,
                show_progress_bar=False,
            ).tolist()

        ids = []
        documents = []
        metadatas = []

        for index, chunk in enumerate(chunks):
            chunk_id = chunk.get(
                "chunk_id",
                f"{video_id or 'video'}_chunk_{index}",
            )

            ids.append(str(chunk_id))
            documents.append(chunk["text"])

            metadata = {
                "chunk_id": str(chunk_id),
                "video_id": video_id or "",
                "start_word_idx": chunk.get("start_word_idx", 0),
                "end_word_idx": chunk.get("end_word_idx", 0),
            }

            metadatas.append(metadata)

        # Upsert avoids duplicate-ID errors when the same video is processed again
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        print(f"Added {len(chunks)} chunks to vector store.")

    def query(
        self,
        query_embedding: Optional[List[float]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 5,
        video_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for similar transcript chunks.

        Supports both query_embedding and query_embeddings so it works
        with different versions of the RAG pipeline.

        Args:
            query_embedding: Single embedding vector.
            query_embeddings: Alternative parameter name for embeddings.
            n_results: Number of chunks to retrieve.
            video_id: Optional video ID filter.

        Returns:
            ChromaDB query results.
        """

        # Support both parameter names
        if query_embedding is None:
            query_embedding = query_embeddings

        if query_embedding is None:
            raise ValueError(
                "An embedding must be provided using "
                "'query_embedding' or 'query_embeddings'."
            )

        # If a nested list is provided, extract the first embedding
        if (
            isinstance(query_embedding, list)
            and len(query_embedding) > 0
            and isinstance(query_embedding[0], list)
        ):
            query_embedding = query_embedding[0]

        # Convert NumPy arrays to normal Python lists
        if hasattr(query_embedding, "tolist"):
            query_embedding = query_embedding.tolist()

        # Do not pass an invalid empty filter to ChromaDB
        where = None

        if video_id:
            where = {"video_id": video_id}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

        return results

    def delete_video(self, video_id: str) -> None:
        """
        Delete all transcript chunks belonging to a video.

        Args:
            video_id: YouTube video ID.
        """

        results = self.collection.get(
            where={"video_id": video_id}
        )

        ids = results.get("ids", [])

        if ids:
            self.collection.delete(ids=ids)
            print(
                f"Deleted {len(ids)} chunks for video: {video_id}"
            )
        else:
            print(
                f"No chunks found for video: {video_id}"
            )

    def get_collection_count(self) -> int:
        """
        Return the total number of stored transcript chunks.
        """

        return self.collection.count()


if __name__ == "__main__":
    print("\nTesting VectorStore...\n")

    vector_store = VectorStore()

    test_video_id = "test_video"

    # Remove old test data to avoid duplicate IDs
    vector_store.delete_video(test_video_id)

    test_chunks = [
        {
            "chunk_id": f"{test_video_id}_chunk_0",
            "text": (
                "Artificial intelligence is a field of computer science "
                "that focuses on creating intelligent machines."
            ),
            "start_word_idx": 0,
            "end_word_idx": 15,
        },
        {
            "chunk_id": f"{test_video_id}_chunk_1",
            "text": (
                "Machine learning allows computers to learn patterns "
                "from data without explicit programming."
            ),
            "start_word_idx": 16,
            "end_word_idx": 30,
        },
    ]

    # Add test chunks
    vector_store.add_chunks(
        chunks=test_chunks,
        video_id=test_video_id,
    )

    print(
        "Total chunks in collection:",
        vector_store.get_collection_count(),
    )

    # Generate embedding for a test query
    query_text = "What is machine learning?"

    query_embedding = vector_store.embedding_model.encode(
        query_text
    ).tolist()

    # Test similarity search
    results = vector_store.query(
        query_embedding=query_embedding,
        n_results=2,
        video_id=test_video_id,
    )

    print("\nRetrieved results:")

    for index, document in enumerate(results["documents"][0]):
        print(f"\nResult {index + 1}:")
        print(document)

    print("\nVectorStore test completed successfully.")