# 🚀 Deploy TORQ Console to Vercel

**Status:** ✅ Ready for immediate deployment

## TL;DR - Quick Deploy

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to production
vercel --prod

# Add your API key
vercel env add ANTHROPIC_API_KEY production

# Test your deployment
curl https://your-project.vercel.app/health
```

## What You Need

1. **Vercel Account**: Free at [vercel.com](https://vercel.com)
2. **API Key**: Get from [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/)
3. **5 Minutes**: That's all it takes!

## Three Ways to Deploy

### 🎯 Option 1: Automated Script (Easiest)

```bash
./deploy-vercel.sh
```

The script will:
- ✅ Check prerequisites
- ✅ Validate your setup
- ✅ Deploy to Vercel
- ✅ Give you next steps

### ⚡ Option 2: Direct CLI (Fastest)

```bash
# One command deployment
vercel --prod

# Set your API key
vercel env add ANTHROPIC_API_KEY production
# Enter your key when prompted
```

### 🔗 Option 3: GitHub Integration (Automated)

1. Push code to GitHub (already done if you're reading this!)
2. Go to [vercel.com/new](https://vercel.com/new)
3. Select your repository
4. Add environment variable: `ANTHROPIC_API_KEY`
5. Click **Deploy** ✨

Every push to main = automatic deployment!

## After Deployment

### Test Your API

```bash
# Health check
curl https://your-project.vercel.app/health

# Try a search query
curl -X POST https://your-project.vercel.app/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "search for AI news"}'

# Try a build query
curl -X POST https://your-project.vercel.app/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "build a todo app"}'
```

### View Interactive Docs

```bash
open https://your-project.vercel.app/docs
```

Swagger UI with all endpoints documented!

## What Gets Deployed

- **Enhanced Prince Flowers API** - Your AI-powered assistant
- **REST Endpoints**:
  - `GET /` - API information
  - `GET /health` - Health check
  - `GET /docs` - Interactive documentation
  - `POST /chat` - Chat with Enhanced Prince
  - `POST /feedback` - Submit feedback

## Environment Variables

You need **at least one** of these:

| Variable | Where to Get | Why You Need It |
|----------|--------------|-----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) | Powers Claude AI (recommended) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/) | Powers GPT (alternative) |

### Setting Variables

**Via CLI:**
```bash
vercel env add ANTHROPIC_API_KEY production
```

**Via Dashboard:**
1. Go to your project in Vercel
2. Settings → Environment Variables
3. Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
4. Select "Production" environment
5. Save

## Files Overview

Everything is ready for you:

```
✓ vercel.json                 - Vercel configuration
✓ .vercelignore              - What NOT to deploy
✓ requirements.txt           - Python dependencies
✓ deploy-vercel.sh           - Deployment script
✓ enhanced_prince_api.py     - Your API (already exists!)
```

## Troubleshooting

### "Vercel CLI not found"

```bash
npm install -g vercel
```

### "API key not configured"

After deployment:
```bash
vercel env add ANTHROPIC_API_KEY production
```

### "Need more help?"

1. **Quick Reference**: See [VERCEL_QUICK_REFERENCE.md](VERCEL_QUICK_REFERENCE.md)
2. **Full Guide**: See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)
3. **Checklist**: See [VERCEL_CHECKLIST.md](VERCEL_CHECKLIST.md)

## Cost

**Free Tier Includes:**
- 100GB bandwidth/month
- 100GB-Hours execution
- Unlimited requests
- HTTPS automatic
- Custom domain support

Perfect for getting started! Upgrade if you need more.

## What You'll Get

🎉 **A fully-functional AI API** deployed to:
- `https://your-project.vercel.app`
- With health monitoring
- Interactive documentation
- Production-ready configuration
- Automatic HTTPS

## Next Steps

1. ✅ Deploy using one of the three options above
2. ✅ Set your API key
3. ✅ Test the endpoints
4. ✅ Share your API URL
5. ✅ Build something amazing! 🚀

## Support

- **Documentation**: [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) (complete guide)
- **Quick Commands**: [VERCEL_QUICK_REFERENCE.md](VERCEL_QUICK_REFERENCE.md)
- **Vercel Help**: [vercel.com/docs](https://vercel.com/docs)
- **Issues**: [GitHub Issues](https://github.com/pilotwaffle/TORQ-CONSOLE/issues)

---

**Ready?** Just run: `./deploy-vercel.sh` 🚀

Or jump straight to: `vercel --prod` ⚡
