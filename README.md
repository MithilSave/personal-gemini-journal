# MindScribe — Personal Gemini Journal

A production-grade, privacy-first personal AI journaling and cognitive brainstorming web application built for Google Cloud Run.

## ✨ Features

- **🔒 Zero-Trust Authentication** — Firebase Auth with JWT ID token verification on the FastAPI backend
- **🧠 AI-Powered Reflection** — Multi-turn dialogue with Gemini 2.5 Flash for empathetic journal coaching
- **📊 Cognitive Analysis** — Automated CBT cognitive distortion detection, emotional valence scoring, and growth insights via JSON schema enforcement
- **🗄️ Multi-Tenant Isolation** — User-scoped Cloud Firestore storage at `/users/{uid}/journals/` with security rules
- **🔑 Enterprise Secret Management** — API keys injected via Google Cloud Secret Manager
- **⚡ Serverless Deployment** — Single-container Cloud Run with static frontend serving

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Google Cloud Run                   │
│  ┌───────────────────────────────────────────────┐  │
│  │              FastAPI Backend                   │  │
│  │  ┌─────────┐ ┌──────────┐ ┌───────────────┐  │  │
│  │  │  Auth   │ │  Gemini  │ │   Firestore   │  │  │
│  │  │ (JWT)   │ │  Service │ │   Service     │  │  │
│  │  └─────────┘ └──────────┘ └───────────────┘  │  │
│  ├───────────────────────────────────────────────┤  │
│  │          Static Frontend (HTML/JS/CSS)        │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
         │              │               │
         ▼              ▼               ▼
   Firebase Auth   Gemini 2.5      Cloud Firestore
                    Flash
```

## 📁 Project Structure

```
personal-gemini-journal/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Package marker
│   │   ├── main.py                  # FastAPI application & route controllers
│   │   ├── auth.py                  # Firebase JWT verification middleware
│   │   ├── models.py                # Pydantic data schemas & response models
│   │   ├── gemini_service.py        # Google AI Studio Gemini API integration
│   │   └── firestore_service.py     # User-isolated Firestore persistence layer
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html                   # Main responsive single-page application
│   ├── app.js                       # Client state, Firebase Auth, and API interactions
│   └── styles.css                   # Premium dark-mode design system
├── firestore.rules                  # Multi-tenant security rules
├── deploy.sh                        # Automated GCP deployment script
├── .gitignore
├── .dockerignore
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- Firebase project with Google Sign-In enabled
- Gemini API key stored in Google Cloud Secret Manager as `GEMINI_API_KEY`
- `gcloud` CLI installed and authenticated

### 1. Configure Firebase

Update the `firebaseConfig` object in `frontend/app.js` with your Firebase project credentials:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_FIREBASE_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  appId: "YOUR_APP_ID"
};
```

### 2. Deploy to Cloud Run

```bash
# Set your GCP project ID
export PROJECT_ID="your-gcp-project-id"

# Run the deployment script
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Enable required GCP APIs (Cloud Run, Secret Manager, Firestore, Cloud Build)
2. Configure IAM bindings for the Cloud Run service account
3. Build and deploy the container to Cloud Run
4. Print the public URL

### Running Locally

To run the application locally without Docker, simply double-click the `run.bat` script in the root directory, or run it from your terminal:

```bash
.\run.bat
```

This will automatically start the server on **port 8000**. 

Then open your browser to: **[http://localhost:8000](http://localhost:8000)**

*(Note: We use port 8000 to prevent conflicts with local NGINX servers and to ensure Firebase Google Sign-In works perfectly on the `localhost` domain without throwing OAuth unauthorized domain errors).*

### 3. Deploy Firestore Security Rules

```bash
firebase deploy --only firestore:rules
```

## 🔐 Security Architecture

| Layer | Implementation |
|-------|---------------|
| **Authentication** | Firebase Auth → JWT ID token verified server-side on every request |
| **Authorization** | All Firestore operations scoped to `/users/{authenticated_uid}/` |
| **Secret Management** | Gemini API key injected via Cloud Secret Manager at runtime |
| **Data Isolation** | Firestore security rules enforce per-user tenant boundaries |
| **Prompt Safety** | System instructions separated from user input; structured JSON schema validation |

## 🧪 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send a journal message and receive an AI coaching response |
| `POST` | `/api/summarize/{journal_id}` | Generate a cognitive summary with CBT analysis |
| `GET` | `/api/journals` | List the authenticated user's journal sessions |

## 📊 Cognitive Summary Schema

The `/api/summarize` endpoint returns structured analysis:

```json
{
  "title": "Navigating Career Uncertainty",
  "key_themes": ["career", "self-doubt", "decision-making"],
  "sentiment_score": -0.3,
  "primary_emotion": "Anxiety",
  "cognitive_distortions_detected": ["Catastrophizing", "Fortune Telling"],
  "action_items": ["List 3 concrete next steps", "Schedule informational interviews"],
  "growth_insight": "Reframe uncertainty as exploration rather than threat..."
}
```

## 🏷️ Tags

`#AccelerateAIwithCloudRun` `#GoogleCloud` `#GeminiAPI` `#CloudRun` `#Firebase` `#FastAPI` `#AI`
