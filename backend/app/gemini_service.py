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
