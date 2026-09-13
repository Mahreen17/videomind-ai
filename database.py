"""
SQLite database management for VideoMind AI.

Stores:
- Processed video metadata
- Questions and answers
- User session information
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


class Database:
    """Manage metadata and processing history using SQLite."""

    def __init__(self, db_path: str = "data/videomind.db"):
        """
        Initialize the SQLite database.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path

        db_directory = os.path.dirname(db_path)

        if db_directory:
            os.makedirs(db_directory, exist_ok=True)

        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Enable foreign key constraints.
        conn.execute("PRAGMA foreign_keys = ON")

        return conn

    def init_schema(self) -> None:
        """Create database tables if they do not already exist."""

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Stores processed video information.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    url TEXT NOT NULL,
                    duration_seconds INTEGER DEFAULT 0,
                    transcript_text TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    chunk_count INTEGER DEFAULT 0
                )
                """
            )

            # Stores questions asked about videos.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id)
                        REFERENCES videos(video_id)
                        ON DELETE CASCADE
                )
                """
            )

            # Stores application sessions.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP
                )
                """
            )

            conn.commit()

        print(f"Database initialized at: {self.db_path}")

    def add_video(
        self,
        video_id: str,
        title: str,
        url: str,
        duration_seconds: int,
        transcript_text: str,
        chunk_count: int,
    ) -> None:
        """
        Store or update processed video information.

        Args:
            video_id: YouTube video ID.
            title: Video title.
            url: Full YouTube URL.
            duration_seconds: Video duration in seconds.
            transcript_text: Complete transcript text.
            chunk_count: Number of text chunks created.
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO videos (
                    video_id,
                    title,
                    url,
                    duration_seconds,
                    transcript_text,
                    chunk_count,
                    processed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(video_id) DO UPDATE SET
                    title = excluded.title,
                    url = excluded.url,
                    duration_seconds = excluded.duration_seconds,
                    transcript_text = excluded.transcript_text,
                    chunk_count = excluded.chunk_count,
                    processed_at = CURRENT_TIMESTAMP
                """,
                (
                    video_id,
                    title,
                    url,
                    duration_seconds,
                    transcript_text,
                    chunk_count,
                ),
            )

            conn.commit()

        print(f"Video {video_id} added to database.")

    def get_video(self, video_id: str) -> Optional[Dict]:
        """
        Retrieve video metadata.

        Args:
            video_id: YouTube video ID.

        Returns:
            Video information as a dictionary, or None if not found.
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT *
                FROM videos
                WHERE video_id = ?
                """,
                (video_id,),
            )

            row = cursor.fetchone()

        return dict(row) if row else None

    def add_question(
        self,
        video_id: str,
        question: str,
        answer: str,
    ) -> None:
        """
        Store a question and its answer.

        Args:
            video_id: YouTube video ID.
            question: User's question.
            answer: Generated answer.
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO questions (
                    video_id,
                    question,
                    answer
                )
                VALUES (?, ?, ?)
                """,
                (video_id, question, answer),
            )

            conn.commit()

    def count_questions_today(
        self,
        video_id: Optional[str] = None,
    ) -> int:
        """
        Count questions asked during the last 24 hours.

        Args:
            video_id: If provided, count only questions for this video.
                      Otherwise, count questions across all videos.

        Returns:
            Number of questions asked during the last 24 hours.
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if video_id:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM questions
                    WHERE video_id = ?
                    AND asked_at > datetime('now', '-1 day')
                    """,
                    (video_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM questions
                    WHERE asked_at > datetime('now', '-1 day')
                    """
                )

            count = cursor.fetchone()[0]

        return count

    def list_videos(self) -> List[Dict]:
        """
        List all processed videos.

        Returns:
            List of video metadata dictionaries.
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT *
                FROM videos
                ORDER BY processed_at DESC
                """
            )

            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def start_session(self, session_id: str) -> None:
        """
        Start a new user session.

        Args:
            session_id: Unique session identifier.
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id)
                VALUES (?)
                """,
                (session_id,),
            )

            conn.commit()

    def end_session(self, session_id: str) -> None:
        """
        Mark a session as ended.

        Args:
            session_id: Unique session identifier.
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE sessions
                SET ended_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (session_id,),
            )

            conn.commit()

    def get_questions_for_video(
        self,
        video_id: str,
    ) -> List[Dict]:
        """
        Retrieve all questions asked for a specific video.

        Args:
            video_id: YouTube video ID.

        Returns:
            List of question and answer dictionaries.
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT *
                FROM questions
                WHERE video_id = ?
                ORDER BY asked_at DESC
                """,
                (video_id,),
            )

            rows = cursor.fetchall()

        return [dict(row) for row in rows]


# Testing
if __name__ == "__main__":
    print("=" * 50)
    print("Testing VideoMind AI Database")
    print("=" * 50)

    db = Database(db_path="data/videomind.db")

    # Test 1: Add a video.
    db.add_video(
        video_id="test123",
        title="How to Learn Python",
        url="https://youtube.com/watch?v=test123",
        duration_seconds=3600,
        transcript_text="This is a sample transcript.",
        chunk_count=12,
    )

    # Test 2: Retrieve the video.
    video = db.get_video("test123")

    if video:
        print(f"\nRetrieved video: {video['title']}")
        print(f"Video ID: {video['video_id']}")
        print(f"Chunk count: {video['chunk_count']}")

    # Test 3: Add a question.
    db.add_question(
        video_id="test123",
        question="What is Python?",
        answer="Python is a programming language.",
    )

    # Test 4: Count questions.
    count = db.count_questions_today()
    print(f"\nQuestions asked in the last 24 hours: {count}")

    # Test 5: Retrieve questions for a video.
    questions = db.get_questions_for_video("test123")
    print(f"Questions for test123: {len(questions)}")

    # Test 6: List videos.
    videos = db.list_videos()
    print(f"Total videos stored: {len(videos)}")

    # Test 7: Session management.
    session_id = "test-session-001"

    db.start_session(session_id)
    print(f"\nSession started: {session_id}")

    db.end_session(session_id)
    print(f"Session ended: {session_id}")

    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)