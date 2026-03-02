#!/bin/bash
set -euo pipefail

# Cerebro Intelligence Fabric - GCP Cloud Run Deployment
# Usage: ./deploy.sh <PROJECT_ID> <REGION>
# Example: ./deploy.sh my-gcp-project us-central1

PROJECT_ID="${1:?Usage: ./deploy.sh <PROJECT_ID> <REGION>}"
REGION="${2:-us-central1}"
BACKEND_SERVICE="kairos-backend"
FRONTEND_SERVICE="kairos-frontend"
REPO="kairos"

echo "=== Cerebro Intelligence Fabric - Deploying to GCP ==="
echo "Project: $PROJECT_ID | Region: $REGION"

# Set project
gcloud config set project "$PROJECT_ID"

# Create Artifact Registry repo if needed
gcloud artifacts repositories describe "$REPO" --location="$REGION" 2>/dev/null || \
  gcloud artifacts repositories create "$REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Cerebro Intelligence Fabric containers"

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"

# Build and push backend
echo "=== Building backend ==="
docker build --platform linux/amd64 -t "${REGISTRY}/${BACKEND_SERVICE}" -f infrastructure/backend/Dockerfile .
docker push "${REGISTRY}/${BACKEND_SERVICE}"

# Deploy backend to Cloud Run
# NOTE: --allow-unauthenticated is used here because the frontend calls the API directly.
# For production with sensitive data, consider using IAM authentication
# and proxying all API calls through the frontend service.
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
  --set-env-vars "NEO4J_URI=${NEO4J_URI:-}" \
  --set-env-vars "NEO4J_USERNAME=${NEO4J_USERNAME:-neo4j}" \
  --set-env-vars "NEO4J_PASSWORD=${NEO4J_PASSWORD:-}" \
  --set-env-vars "OPENAI_API_KEY=${OPENAI_API_KEY:-}" \
  --set-env-vars "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}"

# Get backend URL
BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" --region "$REGION" --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"

# Build frontend with backend URL baked in
echo "=== Building frontend ==="
docker build --platform linux/amd64 \
  --build-arg VITE_API_URL="$BACKEND_URL" \
  -t "${REGISTRY}/${FRONTEND_SERVICE}" \
  -f infrastructure/frontend/Dockerfile .
docker push "${REGISTRY}/${FRONTEND_SERVICE}"

# Deploy frontend to Cloud Run
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

# Update backend CORS with frontend URL
FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" --region "$REGION" --format 'value(status.url)')

gcloud run services update "$BACKEND_SERVICE" \
  --region "$REGION" \
  --update-env-vars "CORS_ORIGINS=${FRONTEND_URL}"

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "Health:   $BACKEND_URL/api/health"
