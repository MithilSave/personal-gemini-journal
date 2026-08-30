$ErrorActionPreference = "Stop"

$PROJECT_ID = "personal-gemini-journal-507013"
$REGION = "us-central1"
$SERVICE_NAME = "personal-gemini-journal"

Write-Host "=== Deploying MindScribe to Google Cloud Run ===" -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# 1. Enable Required GCP APIs
Write-Host "[1/4] Enabling APIs..." -ForegroundColor Yellow
gcloud services enable `
    run.googleapis.com `
    secretmanager.googleapis.com `
    firestore.googleapis.com `
    cloudbuild.googleapis.com

# 2. Grant IAM Roles to Cloud Run Service Account
Write-Host "[2/4] Configuring IAM bindings..." -ForegroundColor Yellow
$PROJECT_NUM = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
$RUN_SA = "${PROJECT_NUM}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding GEMINI_API_KEY `
    --member="serviceAccount:${RUN_SA}" `
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:${RUN_SA}" `
    --role="roles/datastore.user"

# 3. Build & Deploy to Cloud Run
Write-Host "[3/4] Building and deploying container to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --source . `
    --region $REGION `
    --allow-unauthenticated `
    --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest"

# 4. Print Deployed URL
Write-Host "[4/4] Deployment complete!" -ForegroundColor Green
$DEPLOYED_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
Write-Host "Public Cloud Run URL: $DEPLOYED_URL" -ForegroundColor Cyan
