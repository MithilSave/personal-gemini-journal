from google.cloud import firestore
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.models import CognitiveSummary

class FirestoreJournalStore:
    def __init__(self):
        self.db = firestore.Client()

    def _get_journal_ref(self, user_id: str, journal_id: str):
        # Strict tenant boundary: users/{uid}/journals/{journal_id}
        return self.db.collection("users").document(user_id).collection("journals").document(journal_id)

    def save_message_turn(self, user_id: str, journal_id: str, user_msg: str, model_reply: str):
        journal_ref = self._get_journal_ref(user_id, journal_id)
        now = datetime.now(timezone.utc)

        journal_ref.set({"last_updated": now, "user_id": user_id}, merge=True)
        messages_ref = journal_ref.collection("messages")
        messages_ref.add({"role": "user", "content": user_msg, "timestamp": now})
        messages_ref.add({"role": "model", "content": model_reply, "timestamp": now})

    def save_summary(self, user_id: str, journal_id: str, summary: CognitiveSummary):
        journal_ref = self._get_journal_ref(user_id, journal_id)
        journal_ref.set({
            "summary": summary.model_dump(),
            "summary_created_at": datetime.now(timezone.utc)
        }, merge=True)

    def list_user_journals(self, user_id: str) -> List[Dict[str, Any]]:
        docs = self.db.collection("users").document(user_id).collection("journals").order_by(
            "last_updated", direction=firestore.Query.DESCENDING
        ).limit(25).stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if data.get("last_updated"):
                data["last_updated"] = data["last_updated"].isoformat()
            if data.get("created_at"):
                data["created_at"] = data["created_at"].isoformat()
            results.append(data)
        return results

    def get_journal_messages(self, user_id: str, journal_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages from a specific journal session for history replay."""
        journal_ref = self._get_journal_ref(user_id, journal_id)
        messages = journal_ref.collection("messages").order_by("timestamp").stream()

        results = []
        for msg in messages:
            data = msg.to_dict()
            # Convert timestamp to ISO string for JSON serialization
            if data.get("timestamp"):
                data["timestamp"] = data["timestamp"].isoformat()
            results.append(data)
        return results

    def get_mood_timeline(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch summary data from all journals for the emotion timeline chart."""
        docs = self.db.collection("users").document(user_id).collection("journals").order_by(
            "last_updated", direction=firestore.Query.ASCENDING
        ).limit(50).stream()

        timeline = []
        for doc in docs:
            data = doc.to_dict()
            if data.get("summary"):
                entry = {
                    "journal_id": doc.id,
                    "date": data.get("last_updated").isoformat() if data.get("last_updated") else None,
                    "title": data["summary"].get("title", "Untitled"),
                    "sentiment_score": data["summary"].get("sentiment_score", 0),
                    "primary_emotion": data["summary"].get("primary_emotion", "Unknown"),
                }
                timeline.append(entry)
        return timeline

