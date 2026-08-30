\# Master Implementation Specification: MindScribe (Personal Gemini Journal)

\#\# 1\. Project Overview & Objective  
MindScribe is a production-grade, privacy-first personal AI journaling and cognitive brainstorming web application built for Google Cloud Run. It leverages Google AI Studio (Gemini 2.5 Flash), Firebase Authentication, Cloud Firestore, and Google Cloud Secret Manager.

\#\#\# Core Architectural Goals:  
1\. \*\*Zero-Trust Multi-Tenant Isolation\*\*: Cryptographic validation of Firebase JWT ID tokens on the FastAPI backend; all database operations strictly confined to \`/users/{uid}/journals/{journal\_id}\`.  
2\. \*\*Enterprise Secret Management\*\*: API keys injected dynamically via Google Cloud Secret Manager into Cloud Run environment variables; zero hardcoded secrets.  
3\. \*\*Structured Psychological & Cognitive AI\*\*: Multi-turn dialogue with Gemini 2.5 Flash paired with JSON-schema-enforced cognitive distortion identification, emotional valence analysis, and actionable growth synthesis.  
4\. \*\*Serverless Scalability\*\*: Containerized deployment on Google Cloud Run with single-container static frontend serving.

\---

\#\# 2\. Google AI Studio Security Directives (System Constitution)

When configuring Google AI Studio Custom Instructions or the backend system prompt, use the following directives:

\`\`\`text  
\=== ENTERPRISE SECURITY CONSTITUTION & CODING DIRECTIVES \===

1\. THREAT MODELING & ZERO-TRUST AUTHENTICATION  
\- Never trust client-provided identities. The user identity (UID) must be resolved exclusively on the server by verifying the cryptographic Firebase ID Token (JWT).  
\- Reject any request lacking a valid 'Authorization: Bearer \<token\>' header.

2\. MULTI-TENANT DATABASE ISOLATION  
\- Every Firestore read, write, update, or list operation must be strictly prefixed with \`/users/{authenticated\_uid}/\`.  
\- No root-level global scans are permitted. Prevent cross-user data leakage at both the application and database levels.

3\. PROMPT INJECTION & SCHEMA INTEGRITY  
\- Separate system roles from user inputs.  
\- Enforce strict JSON schema validation (via Pydantic and response\_schema) for all structured outputs (summaries, emotion detection, action items).

4\. SECRET MANAGEMENT  
\- Never hardcode API keys, service account credentials, or environment configs.  
\- Runtime secrets must be accessed solely via Google Cloud Secret Manager injected into the environment.  
\`\`\`

\---

\#\# 3\. Project File Tree Structure

\`\`\`text  
personal-gemini-journal/  
├── backend/  
│   ├── app/  
│   │   ├── \_\_init\_\_.py  
│   │   ├── main.py              \# FastAPI application & route controllers  
│   │   ├── auth.py              \# Firebase JWT verification middleware  
│   │   ├── models.py            \# Pydantic data schemas & response models  
│   │   ├── gemini\_service.py    \# Google AI Studio Gemini API integration  
│   │   └── firestore\_service.py \# User-isolated Firestore persistence layer  
│   ├── requirements.txt  
│   └── Dockerfile  
├── frontend/  
│   ├── index.html               \# Main responsive single-page application  
│   ├── app.js                   \# Client state, Firebase Auth, and API interactions  
│   └── styles.css  
├── firestore.rules               \# Multi-tenant security rules  
├── .dockerignore  
├── .gitignore  
├── deploy.sh                    \# Automated GCP deployment script  
└── README.md  
\`\`\`

\---

\#\# 4\. Source Code Implementation

\#\#\# File: \`backend/requirements.txt\`  
\`\`\`txt  
fastapi==0.115.0  
uvicorn\[standard\]==0.30.6  
google-genai==0.1.1  
google-cloud-secret-manager==2.20.0  
google-cloud-firestore==2.19.0  
firebase-admin==6.5.0  
pydantic==2.9.2  
python-dotenv==1.0.1  
\`\`\`

\#\#\# File: \`backend/app/\_\_init\_\_.py\`  
\`\`\`python  
\# MindScribe Application Package  
\`\`\`

\#\#\# File: \`backend/app/models.py\`  
\`\`\`python  
from pydantic import BaseModel, Field  
from typing import List, Optional  
from datetime import datetime

class ChatMessage(BaseModel):  
    role: str \= Field(..., description="'user' or 'model'")  
    content: str \= Field(..., min\_length=1, max\_length=10000)  
    timestamp: Optional\[datetime\] \= None

class JournalChatRequest(BaseModel):  
    journal\_id: Optional\[str\] \= None  
    message: str \= Field(..., min\_length=1, max\_length=5000)  
    history: List\[ChatMessage\] \= \[\]

class CognitiveSummary(BaseModel):  
    title: str \= Field(..., description="Short expressive title for the session")  
    key\_themes: List\[str\] \= Field(..., description="Key topics discussed")  
    sentiment\_score: float \= Field(..., ge=-1.0, le=1.0, description="Sentiment valence between \-1.0 and 1.0")  
    primary\_emotion: str \= Field(..., description="Dominant emotion identified")  
    cognitive\_distortions\_detected: List\[str\] \= Field(..., description="List of CBT cognitive distortions, or \['None'\]")  
    action\_items: List\[str\] \= Field(..., description="Actionable takeaways")  
    growth\_insight: str \= Field(..., description="Constructive reframing and coaching advice")

class JournalEntryResponse(BaseModel):  
    journal\_id: str  
    reply: str  
    summary: Optional\[CognitiveSummary\] \= None  
\`\`\`

\#\#\# File: \`backend/app/auth.py\`  
\`\`\`python  
import firebase\_admin  
from firebase\_admin import auth  
from fastapi import HTTPException, Security, status  
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

if not firebase\_admin.\_apps:  
    firebase\_admin.initialize\_app()

security \= HTTPBearer()

async def get\_current\_user\_id(credentials: HTTPAuthorizationCredentials \= Security(security)) \-\> str:  
    """  
    Decodes and cryptographically validates the Firebase JWT ID Token.  
    Returns the authenticated user's unique UID.  
    """  
    token \= credentials.credentials  
    try:  
        decoded\_token \= auth.verify\_id\_token(token)  
        uid \= decoded\_token.get("uid")  
        if not uid:  
            raise HTTPException(  
                status\_code=status.HTTP\_401\_UNAUTHORIZED,  
                detail="Authentication failed: UID missing from token payload"  
            )  
        return uid  
    except Exception as e:  
        raise HTTPException(  
            status\_code=status.HTTP\_401\_UNAUTHORIZED,  
            detail=f"Invalid or expired authentication token: {str(e)}"  
        )  
\`\`\`

\#\#\# File: \`backend/app/gemini\_service.py\`  
\`\`\`python  
import json  
from google import genai  
from google.genai import types  
from app.models import ChatMessage, CognitiveSummary

class GeminiJournalEngine:  
    def \_\_init\_\_(self):  
        \# The Google GenAI SDK automatically resolves GEMINI\_API\_KEY from environment  
        self.client \= genai.Client()

    def generate\_chat\_response(self, message: str, history: list\[ChatMessage\]) \-\> str:  
        system\_instruction \= (  
            "You are MindScribe, a reflective, empathetic, and security-aware personal AI journal coach. "  
            "Help the user explore thoughts, brainstorm solutions, and reflect objectively. "  
            "Keep responses supportive, grounded, and concise."  
        )

        contents \= \[\]  
        for msg in history:  
            role \= "user" if msg.role \== "user" else "model"  
            contents.append(types.Content(role=role, parts=\[types.Part.from\_text(text=msg.content)\]))  
          
        contents.append(types.Content(role="user", parts=\[types.Part.from\_text(text=message)\]))

        config \= types.GenerateContentConfig(  
            system\_instruction=system\_instruction,  
            temperature=0.7,  
            max\_output\_tokens=1024,  
        )

        response \= self.client.models.generate\_content(  
            model="gemini-2.5-flash",  
            contents=contents,  
            config=config  
        )  
        return response.text

    def generate\_cognitive\_summary(self, full\_transcript: str) \-\> CognitiveSummary:  
        """  
        Original Feature Enhancement: Cognitive distortion detection and behavioral synthesis.  
        Enforces structured JSON schema validation at the Gemini API level.  
        """  
        prompt \= (  
            "Analyze the following personal journal transcript. Extract core themes, sentiment valence (-1.0 to 1.0), "  
            "dominant emotion, detected cognitive distortions (e.g., Catastrophizing, All-or-Nothing thinking, Mind Reading, or None), "  
            "concrete action items, and an actionable growth insight.\\n\\n"  
            f"Transcript:\\n{full\_transcript}"  
        )

        config \= types.GenerateContentConfig(  
            system\_instruction="You are an expert psychological data synthesizer and reflection analyst.",  
            response\_mime\_type="application/json",  
            response\_schema=CognitiveSummary,  
            temperature=0.2,  
        )

        response \= self.client.models.generate\_content(  
            model="gemini-2.5-flash",  
            contents=prompt,  
            config=config  
        )  
        return CognitiveSummary(\*\*json.loads(response.text))  
\`\`\`

\#\#\# File: \`backend/app/firestore\_service.py\`  
\`\`\`python  
from google.cloud import firestore  
from datetime import datetime, timezone  
from typing import List, Dict, Any  
from app.models import CognitiveSummary

class FirestoreJournalStore:  
    def \_\_init\_\_(self):  
        self.db \= firestore.Client()

    def \_get\_journal\_ref(self, user\_id: str, journal\_id: str):  
        \# Strict tenant boundary: users/{uid}/journals/{journal\_id}  
        return self.db.collection("users").document(user\_id).collection("journals").document(journal\_id)

    def save\_message\_turn(self, user\_id: str, journal\_id: str, user\_msg: str, model\_reply: str):  
        journal\_ref \= self.\_get\_journal\_ref(user\_id, journal\_id)  
        now \= datetime.now(timezone.utc)

        journal\_ref.set({"last\_updated": now, "user\_id": user\_id}, merge=True)  
        messages\_ref \= journal\_ref.collection("messages")  
        messages\_ref.add({"role": "user", "content": user\_msg, "timestamp": now})  
        messages\_ref.add({"role": "model", "content": model\_reply, "timestamp": now})

    def save\_summary(self, user\_id: str, journal\_id: str, summary: CognitiveSummary):  
        journal\_ref \= self.\_get\_journal\_ref(user\_id, journal\_id)  
        journal\_ref.set({  
            "summary": summary.model\_dump(),  
            "summary\_created\_at": datetime.now(timezone.utc)  
        }, merge=True)

    def list\_user\_journals(self, user\_id: str) \-\> List\[Dict\[str, Any\]\]:  
        docs \= self.db.collection("users").document(user\_id).collection("journals").order\_by(  
            "last\_updated", direction=firestore.Query.DESCENDING  
        ).limit(25).stream()

        results \= \[\]  
        for doc in docs:  
            data \= doc.to\_dict()  
            data\["id"\] \= doc.id  
            results.append(data)  
        return results  
\`\`\`

\#\#\# File: \`backend/app/main.py\`  
\`\`\`python  
import uuid  
from fastapi import FastAPI, Depends  
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.staticfiles import StaticFiles  
from app.auth import get\_current\_user\_id  
from app.models import JournalChatRequest, JournalEntryResponse  
from app.gemini\_service import GeminiJournalEngine  
from app.firestore\_service import FirestoreJournalStore

app \= FastAPI(title="MindScribe \- Personal Gemini Journal", version="1.0.0")

app.add\_middleware(  
    CORSMiddleware,  
    allow\_origins=\["\*"\],  
    allow\_credentials=True,  
    allow\_methods=\["\*"\],  
    allow\_headers=\["\*"\],  
)

gemini \= GeminiJournalEngine()  
store \= FirestoreJournalStore()

@app.post("/api/chat", response\_model=JournalEntryResponse)  
async def chat\_and\_journal(req: JournalChatRequest, uid: str \= Depends(get\_current\_user\_id)):  
    journal\_id \= req.journal\_id or str(uuid.uuid4())  
    model\_reply \= gemini.generate\_chat\_response(req.message, req.history)  
    store.save\_message\_turn(uid, journal\_id, req.message, model\_reply)  
    return JournalEntryResponse(journal\_id=journal\_id, reply=model\_reply)

@app.post("/api/summarize/{journal\_id}")  
async def summarize\_journal(journal\_id: str, uid: str \= Depends(get\_current\_user\_id)):  
    journal\_ref \= store.\_get\_journal\_ref(uid, journal\_id)  
    messages \= journal\_ref.collection("messages").order\_by("timestamp").stream()  
      
    transcript \= "\\n".join(\[f"{m.get('role').upper()}: {m.get('content')}" for m in messages\])  
    summary \= gemini.generate\_cognitive\_summary(transcript)  
    store.save\_summary(uid, journal\_id, summary)  
    return {"journal\_id": journal\_id, "summary": summary}

@app.get("/api/journals")  
async def list\_journals(uid: str \= Depends(get\_current\_user\_id)):  
    return {"journals": store.list\_user\_journals(uid)}

\# Mount static frontend for single container deployment  
app.mount("/", StaticFiles(directory="/app/frontend", html=True), name="static")  
\`\`\`

\#\#\# File: \`backend/Dockerfile\`  
\`\`\`dockerfile  
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \\  
    PORT=8080

WORKDIR /app

COPY backend/requirements.txt .  
RUN pip install \--no-cache-dir \-r requirements.txt

COPY backend /app/backend  
COPY frontend /app/frontend

WORKDIR /app/backend

EXPOSE 8080  
CMD \["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"\]  
\`\`\`

\#\#\# File: \`firestore.rules\`  
\`\`\`javascript  
rules\_version \= '2';  
service cloud.firestore {  
  match /databases/{database}/documents {  
    // Multi-tenant containment rule  
    match /users/{userId}/{document=\*\*} {  
      allow read, write: if request.auth \!= null && request.auth.uid \== userId;  
    }  
      
    // Explicit global deny  
    match /{document=\*\*} {  
      allow read, write: if false;  
    }  
  }  
}  
\`\`\`

\#\#\# File: \`frontend/index.html\`  
\`\`\`html  
\<\!DOCTYPE html\>  
\<html lang="en"\>  
\<head\>  
  \<meta charset="UTF-8"\>  
  \<meta name="viewport" content="width=device-width, initial-scale=1.0"\>  
  \<title\>MindScribe — Personal Gemini Journal\</title\>  
  \<script src="https://cdn.tailwindcss.com"\>\</script\>  
  \<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"\>\</script\>  
  \<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-auth-compat.js"\>\</script\>  
\</head\>  
\<body class="bg-slate-900 text-slate-100 min-h-screen flex items-center justify-center p-4"\>  
  \<div class="max-w-3xl w-full bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-4"\>  
    \<div class="flex items-center justify-between border-b border-slate-700 pb-4"\>  
      \<div\>  
        \<h1 class="text-2xl font-bold text-indigo-400"\>MindScribe\</h1\>  
        \<p class="text-xs text-slate-400"\>Secure Personal Gemini Journal & Cognitive Companion\</p\>  
      \</div\>  
      \<div id="auth-controls"\>  
        \<button id="login-btn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition"\>Sign In with Google\</button\>  
        \<span id="user-display" class="hidden text-xs text-slate-300"\>\</span\>  
      \</div\>  
    \</div\>

    \<\!-- Chat View \--\>  
    \<div id="chat-window" class="h-80 overflow-y-auto bg-slate-950 p-4 rounded-xl space-y-3 border border-slate-800 text-sm"\>  
      \<p class="text-slate-500 italic"\>Sign in to start an authenticated journaling session.\</p\>  
    \</div\>

    \<\!-- Input Section \--\>  
    \<div class="flex gap-2"\>  
      \<input id="chat-input" type="text" placeholder="Reflect on your thoughts, challenges, or goals..." class="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white outline-none focus:border-indigo-500 text-sm disabled:opacity-50" disabled /\>  
      \<button id="send-btn" class="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-lg font-medium text-sm text-white disabled:opacity-50 transition" disabled\>Send\</button\>  
      \<button id="summarize-btn" class="bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-lg font-medium text-sm text-white disabled:opacity-50 transition" disabled\>Summarize\</button\>  
    \</div\>  
  \</div\>

  \<script\>  
    // Replace with your Firebase Project Web Configuration  
    const firebaseConfig \= {  
      apiKey: "YOUR\_FIREBASE\_API\_KEY",  
      authDomain: "YOUR\_PROJECT\_ID.firebaseapp.com",  
      projectId: "YOUR\_PROJECT\_ID",  
      appId: "YOUR\_APP\_ID"  
    };  
    firebase.initializeApp(firebaseConfig);

    let idToken \= null;  
    let currentJournalId \= null;  
    let history \= \[\];

    const loginBtn \= document.getElementById('login-btn');  
    const userDisplay \= document.getElementById('user-display');  
    const chatInput \= document.getElementById('chat-input');  
    const sendBtn \= document.getElementById('send-btn');  
    const summarizeBtn \= document.getElementById('summarize-btn');  
    const chatWindow \= document.getElementById('chat-window');

    loginBtn.onclick \= async () \=\> {  
      const provider \= new firebase.auth.GoogleAuthProvider();  
      const res \= await firebase.auth().signInWithPopup(provider);  
      idToken \= await res.user.getIdToken();  
      userDisplay.textContent \= \`User: ${res.user.displayName}\`;  
      userDisplay.classList.remove('hidden');  
      loginBtn.classList.add('hidden');  
      chatInput.disabled \= false;  
      sendBtn.disabled \= false;  
      summarizeBtn.disabled \= false;  
      chatWindow.innerHTML \= \`\<p class="text-indigo-300"\>Session initialized. What would you like to reflect on today?\</p\>\`;  
    };

    sendBtn.onclick \= async () \=\> {  
      const message \= chatInput.value.trim();  
      if (\!message || \!idToken) return;  
      chatInput.value \= '';

      chatWindow.innerHTML \+= \`\<div class="text-indigo-300 font-medium"\>\<b\>You:\</b\> ${message}\</div\>\`;  
      history.push({ role: 'user', content: message });

      const res \= await fetch('/api/chat', {  
        method: 'POST',  
        headers: { 'Content-Type': 'application/json', 'Authorization': \`Bearer ${idToken}\` },  
        body: JSON.stringify({ journal\_id: currentJournalId, message, history })  
      });  
      const data \= await res.json();  
      currentJournalId \= data.journal\_id;  
      history.push({ role: 'model', content: data.reply });  
      chatWindow.innerHTML \+= \`\<div class="text-slate-200"\>\<b\>Gemini:\</b\> ${data.reply}\</div\>\`;  
      chatWindow.scrollTop \= chatWindow.scrollHeight;  
    };

    summarizeBtn.onclick \= async () \=\> {  
      if (\!currentJournalId || \!idToken) return;  
      chatWindow.innerHTML \+= \`\<div class="text-emerald-400 italic"\>Synthesizing cognitive metrics...\</div\>\`;  
      const res \= await fetch(\`/api/summarize/${currentJournalId}\`, {  
        method: 'POST',  
        headers: { 'Authorization': \`Bearer ${idToken}\` }  
      });  
      const data \= await res.json();  
      const s \= data.summary;  
      chatWindow.innerHTML \+= \`  
        \<div class="bg-emerald-950 border border-emerald-800 p-4 rounded-xl text-xs text-emerald-100 space-y-1 my-2"\>  
          \<p class="font-bold text-sm text-emerald-300"\>${s.title}\</p\>  
          \<p\>\<b\>Emotion:\</b\> ${s.primary\_emotion} (Sentiment Valence: ${s.sentiment\_score})\</p\>  
          \<p\>\<b\>Distortions Identified:\</b\> ${s.cognitive\_distortions\_detected.join(', ') || 'None'}\</p\>  
          \<p\>\<b\>Growth Insight:\</b\> ${s.growth\_insight}\</p\>  
          \<p\>\<b\>Action Items:\</b\> ${s.action\_items.join('; ')}\</p\>  
        \</div\>  
      \`;  
      chatWindow.scrollTop \= chatWindow.scrollHeight;  
    };  
  \</script\>  
\</body\>  
\</html\>  
\`\`\`

\#\#\# File: \`.gitignore\`  
\`\`\`gitignore  
\_\_pycache\_\_/  
\*.py\[cod\]  
.env  
.venv  
env/  
venv/  
.DS\_Store  
\*.log  
\`\`\`

\#\#\# File: \`.dockerignore\`  
\`\`\`dockerignore  
\_\_pycache\_\_  
\*.pyc  
\*.pyo  
\*.pyd  
.Python  
env/  
venv/  
.git  
.gitignore  
.dockerignore  
\`\`\`

\---

\#\# 5\. Deployment Script (\`deploy.sh\`)

\`\`\`bash  
\#\!/usr/bin/env bash  
set \-e

\# Configuration variables  
PROJECT\_ID="${PROJECT\_ID:-your-gcp-project-id}"  
REGION="${REGION:-us-central1}"  
SERVICE\_NAME="personal-gemini-journal"

echo "=== Deploying MindScribe to Google Cloud Run \==="  
gcloud config set project "$PROJECT\_ID"

\# 1\. Enable Required GCP APIs  
echo "\[1/4\] Enabling APIs..."  
gcloud services enable \\  
    run.googleapis.com \\  
    secretmanager.googleapis.com \\  
    firestore.googleapis.com \\  
    cloudbuild.googleapis.com

\# 2\. Grant IAM Roles to Cloud Run Service Account  
echo "\[2/4\] Configuring IAM bindings..."  
PROJECT\_NUM=$(gcloud projects describe "$PROJECT\_ID" \--format="value(projectNumber)")  
RUN\_SA="${PROJECT\_NUM}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding GEMINI\_API\_KEY \\  
    \--member="serviceAccount:${RUN\_SA}" \\  
    \--role="roles/secretmanager.secretAccessor" || true

gcloud projects add-iam-policy-binding "$PROJECT\_ID" \\  
    \--member="serviceAccount:${RUN\_SA}" \\  
    \--role="roles/datastore.user" || true

\# 3\. Build & Deploy to Cloud Run  
echo "\[3/4\] Building and deploying container to Cloud Run..."  
gcloud run deploy "$SERVICE\_NAME" \\  
    \--source . \\  
    \--region "$REGION" \\  
    \--allow-unauthenticated \\  
    \--set-secrets="GEMINI\_API\_KEY=GEMINI\_API\_KEY:latest"

\# 4\. Print Deployed URL  
echo "\[4/4\] Deployment complete\!"  
DEPLOYED\_URL=$(gcloud run services describe "$SERVICE\_NAME" \--region "$REGION" \--format="value(status.url)")  
echo "Public Cloud Run URL: $DEPLOYED\_URL"  
\`\`\`

\---

\#\# 6\. Submission Details & Social Media Template

\#\#\# Project Description (for submission form)  
\> \*\*MindScribe: Secure Personal Gemini Journal\*\*    
\> An authenticated AI journaling application built with a zero-trust architecture.    
\> \- \*\*Firebase Auth\*\*: Verifies JWT ID tokens on the FastAPI backend for secure user identity resolution.    
\> \- \*\*Cloud Firestore\*\*: Enforces tenant containment by storing journals strictly under \`/users/{uid}/journals/\`, backed by Firestore Security Rules.    
\> \- \*\*Google Cloud Run\*\*: Serverless container hosting with automated scaling and single-port static frontend delivery.    
\> \- \*\*Google AI Studio (Gemini 2.5 Flash)\*\*: Conducts empathetic journaling dialogues and outputs structured cognitive summaries (CBT distortions, emotional valence, and growth insights) via JSON schema enforcement.    
\> \- \*\*Secret Manager\*\*: Securely mounts the Gemini API key at runtime without exposing secrets in source code.

\#\#\# Social Post Copy (\`\#AccelerateAIwithCloudRun\`)  
\> 🚀 Excited to share \*\*MindScribe — A Secure Personal Gemini Journal\*\* built for the Google AI Studio & Cloud Run Challenge\!  
\>  
\> 🔒 \*\*Zero-Trust Auth & Key Management\*\*: Firebase Auth JWT verification on FastAPI backend with API keys secured via Google Cloud Secret Manager.    
\> 📊 \*\*Isolated Multi-Tenant Storage\*\*: User-scoped Cloud Firestore documents with zero cross-tenant leakage.    
\> 🧠 \*\*AI-Powered Reflection\*\*: Multi-turn dialogue with Gemini 2.5 Flash featuring automated CBT cognitive distortion detection, emotional valence scoring, and executive synthesis.    
\> ⚡ \*\*Cloud Native\*\*: Containerized and deployed serverless on Google Cloud Run.  
\>  
\> 🔗 \*\*Live App\*\*: \[Insert your Cloud Run URL\]    
\> 💻 \*\*GitHub Repo\*\*: \[Insert your GitHub Repository URL\]    
\>  
\> \#AccelerateAIwithCloudRun \#GoogleCloud \#GeminiAPI \#CloudRun \#Firebase \#FastAPI \#AI  
