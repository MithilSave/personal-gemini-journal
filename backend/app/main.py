import os
import io
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env for local development

from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
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

@app.get("/api/daily-prompt")
async def get_daily_prompt(uid: str = Depends(get_current_user_id)):
    """Generate a personalized journaling prompt based on the user's past sessions."""
    journals = store.list_user_journals(uid)
    past_summaries = [j.get("summary") for j in journals if j.get("summary")]
    prompt = gemini.generate_daily_prompt(past_summaries)
    return {"prompt": prompt}

@app.get("/api/export/{journal_id}")
async def export_journal_pdf(journal_id: str, uid: str = Depends(get_current_user_id)):
    """Export a journal session as a downloadable HTML report styled for print/PDF."""
    messages = store.get_journal_messages(uid, journal_id)
    
    # Get journal metadata for the title
    journals = store.list_user_journals(uid)
    journal_meta = next((j for j in journals if j.get("id") == journal_id), {})
    title = journal_meta.get("summary", {}).get("title", "Journal Session") if journal_meta.get("summary") else "Journal Session"
    summary = journal_meta.get("summary")
    export_date = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")

    # Build HTML report
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>MindScribe — {title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',sans-serif; background:#0f172a; color:#e2e8f0; padding:2rem; max-width:800px; margin:0 auto; }}
  .header {{ text-align:center; margin-bottom:2rem; padding-bottom:1.5rem; border-bottom:1px solid rgba(255,255,255,0.1); }}
  .header h1 {{ font-size:1.8rem; background:linear-gradient(to right,#818cf8,#c084fc); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0.5rem; }}
  .header .subtitle {{ color:#94a3b8; font-size:0.85rem; }}
  .header .date {{ color:#64748b; font-size:0.75rem; margin-top:0.5rem; }}
  .msg {{ margin-bottom:1.25rem; padding:1rem 1.25rem; border-radius:12px; line-height:1.7; }}
  .msg.user {{ background:linear-gradient(135deg,rgba(99,102,241,0.3),rgba(139,92,246,0.3)); border-left:4px solid #818cf8; }}
  .msg.model {{ background:rgba(30,41,59,0.6); border-left:4px solid #334155; }}
  .msg .role {{ font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; margin-bottom:0.4rem; font-weight:600; }}
  .summary-box {{ background:linear-gradient(135deg,rgba(16,185,129,0.15),rgba(5,150,105,0.05)); border:1px solid rgba(16,185,129,0.3); border-radius:16px; padding:1.5rem; margin-top:2rem; }}
  .summary-box h2 {{ color:#34d399; font-size:1.1rem; margin-bottom:1rem; }}
  .summary-box .item {{ margin-bottom:0.75rem; }}
  .summary-box .label {{ font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em; color:rgba(52,211,153,0.8); font-weight:600; }}
  .summary-box .value {{ font-size:0.9rem; margin-top:0.2rem; }}
  .footer {{ text-align:center; margin-top:2rem; padding-top:1rem; border-top:1px solid rgba(255,255,255,0.05); color:#475569; font-size:0.7rem; }}
  @media print {{ body {{ background:white; color:#1e293b; }} .msg.user {{ background:#ede9fe; border-left-color:#6366f1; }} .msg.model {{ background:#f1f5f9; border-left-color:#94a3b8; }} }}
</style></head><body>
<div class="header">
  <h1>✦ {title}</h1>
  <div class="subtitle">MindScribe — Personal Gemini Journal</div>
  <div class="date">Exported on {export_date}</div>
</div>
"""
    for msg in messages:
        role_label = "You" if msg.get("role") == "user" else "MindScribe AI"
        role_class = msg.get("role", "model")
        html += f'<div class="msg {role_class}"><div class="role">{role_label}</div>{msg.get("content", "")}</div>\n'

    if summary:
        html += '<div class="summary-box"><h2>📊 Cognitive Analysis</h2>'
        html += f'<div class="item"><div class="label">Primary Emotion</div><div class="value">{summary.get("primary_emotion", "N/A")}</div></div>'
        html += f'<div class="item"><div class="label">Sentiment Score</div><div class="value">{summary.get("sentiment_score", "N/A")}</div></div>'
        if summary.get("key_themes"):
            html += f'<div class="item"><div class="label">Key Themes</div><div class="value">{", ".join(summary["key_themes"])}</div></div>'
        if summary.get("cognitive_distortions_detected"):
            html += f'<div class="item"><div class="label">Cognitive Distortions</div><div class="value">{", ".join(summary["cognitive_distortions_detected"])}</div></div>'
        if summary.get("growth_insight"):
            html += f'<div class="item"><div class="label">💡 Growth Insight</div><div class="value">{summary["growth_insight"]}</div></div>'
        html += '</div>'

    html += '<div class="footer">Generated by MindScribe — Powered by Google Gemini</div></body></html>'

    return StreamingResponse(
        io.BytesIO(html.encode("utf-8")),
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="mindscribe-{journal_id[:8]}.html"'}
    )

# Mount static frontend for single container deployment
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

