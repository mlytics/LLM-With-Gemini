#!/bin/bash

# ============================================================================
# Google Cloud Run Deployment Script
# ============================================================================
# This script builds and deploys the Agent-Will-Smith API to Google Cloud Run
# 
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Secrets must be created in Google Secret Manager:
#   - GEMINI_API_KEY
#   - API_BEARER_TOKEN
#   - GOOGLE_SEARCH_KEY (optional)
#   - GOOGLE_SEARCH_ENGINE_ID (optional)
# ============================================================================

set -e  # Exit on error

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
PROJECT_ID="uat-env-888888"
PROJECT_NAME="p-uat"
SERVICE_NAME="agent-william-smith"
REGION="asia-east1"  # Change to your preferred region
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Set test environment variables (for running tests before deployment)
# These are only used if you uncomment the test step below
# They can also be set in .env file or exported before running this script
export TEST_DOMAIN="${TEST_DOMAIN:-https://m.cnyes.com/news/id/5627491}"
export TEST_BASE_URL="${TEST_BASE_URL:-https://m.cnyes.com}"

# Optional: Run tests before deployment (uncomment to enable)
# echo "Running tests with TEST_DOMAIN=${TEST_DOMAIN}..."
# if ! pytest tests/ -v --tb=short; then
#     echo "❌ Tests failed! Deployment aborted."
#     exit 1
# fi
# echo "✅ All tests passed!"

# Set the project
echo "Setting GCP project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Build and push the Docker image
echo "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "GEMINI_MODEL=gemini-2.5-flash-lite" \
  --set-env-vars "ALLOWED_ORIGINS=https://aigc-mvp.mlytics.co" \
  --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest" \
  --set-secrets "API_BEARER_TOKEN=API_BEARER_TOKEN:latest" \
  --set-secrets "GOOGLE_SEARCH_KEY=GOOGLE_SEARCH_KEY:latest" \
  --set-secrets "GOOGLE_SEARCH_ENGINE_ID=GOOGLE_SEARCH_ENGINE_ID:latest"

echo ""
echo "✅ Deployment complete!"
echo "Service URL will be displayed above"
echo ""
echo "Note: TEST_DOMAIN and TEST_BASE_URL are set for local test execution only."
echo "      They are NOT deployed to Cloud Run (only used if running tests before deployment)."
