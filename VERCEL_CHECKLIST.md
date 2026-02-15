# Vercel Deployment Checklist

Use this checklist before deploying to Vercel:

## Pre-Deployment

- [ ] **API Keys Ready**: Have your `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- [ ] **Vercel CLI Installed**: `npm install -g vercel` (or use GitHub integration)
- [ ] **Git Committed**: All changes committed and pushed
- [ ] **Review Files**: Check what will be deployed (use `.vercelignore`)

## Configuration

- [ ] **vercel.json**: Review configuration (memory, timeout, environment)
- [ ] **requirements.txt**: Ensure all dependencies are listed
- [ ] **CORS Settings**: Update `allow_origins` in `enhanced_prince_api.py` if needed
- [ ] **Environment Variables**: Plan which variables to set in Vercel

## Deployment Steps

### Option 1: CLI Deployment

```bash
# Login
vercel login

# Deploy to preview (test first)
vercel

# Test the preview URL
curl https://your-preview.vercel.app/health

# Deploy to production
vercel --prod
```

### Option 2: GitHub Integration

1. Push code to GitHub
2. Import project in Vercel dashboard
3. Configure environment variables
4. Deploy automatically on push

## Post-Deployment

- [ ] **Add API Keys**: Set environment variables in Vercel
  ```bash
  vercel env add ANTHROPIC_API_KEY production
  ```

- [ ] **Test Health Endpoint**:
  ```bash
  curl https://your-project.vercel.app/health
  ```

- [ ] **Test Chat Endpoint**:
  ```bash
  curl -X POST https://your-project.vercel.app/chat \
    -H "Content-Type: application/json" \
    -d '{"query": "search for AI news"}'
  ```

- [ ] **Check API Documentation**:
  Visit `https://your-project.vercel.app/docs`

- [ ] **Monitor Logs**:
  ```bash
  vercel logs your-project.vercel.app --follow
  ```

## Production Hardening

- [ ] **Update CORS**: Change `allow_origins=["*"]` to specific domains
  ```python
  allow_origins=[
      "https://your-frontend.com",
      "https://app.your-domain.com"
  ]
  ```

- [ ] **Rate Limiting**: Consider adding rate limiting (see deployment guide)
- [ ] **Custom Domain**: Set up custom domain in Vercel dashboard
- [ ] **Monitoring**: Set up error tracking and monitoring
- [ ] **Analytics**: Enable Vercel Analytics for insights

## Troubleshooting

If deployment fails:

1. **Check build logs** in Vercel dashboard
2. **Verify dependencies** in requirements.txt
3. **Test locally** with the same Python version (3.11)
4. **Review .vercelignore** to ensure needed files aren't excluded
5. **Check function size** - should be under 50MB

Common issues:

- **"Module not found"**: Add missing package to requirements.txt
- **"API key not configured"**: Set environment variables in Vercel
- **"Function timeout"**: Optimize code or increase timeout (Pro plan)
- **"Cold start slow"**: Normal for first request, consider warming strategies

## Security Checklist

- [ ] **API Keys**: Never commit API keys to Git
- [ ] **Environment Variables**: Use Vercel's env system
- [ ] **CORS**: Restrict to specific origins in production
- [ ] **HTTPS**: Automatic with Vercel (always enabled)
- [ ] **Rate Limiting**: Implement for public APIs
- [ ] **Input Validation**: All inputs validated by Pydantic models

## Performance Optimization

- [ ] **Dependencies**: Keep requirements.txt minimal
- [ ] **Cold Starts**: Accept 1-3s for first request
- [ ] **Memory**: Configured to 3GB for optimal performance
- [ ] **Timeout**: Set to 60s for complex queries
- [ ] **Caching**: Consider caching frequent queries

## Documentation

- [ ] **README**: Update with your Vercel URL
- [ ] **API Docs**: Share `/docs` endpoint URL
- [ ] **Environment**: Document all required environment variables
- [ ] **Usage Examples**: Provide curl examples for users

## Support Resources

- **Deployment Guide**: [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)
- **Quick Reference**: [VERCEL_QUICK_REFERENCE.md](VERCEL_QUICK_REFERENCE.md)
- **Vercel Docs**: https://vercel.com/docs
- **GitHub Issues**: https://github.com/pilotwaffle/TORQ-CONSOLE/issues

---

**Ready to deploy?** Run: `./deploy-vercel.sh` or `vercel --prod`
