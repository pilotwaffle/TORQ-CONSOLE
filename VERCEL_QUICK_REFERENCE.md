# Vercel Deployment - Quick Reference

## Quick Deploy

```bash
# One-line deployment
vercel --prod

# Or use the deployment script
./deploy-vercel.sh
```

## Essential Commands

```bash
# Login to Vercel
vercel login

# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Add environment variable
vercel env add ANTHROPIC_API_KEY production

# View logs
vercel logs

# View project info
vercel inspect
```

## Test Endpoints

```bash
# Health check
curl https://your-project.vercel.app/health

# Chat (Type A: Research)
curl -X POST https://your-project.vercel.app/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "search for AI news"}'

# Chat (Type B: Build)
curl -X POST https://your-project.vercel.app/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "build a todo app"}'

# API Documentation
open https://your-project.vercel.app/docs
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | Claude API key |
| `OPENAI_API_KEY` | Yes* | OpenAI API key |

*At least one is required

## Project Structure

```
.
├── enhanced_prince_api.py     # Main API (what gets deployed)
├── vercel.json                # Vercel configuration
├── requirements.txt           # Python dependencies
├── requirements-vercel.txt    # Minimal Vercel dependencies
├── .vercelignore              # Files to exclude
├── deploy-vercel.sh           # Deployment script
└── VERCEL_DEPLOYMENT.md       # Full documentation
```

## Configuration

### vercel.json
- Python runtime with @vercel/python
- 3GB memory, 60s timeout
- Routes all traffic to enhanced_prince_api.py

### requirements.txt
- Core web framework (FastAPI, Uvicorn)
- AI clients (Anthropic, OpenAI)
- Essential utilities
- No heavy ML libraries (for faster cold starts)

## Troubleshooting

### API key not working
```bash
# Check environment variables
vercel env ls

# Add missing key
vercel env add ANTHROPIC_API_KEY production
```

### Module not found
```bash
# Ensure requirements.txt is in root
# Vercel automatically installs from it
ls -la requirements.txt
```

### Function timeout
```bash
# Check timeout in vercel.json
# Max is 60s for Pro plan
cat vercel.json | grep maxDuration
```

## Resources

- **Full Guide**: See `VERCEL_DEPLOYMENT.md`
- **Vercel Docs**: https://vercel.com/docs
- **GitHub**: https://github.com/pilotwaffle/TORQ-CONSOLE

## Support

- GitHub Issues: [Report a problem](https://github.com/pilotwaffle/TORQ-CONSOLE/issues)
- Vercel Support: support@vercel.com (Pro plans)
