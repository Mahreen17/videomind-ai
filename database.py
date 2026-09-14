import os
import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_path="data/videomind.db"):
        self.db_path = db_path

        os.makedirs(
            os.path.dirname(self.db_path),
            exist_ok=True
        )

        self._create_tables()

        print(
            f"Database initialized at: {self.db_path}"
        )

    def get_connection(self):
        """
        Create and return a SQLite database connection.
        """

        connection = sqlite3.connect(self.db_path)

        connection.row_factory = sqlite3.Row

        return connection

    def _create_tables(self):
        """
        Create all required database tables.
        """

        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT UNIQUE NOT NULL,
                video_url TEXT NOT NULL,
                title TEXT,
                transcript TEXT,
                language TEXT,
                transcript_length INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                question TEXT NOT NULL,
                answer TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                session_name TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.commit()
        connection.close()

    def add_video(
        self,
        video_id,
        video_url=None,
        title=None,
        transcript=None,
        language=None,
        transcript_length=0,
        chunk_count=0
    ):
        """
        Add or update a processed video.

        Args:
            video_id: YouTube video ID.
            video_url: Original YouTube URL.
            title: Video title.
            transcript: Full transcript text.
            language: Transcript language.
            transcript_length: Number of transcript characters.
            chunk_count: Number of stored chunks.

        Returns:
            Dictionary containing the saved video.
        """

        connection = self.get_connection()
        cursor = connection.cursor()

        created_at = datetime.now().isoformat()

        # Automatically calculate transcript length.
        if transcript and transcript_length == 0:
            transcript_length = len(transcript)

        cursor.execute(
            """
            INSERT INTO videos (
                video_id,
                video_url,
                title,
                transcript,
                language,
                transcript_length,
                chunk_count,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                video_url = excluded.video_url,
                title = excluded.title,
                transcript = excluded.transcript,
                language = excluded.language,
                transcript_length = excluded.transcript_length,
                chunk_count = excluded.chunk_count
            """,
            (
                video_id,
                video_url or "",
                title or "",
                transcript or "",
                language or "",
                transcript_length,
                chunk_count,
                created_at
            )
        )

        connection.commit()

        video = cursor.execute(
            """
            SELECT *
            FROM videos
            WHERE video_id = ?
            """,
            (video_id,)
        ).fetchone()

        connection.close()

        return dict(video) if video else None

    def get_video(self, video_id):
        """
        Get one video by its YouTube video ID.
        """

        connection = self.get_connection()

        video = connection.execute(
            """
            SELECT *
            FROM videos
            WHERE video_id = ?
            """,
            (video_id,)
        ).fetchone()

        connection.close()

        return dict(video) if video else None

    def list_videos(self):
        """
        Return all processed videos.
        """

        connection = self.get_connection()

        videos = connection.execute(
            """
            SELECT *
            FROM videos
            ORDER BY created_at DESC
            """
        ).fetchall()

        connection.close()

        return [dict(video) for video in videos]

    def add_question(
        self,
        video_id,
        question,
        answer=""
    ):
        """
        Save a question and its answer.
        """

        connection = self.get_connection()

        connection.execute(
            """
            INSERT INTO questions (
                video_id,
                question,
                answer,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                video_id,
                question,
                answer,
                datetime.now().isoformat()
            )
        )

        connection.commit()
        connection.close()

    def get_questions(self, video_id=None):
        """
        Get saved questions.

        If video_id is provided, return questions
        for that video only.
        """

        connection = self.get_connection()

        if video_id:
            questions = connection.execute(
                """
                SELECT *
                FROM questions
                WHERE video_id = ?
                ORDER BY created_at DESC
                """,
                (video_id,)
            ).fetchall()
        else:
            questions = connection.execute(
                """
                SELECT *
                FROM questions
                ORDER BY created_at DESC
                """
            ).fetchall()

        connection.close()

        return [dict(question) for question in questions]

    def count_questions_today(self):
        """
        Count questions asked today.
        """

        today = datetime.now().strftime("%Y-%m-%d")

        connection = self.get_connection()

        result = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM questions
            WHERE DATE(created_at) = ?
            """,
            (today,)
        ).fetchone()

        connection.close()

        return result["count"]

    def create_session(
        self,
        video_id=None,
        session_name=None
    ):
        """
        Create a chat session.
        """

        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO sessions (
                video_id,
                session_name,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                video_id,
                session_name or "",
                datetime.now().isoformat()
            )
        )

        session_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return session_id

    def add_chat_message(
        self,
        session_id,
        role,
        message
    ):
        """
        Add a message to chat history.
        """

        connection = self.get_connection()

        connection.execute(
            """
            INSERT INTO chat_history (
                session_id,
                role,
                message,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                message,
                datetime.now().isoformat()
            )
        )

        connection.commit()
        connection.close()

    def get_chat_history(self, session_id):
        """
        Return all messages for a session.
        """

        connection = self.get_connection()

        messages = connection.execute(
            """
            SELECT *
            FROM chat_history
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,)
        ).fetchall()

        connection.close()

        return [dict(message) for message in messages]

    def delete_video(self, video_id):
        """
        Delete a video and its saved questions.
        """

        connection = self.get_connection()

        connection.execute(
            """
            DELETE FROM questions
            WHERE video_id = ?
            """,
            (video_id,)
        )

        connection.execute(
            """
            DELETE FROM videos
            WHERE video_id = ?
            """,
            (video_id,)
        )

        connection.commit()
        connection.close()


if __name__ == "__main__":
    print("=" * 60)
    print("VideoMind AI - Database Test")
    print("=" * 60)

    database = Database()

    test_video = database.add_video(
        video_id="test_video",
        video_url="https://www.youtube.com/watch?v=test_video",
        title="Test Video",
        transcript="This is a sample transcript for testing.",
        language="English",
        transcript_length=42,
        chunk_count=2
    )

    print("\nVideo added:")
    print(test_video)

    print("\nAll videos:")

    for video in database.list_videos():
        print(video)

    database.add_question(
        video_id="test_video",
        question="What is this video about?",
        answer="This is a test answer."
    )

    print("\nQuestions today:")
    print(database.count_questions_today())

    print("\nDatabase test completed successfully.")
    print("=" * 60)