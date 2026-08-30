#!/usr/bin/env bash
set -e

# Configuration variables
PROJECT_ID="${PROJECT_ID:-personal-gemini-journal-507013}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="personal-gemini-journal"

echo "=== Deploying MindScribe to Google Cloud Run ==="
gcloud config set project "$PROJECT_ID"

# 1. Enable Required GCP APIs
echo "[1/4] Enabling APIs..."
gcloud services enable \
    run.googleapis.com \
    secretmanager.googleapis.com \
    firestore.googleapis.com \
    cloudbuild.googleapis.com

# 2. Grant IAM Roles to Cloud Run Service Account
echo "[2/4] Configuring IAM bindings..."
PROJECT_NUM=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
RUN_SA="${PROJECT_NUM}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
    --member="serviceAccount:${RUN_SA}" \
    --role="roles/secretmanager.secretAccessor" || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${RUN_SA}" \
    --role="roles/datastore.user" || true

# 3. Build & Deploy to Cloud Run
echo "[3/4] Building and deploying container to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest"

# 4. Print Deployed URL
echo "[4/4] Deployment complete!"
DEPLOYED_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
echo "Public Cloud Run URL: $DEPLOYED_URL"
