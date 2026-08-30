import json
from google import genai
from google.genai import types
from app.models import ChatMessage, CognitiveSummary

class GeminiJournalEngine:
    def __init__(self):
        # The Google GenAI SDK automatically resolves GEMINI_API_KEY from environment
        self.client = genai.Client()

    def generate_chat_response(self, message: str, history: list[ChatMessage]) -> str:
        system_instruction = (
            "You are MindScribe, a reflective, empathetic, and security-aware personal AI journal coach. "
            "Help the user explore thoughts, brainstorm solutions, and reflect objectively. "
            "Keep responses supportive, grounded, and concise."
        )

        contents = []
        for msg in history:
            role = "user" if msg.role == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
        
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=1024,
        )

        response = self.client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=contents,
            config=config
        )
        return response.text

    def generate_cognitive_summary(self, full_transcript: str) -> CognitiveSummary:
        """
        Original Feature Enhancement: Cognitive distortion detection and behavioral synthesis.
        Enforces structured JSON schema validation at the Gemini API level.
        """
        prompt = (
            "Analyze the following personal journal transcript. Extract core themes, sentiment valence (-1.0 to 1.0), "
            "dominant emotion, detected cognitive distortions (e.g., Catastrophizing, All-or-Nothing thinking, Mind Reading, or None), "
            "concrete action items, and an actionable growth insight.\n\n"
            f"Transcript:\n{full_transcript}"
        )

        config = types.GenerateContentConfig(
            system_instruction="You are an expert psychological data synthesizer and reflection analyst.",
            response_mime_type="application/json",
            response_schema=CognitiveSummary,
            temperature=0.2,
        )

        response = self.client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=config
        )
        return CognitiveSummary(**json.loads(response.text))

    def generate_daily_prompt(self, past_summaries: list[dict]) -> str:
        """
        Original Feature: AI-Generated Personalized Daily Prompt.
        Uses the user's past journal summaries to create a contextual,
        deeply personalized reflection question.
        """
        context = ""
        if past_summaries:
            recent = past_summaries[:5]  # Use last 5 sessions for context
            context = "Here is a summary of the user's recent journal sessions:\n"
            for s in recent:
                context += f"- Title: {s.get('title', 'Untitled')}, Emotion: {s.get('primary_emotion', 'Unknown')}, Sentiment: {s.get('sentiment_score', 0)}\n"
                if s.get('key_themes'):
                    context += f"  Themes: {', '.join(s['key_themes'])}\n"
            context += "\n"

        prompt = (
            f"{context}"
            "Based on the user's recent emotional patterns and themes (or if no history exists, provide a universal prompt), "
            "generate ONE deeply thoughtful, personalized journaling prompt that:\n"
            "1. Acknowledges their recent emotional trajectory\n"
            "2. Gently encourages growth or deeper exploration\n"
            "3. Is open-ended and inviting, not clinical\n"
            "4. Is 1-2 sentences max\n\n"
            "Return ONLY the prompt text, nothing else."
        )

        config = types.GenerateContentConfig(
            system_instruction="You are a warm, insightful journaling coach. Generate prompts that feel personal and meaningful.",
            temperature=0.9,
            max_output_tokens=150,
        )

        response = self.client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=config
        )
        return response.text.strip()
