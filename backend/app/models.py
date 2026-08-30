from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'model'")
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: Optional[datetime] = None

class JournalChatRequest(BaseModel):
    journal_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=5000)
    history: List[ChatMessage] = []

class CognitiveSummary(BaseModel):
    title: str = Field(..., description="Short expressive title for the session")
    key_themes: List[str] = Field(..., description="Key topics discussed")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment valence between -1.0 and 1.0")
    primary_emotion: str = Field(..., description="Dominant emotion identified")
    cognitive_distortions_detected: List[str] = Field(..., description="List of CBT cognitive distortions, or ['None']")
    action_items: List[str] = Field(..., description="Actionable takeaways")
    growth_insight: str = Field(..., description="Constructive reframing and coaching advice")

class JournalEntryResponse(BaseModel):
    journal_id: str
    reply: str
    summary: Optional[CognitiveSummary] = None
