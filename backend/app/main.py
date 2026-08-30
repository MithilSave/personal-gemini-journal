import os
import uuid
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env for local development

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.auth import get_current_user_id
from app.models import JournalChatRequest, JournalEntryResponse
from app.gemini_service import GeminiJournalEngine
from app.firestore_service import FirestoreJournalStore

app = FastAPI(title="MindScribe - Personal Gemini Journal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gemini = GeminiJournalEngine()
store = FirestoreJournalStore()

@app.post("/api/chat", response_model=JournalEntryResponse)
async def chat_and_journal(req: JournalChatRequest, uid: str = Depends(get_current_user_id)):
    journal_id = req.journal_id or str(uuid.uuid4())
    model_reply = gemini.generate_chat_response(req.message, req.history)
    store.save_message_turn(uid, journal_id, req.message, model_reply)
    return JournalEntryResponse(journal_id=journal_id, reply=model_reply)

@app.post("/api/summarize/{journal_id}")
async def summarize_journal(journal_id: str, uid: str = Depends(get_current_user_id)):
    journal_ref = store._get_journal_ref(uid, journal_id)
    messages = journal_ref.collection("messages").order_by("timestamp").stream()
    
    transcript = "\n".join([f"{m.get('role').upper()}: {m.get('content')}" for m in messages])
    summary = gemini.generate_cognitive_summary(transcript)
    store.save_summary(uid, journal_id, summary)
    return {"journal_id": journal_id, "summary": summary}

@app.get("/api/journals")
async def list_journals(uid: str = Depends(get_current_user_id)):
    return {"journals": store.list_user_journals(uid)}

@app.get("/api/journals/{journal_id}/messages")
async def get_journal_messages(journal_id: str, uid: str = Depends(get_current_user_id)):
    messages = store.get_journal_messages(uid, journal_id)
    return {"journal_id": journal_id, "messages": messages}

@app.get("/api/mood-timeline")
async def get_mood_timeline(uid: str = Depends(get_current_user_id)):
    timeline = store.get_mood_timeline(uid)
    return {"timeline": timeline}

# Mount static frontend for single container deployment
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

