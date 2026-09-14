"""
LLM Client for VideoMind AI.

Uses Groq's OpenAI-compatible API to generate:
- Answers to questions
- Video summaries
- Study notes
"""

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables from .env
load_dotenv()


class LLMClient:
    """Handles communication between VideoMind AI and Groq."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")

        self.base_url = os.getenv(
            "LLM_BASE_URL",
            "https://api.groq.com/openai/v1"
        )

        self.model = os.getenv(
            "LLM_MODEL",
            "openai/gpt-oss-20b"
        )

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. "
                "Please add your Groq API key to the .env file."
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    @staticmethod
    def limit_text(text: str, max_chars: int = 16000) -> str:
        """
        Limit the amount of text sent to Groq.

        This helps prevent token-limit errors when processing
        long YouTube transcripts.
        """

        if not text:
            return ""

        text = str(text)

        if len(text) <= max_chars:
            return text

        return (
            text[:max_chars]
            + "\n\n"
            "[Transcript shortened automatically because of API limits.]"
        )

    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.2
    ) -> str:
        """
        Send a prompt to Groq and return the generated response.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are VideoMind AI, a helpful educational assistant. "
                        "Provide accurate, clear, concise, and well-structured "
                        "answers based on the available video content."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content or ""

    def answer_question(
        self,
        question: str,
        context: str,
        transcript: Optional[str] = None
    ) -> str:
        """
        Answer a user question using retrieved transcript context.
        """

        context = self.limit_text(context, 12000)
        transcript_text = self.limit_text(transcript or "", 4000)

        prompt = f"""
Answer the user's question using the provided video context.

Question:
{question}

Retrieved Context:
{context}

Additional Transcript Context:
{transcript_text}

Instructions:
- Answer directly and clearly.
- Use information supported by the provided context.
- Do not invent facts.
- If the answer is not available, say that it is not clearly covered.
- Use headings or bullet points when useful.
"""

        return self.generate_response(
            prompt,
            max_tokens=900
        )

    def summarize(
        self,
        context: str = "",
        transcript: Optional[str] = None
    ) -> str:
        """
        Generate a concise summary of the video transcript.
        """

        text = transcript or context
        text = self.limit_text(text, 16000)

        prompt = f"""
Create a clear and well-structured summary of the following video transcript.

Use Markdown formatting with headings and bullet points.

Follow this structure:

# Summary

## Overview

## Main Topics

## Key Takeaways

Keep the explanation concise, accurate, and easy to study.

Transcript:
{text}
"""

        return self.generate_response(
            prompt,
            max_tokens=1100
        )

    def generate_summary(
        self,
        context: str = "",
        transcript: Optional[str] = None
    ) -> str:
        """
        Compatibility method used by rag_pipeline.py.
        """

        return self.summarize(
            context=context,
            transcript=transcript
        )

    def generate_study_notes(
        self,
        context: str = "",
        transcript: Optional[str] = None
    ) -> str:
        """
        Generate structured Markdown study notes.
        """

        text = transcript or context
        text = self.limit_text(text, 16000)

        prompt = f"""
Create well-organized study notes from the following video transcript.

Return Markdown that can be displayed directly in Streamlit.

Use:
- Clear headings
- Bold important terms
- Bullet points
- Numbered lists where appropriate
- Short paragraphs
- Simple explanations

Follow this structure:

# Study Notes

## Overview

## Main Topics

## Key Concepts

## Important Points

## Possible Interview or Exam Questions

## Final Takeaways

Do not include unnecessary introductions.

Make the notes useful for revision and easy to read.

Transcript:
{text}
"""

        return self.generate_response(
            prompt,
            max_tokens=1400
        )