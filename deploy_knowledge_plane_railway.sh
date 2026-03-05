#!/bin/bash
# TORQ Knowledge Plane Railway Deployment Script
# This script deploys the TORQ Knowledge Plane backend to Railway

set -e

echo "=================================="
echo "TORQ Knowledge Plane Deployment"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Railway CLI not found. Installing...${NC}"
    npm install -g @railway/cli
fi

echo -e "${GREEN}Railway CLI installed.${NC}"
echo ""

# Check if logged in
echo "Checking Railway login status..."
if railway whoami &> /dev/null; then
    echo -e "${GREEN}Already logged in as: $(railway whoami)${NC}"
else
    echo -e "${YELLOW}Not logged in. Please login to Railway...${NC}"
    railway login
fi

echo ""
echo "=================================="
echo "Preparing Knowledge Plane Deployment"
echo "=================================="
echo ""

# Navigate to TORQ-CONSOLE directory
cd /e/TORQ-CONSOLE

# Verify railway_app.py has Knowledge Plane routes
if grep -q "Knowledge Plane Routes" railway_app.py; then
    echo -e "${GREEN}Knowledge Plane routes detected in railway_app.py${NC}"
else
    echo -e "${RED}Knowledge Plane routes not found. Adding...${NC}"
    python add_knowledge_routes.py
fi

# Check if knowledge_plane module exists
if [ -f "torq_console/knowledge_plane/railway_integration.py" ]; then
    echo -e "${GREEN}Knowledge Plane module exists${NC}"
else
    echo -e "${RED}Knowledge Plane module not found!${NC}"
    exit 1
fi

echo ""
echo "=================================="
echo "Railway Project Setup"
echo "=================================="
echo ""

# Check if project is linked
if railway status &> /dev/null; then
    echo -e "${GREEN}Railway project is linked${NC}"
    railway status
else
    echo -e "${YELLOW}No Railway project linked. Please:${NC}"
    echo "1. Open Railway in your browser: https://railway.app/new"
    echo "2. Create a new project or select existing"
    echo "3. Run: railway link"
    echo ""
    read -p "Press Enter after linking your Railway project..."
fi

echo ""
echo "=================================="
echo "Setting Environment Variables"
echo "=================================="
echo ""

# Set environment variables
echo "Setting environment variables..."

# Get values from .env file
if [ -f .env ]; then
    OPENAI_KEY=$(grep OPENAI_API_KEY .env | cut -d'=' -f2)
    SUPABASE_URL=$(grep SUPABASE_URL .env | cut -d'=' -f2)
    SUPABASE_KEY=$(grep SUPABASE_SERVICE_ROLE_KEY .env | cut -d'=' -f2)

    if [ -n "$OPENAI_KEY" ]; then
        railway variables set OPENAI_API_KEY="$OPENAI_KEY" 2>/dev/null || true
        echo -e "${GREEN}Set OPENAI_API_KEY${NC}"
    fi

    if [ -n "$SUPABASE_URL" ]; then
        railway variables set SUPABASE_URL="$SUPABASE_URL" 2>/dev/null || true
        echo -e "${GREEN}Set SUPABASE_URL${NC}"
    fi

    if [ -n "$SUPABASE_KEY" ]; then
        railway variables set SUPABASE_SERVICE_ROLE_KEY="$SUPABASE_KEY" 2>/dev/null || true
        echo -e "${GREEN}Set SUPABASE_SERVICE_ROLE_KEY${NC}"
    fi
fi

# Set TORQ_BRAIN_KEY (can be same as OPENAI or a separate key)
railway variables set TORQ_BRAIN_KEY="$OPENAI_KEY" 2>/dev/null || true
echo -e "${GREEN}Set TORQ_BRAIN_KEY${NC}"

# Set production flags
railway variables set TORQ_CONSOLE_PRODUCTION=true 2>/dev/null || true
railway variables set TORQ_DISABLE_LOCAL_LLM=true 2>/dev/null || true
railway variables set TORQ_DISABLE_GPU=true 2>/dev/null || true
echo -e "${GREEN}Set production flags${NC}"

echo ""
echo "=================================="
echo "Deploying to Railway"
echo "=================================="
echo ""

# Trigger deployment
echo "Uploading to Railway..."
railway up

echo ""
echo "=================================="
echo "Deployment Status"
echo "=================================="
echo ""

# Wait for deployment to complete
echo "Waiting for deployment to complete..."
sleep 5

# Get deployment status
railway status

echo ""
echo "=================================="
echo "Deployment Complete!"
echo "=================================="
echo ""

# Get service URL
SERVICE_URL=$(railway domain 2>/dev/null | head -1)
echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
echo ""

# Health check
echo "Running health check..."
HEALTH_URL="$SERVICE_URL/health"
echo "Health check URL: $HEALTH_URL"

if command -v curl &> /dev/null; then
    sleep 5
    curl -s "$HEALTH_URL" | python -m json.tool || echo "Health check not ready yet"
fi

echo ""
echo "=================================="
echo "Knowledge Plane API Endpoints"
echo "=================================="
echo ""
echo "POST $SERVICE_URL/api/knowledge/store"
echo "     Store a knowledge entry"
echo ""
echo "POST $SERVICE_URL/api/knowledge/search"
echo "     Search the knowledge base"
echo ""
echo "GET  $SERVICE_URL/api/knowledge/recent?limit=20"
echo "     Get recent knowledge entries"
echo ""
echo "GET  $SERVICE_URL/api/knowledge/stats"
echo "     Get knowledge base statistics"
echo ""
echo "GET  $SERVICE_URL/api/knowledge/health"
echo "     Knowledge Plane health check"
echo ""

echo -e "${GREEN}Deployment Summary${NC}"
echo "=================================="
echo "Service URL: $SERVICE_URL"
echo "Knowledge Plane: Enabled"
echo "Version: 1.1.0-knowledge-plane"
echo ""
echo "Next steps:"
echo "1. Test the health endpoint: curl $SERVICE_URL/api/knowledge/health"
echo "2. Store a knowledge entry: curl -X POST $SERVICE_URL/api/knowledge/store -d '{\"content\": \"test\"}'"
echo "3. Search the knowledge base: curl -X POST $SERVICE_URL/api/knowledge/search -d '{\"query\": \"test\"}'"
