#!/bin/bash
set -euo pipefail

# TalentLens - GCP Cloud Run Deployment
# Usage: ./deploy.sh <PROJECT_ID> <REGION>
#
# Env vars (DATABASE_URL, ANTHROPIC_API_KEY, etc.) are only updated when set
# in the local shell. If unset, the existing Cloud Run values are preserved.
# To set them for the first time or update them, export before running:
#   export DATABASE_URL="postgresql+asyncpg://..." ANTHROPIC_API_KEY="sk-..."
#   ./deploy.sh up-gpt-468817 us-central1

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
GCS_BUCKET="${PROJECT_ID}-talentlens-uploads"

# Create GCS bucket for CV uploads if needed
if ! gsutil ls -b "gs://${GCS_BUCKET}" 2>/dev/null; then
  echo "=== Creating GCS bucket ${GCS_BUCKET} ==="
  gsutil mb -l "$REGION" "gs://${GCS_BUCKET}"
  gsutil iam ch allUsers:objectViewer "gs://${GCS_BUCKET}"
fi

# Build and push backend
echo "=== Building backend ==="
docker build --platform linux/amd64 -t "${REGISTRY}/${BACKEND_SERVICE}" -f infrastructure/backend/Dockerfile .
docker push "${REGISTRY}/${BACKEND_SERVICE}"

# Build env var flags — only include vars that are set locally.
# Uses --update-env-vars so existing Cloud Run values are preserved.
ENV_VARS="ENV=production||GCS_BUCKET=${GCS_BUCKET}"
for var in DATABASE_URL ANTHROPIC_API_KEY DEEPGRAM_API_KEY FIREFLIES_WEBHOOK_SECRET SLACK_BOT_TOKEN SLACK_DEFAULT_CHANNEL; do
  if [ -n "${!var:-}" ]; then
    ENV_VARS="${ENV_VARS}||${var}=${!var}"
    echo "  -> $var will be updated"
  else
    echo "  -> $var not set locally, keeping existing Cloud Run value"
  fi
done

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
  --update-env-vars "^||^${ENV_VARS}"

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

# Update CORS — include both URL formats (short hash and numbered project)
FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" --region "$REGION" --format 'value(status.url)')
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
FRONTEND_URL_NUMBERED="https://${FRONTEND_SERVICE}-${PROJECT_NUMBER}.${REGION}.run.app"
gcloud run services update "$BACKEND_SERVICE" \
  --region "$REGION" \
  --update-env-vars "^||^CORS_ORIGINS=${FRONTEND_URL_NUMBERED},${FRONTEND_URL},http://localhost:5173"

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "Health:   $BACKEND_URL/api/health"
