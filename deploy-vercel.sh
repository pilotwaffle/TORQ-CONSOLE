#!/bin/bash
# Deploy TORQ Console Enhanced Prince API to Vercel

set -e

echo "=========================================="
echo "TORQ Console - Vercel Deployment Script"
echo "=========================================="
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found"
    echo ""
    echo "Install it with:"
    echo "  npm install -g vercel"
    echo ""
    exit 1
fi

echo "✅ Vercel CLI found"
echo ""

# Check for API keys
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: No API keys detected in environment"
    echo ""
    echo "You'll need to set at least one of:"
    echo "  - ANTHROPIC_API_KEY (recommended)"
    echo "  - OPENAI_API_KEY"
    echo ""
    echo "After deployment, add it with:"
    echo "  vercel env add ANTHROPIC_API_KEY production"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ API key detected in environment"
    echo ""
fi

# Check if this is first deployment
if [ ! -f ".vercel/project.json" ]; then
    echo "📦 First-time deployment detected"
    echo ""
    echo "This will:"
    echo "  1. Create a new Vercel project"
    echo "  2. Deploy the Enhanced Prince API"
    echo "  3. Give you a production URL"
    echo ""
    read -p "Ready to deploy? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
    
    # First deployment
    echo ""
    echo "🚀 Deploying to Vercel..."
    vercel --prod
else
    echo "📦 Existing project detected"
    echo ""
    echo "This will deploy to production"
    echo ""
    read -p "Deploy now? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
    
    # Subsequent deployment
    echo ""
    echo "🚀 Deploying to Vercel..."
    vercel --prod
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Test your deployment:"
echo "   curl https://your-project.vercel.app/health"
echo ""
echo "2. Add API keys (if not already set):"
echo "   vercel env add ANTHROPIC_API_KEY production"
echo ""
echo "3. View logs:"
echo "   vercel logs"
echo ""
echo "4. Visit your API documentation:"
echo "   https://your-project.vercel.app/docs"
echo ""
echo "For more information, see VERCEL_DEPLOYMENT.md"
echo ""
