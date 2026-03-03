#!/bin/bash
set -euo pipefail

# TalentLens - GCP Cloud Run Deployment
# Usage: ./deploy.sh <PROJECT_ID> <REGION>

PROJECT_ID="${1:?Usage: ./deploy.sh <PROJECT_ID> <REGION>}"
REGION="${2:-us-central1}"
BACKEND_SERVICE="talentlens-backend"
FRONTEND_SERVICE="talentlens-frontend"
REPO="talentlens"

echo "=== TalentLens - Deploying to GCP ==="
echo "Project: $PROJECT_ID | Region: $REGION"

gcloud config set project "$PROJECT_ID"

# Create Artifact Registry repo if needed
gcloud artifacts repositories describe "$REPO" --location="$REGION" 2>/dev/null || \
  gcloud artifacts repositories create "$REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="TalentLens containers"

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"

# Build and push backend
echo "=== Building backend ==="
docker build --platform linux/amd64 -t "${REGISTRY}/${BACKEND_SERVICE}" -f infrastructure/backend/Dockerfile .
docker push "${REGISTRY}/${BACKEND_SERVICE}"

# Deploy backend
echo "=== Deploying backend ==="
gcloud run deploy "$BACKEND_SERVICE" \
  --image "${REGISTRY}/${BACKEND_SERVICE}" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "ENV=production" \
  --set-env-vars "DATABASE_URL=${DATABASE_URL:-}" \
  --set-env-vars "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}" \
  --set-env-vars "DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY:-}" \
  --set-env-vars "FIREFLIES_WEBHOOK_SECRET=${FIREFLIES_WEBHOOK_SECRET:-}" \
  --set-env-vars "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:-}" \
  --set-env-vars "SLACK_DEFAULT_CHANNEL=${SLACK_DEFAULT_CHANNEL:-}"

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" --region "$REGION" --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"

# Build frontend with backend URL
echo "=== Building frontend ==="
docker build --platform linux/amd64 \
  --build-arg VITE_API_URL="$BACKEND_URL" \
  -t "${REGISTRY}/${FRONTEND_SERVICE}" \
  -f infrastructure/frontend/Dockerfile .
docker push "${REGISTRY}/${FRONTEND_SERVICE}"

# Deploy frontend
echo "=== Deploying frontend ==="
gcloud run deploy "$FRONTEND_SERVICE" \
  --image "${REGISTRY}/${FRONTEND_SERVICE}" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 3000 \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3

# Update CORS
FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" --region "$REGION" --format 'value(status.url)')
gcloud run services update "$BACKEND_SERVICE" \
  --region "$REGION" \
  --update-env-vars "CORS_ORIGINS=${FRONTEND_URL}"

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "Health:   $BACKEND_URL/api/health"
