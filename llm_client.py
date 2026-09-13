"""
LLM client for communicating with FreeLLMAPI gateway.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class LLMClient:
    """Interface to FreeLLMAPI for LLM queries."""

    def __init__(self):
        self.base_url = os.getenv(
            "FREELLMAPI_BASE_URL",
            "http://localhost:3001/v1"
        )

        self.api_key = os.getenv(
            "FREELLMAPI_API_KEY",
            "freellmapi-your-unified-key"
        )

        self.model = os.getenv(
            "FREELLMAPI_MODEL",
            "auto"
        )

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

        print("LLM Client initialized:")
        print(f"  Base URL: {self.base_url}")
        print(f"  Model: {self.model}")

    def _generate_response(
        self,
        messages: list,
        max_tokens: int,
        temperature: float = 0.3
    ) -> Optional[str]:
        """Send a request to FreeLLMAPI."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if not response.choices:
                print("Error: No response choices returned.")
                return None

            answer = response.choices[0].message.content

            if not answer:
                print("Error: Empty response received.")
                return None

            return answer.strip()

        except Exception as e:
            print(f"Error calling FreeLLMAPI: {e}")
            return None

    def answer_question(
        self,
        context: str,
        question: str,
        max_tokens: int = 300
    ) -> Optional[str]:
        """Answer a question using transcript context."""

        if not context.strip():
            print("Error: Transcript context is empty.")
            return None

        if not question.strip():
            print("Error: Question is empty.")
            return None

        prompt = f"""
You are a helpful assistant that answers questions about video content.

Use only the information available in the transcript context below.

If the answer is not available in the context, respond exactly with:

"I don't have information about that in the video transcript."

Do not use outside knowledge.

Transcript Context:
{context}

Question:
{question}

Answer:
"""

        messages = [
            {
                "role": "system",
                "content": (
                    "Answer questions only using the provided transcript "
                    "context. Do not invent information."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        return self._generate_response(
            messages,
            max_tokens,
            temperature=0.3
        )

    def generate_summary(
        self,
        context: str,
        max_tokens: int = 500
    ) -> Optional[str]:
        """Generate a concise summary of transcript content."""

        if not context.strip():
            print("Error: Transcript context is empty.")
            return None

        messages = [
            {
                "role": "system",
                "content": (
                    "Summarize the transcript accurately and concisely. "
                    "Use only the information provided."
                )
            },
            {
                "role": "user",
                "content": f"Summarize this transcript:\n\n{context}"
            }
        ]

        return self._generate_response(
            messages,
            max_tokens,
            temperature=0.3
        )

    def generate_study_notes(
        self,
        context: str,
        max_tokens: int = 800
    ) -> Optional[str]:
        """Generate structured study notes from transcript content."""

        if not context.strip():
            print("Error: Transcript context is empty.")
            return None

        prompt = f"""
Create structured study notes from the following video transcript.

Use this format:

Key Points:
- Important points from the transcript

Important Concepts:
- Concept: Definition

Examples:
- Examples mentioned in the transcript

Summary:
A short overall summary.

Only use information from the transcript.

Transcript:
{context}
"""

        messages = [
            {
                "role": "system",
                "content": (
                    "Create accurate and well-organized study notes "
                    "using only the provided transcript."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        return self._generate_response(
            messages,
            max_tokens,
            temperature=0.3
        )


if __name__ == "__main__":

    print("=" * 50)
    print("Testing LLM Client")
    print("=" * 50)

    client = LLMClient()

    test_context = """
Machine learning is a subset of artificial intelligence that enables
systems to learn from data. Instead of being explicitly programmed,
machine learning systems use algorithms to identify patterns in data.

There are three main types of machine learning:
supervised learning, unsupervised learning, and reinforcement learning.
"""

    print("\n--- Testing Question Answering ---")

    question = "What is machine learning?"

    answer = client.answer_question(
        context=test_context,
        question=question
    )

    print(f"Q: {question}")
    print(f"A: {answer}")

    print("\n--- Testing Summary Generation ---")

    summary = client.generate_summary(test_context)

    print(f"Summary:\n{summary}")

    print("\n--- Testing Study Notes Generation ---")

    notes = client.generate_study_notes(test_context)

    print(f"Notes:\n{notes}")

    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)