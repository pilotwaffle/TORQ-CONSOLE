# Vercel Deployment Notes

## Configuration Overview

The TORQ Console Vercel deployment is configured to deploy the **Enhanced Prince Flowers API** as a serverless function.

### What Gets Deployed

- **File**: `enhanced_prince_api.py`
- **Runtime**: Python 3.11 via `@vercel/python`
- **Memory**: 3GB (3008MB)
- **Timeout**: 60 seconds
- **Max Size**: 50MB

### Key Configuration

```json
{
  "builds": [{
    "src": "enhanced_prince_api.py",
    "use": "@vercel/python"
  }]
}
```

### Environment Variables

Required (set in Vercel dashboard or via CLI):
- `ANTHROPIC_API_KEY` - For Claude API access (recommended)
- `OPENAI_API_KEY` - For GPT API access (alternative)

At least one API key must be configured.

### API Endpoints

Once deployed, your API will have:

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `POST /chat` - Chat with Enhanced Prince
- `POST /feedback` - Submit feedback for learning

### Dependencies

Dependencies are automatically installed from `requirements.txt` during deployment.

For a minimal deployment, use `requirements-vercel.txt` instead:
1. Rename `requirements-vercel.txt` to `requirements.txt`
2. Or configure in vercel.json:
   ```json
   "config": {
     "requirementsFilename": "requirements-vercel.txt"
   }
   ```

### Cold Starts

First request may take 1-3 seconds (cold start). Subsequent requests are faster as the container stays warm.

To minimize cold starts:
- Keep dependencies minimal
- Avoid heavy initialization in startup events
- Consider implementing a warming strategy (periodic health checks)

### CORS Configuration

Default configuration allows all origins (`allow_origins=["*"]`).

For production, update in `enhanced_prince_api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.com",
        "https://app.your-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Troubleshooting

#### "Module not found"
- Ensure dependency is in `requirements.txt`
- Check `.vercelignore` isn't excluding needed files

#### "API key not configured"
- Set environment variables in Vercel dashboard
- Or use CLI: `vercel env add ANTHROPIC_API_KEY production`

#### "Function timeout"
- Increase `maxDuration` in vercel.json (max 60s for Pro)
- Optimize slow operations
- Break complex tasks into smaller requests

#### "Memory limit exceeded"
- Current limit: 3GB (max for Pro plan)
- Remove heavy dependencies
- Optimize memory usage

### Monitoring

View logs in real-time:
```bash
vercel logs your-project.vercel.app --follow
```

Check function metrics in Vercel dashboard:
- Request count
- Error rate
- Execution time
- Bandwidth usage

### Security Considerations

1. **API Keys**: Never commit to Git, use Vercel environment variables
2. **CORS**: Restrict origins in production
3. **Rate Limiting**: Consider implementing for public APIs
4. **Input Validation**: All inputs validated by Pydantic models
5. **HTTPS**: Automatic with Vercel (always enabled)

### Cost Considerations

Vercel free tier includes:
- 100GB bandwidth
- 100GB-Hours function execution
- Unlimited requests

Monitor usage in dashboard to avoid overages.

### References

- [Vercel Python Documentation](https://vercel.com/docs/functions/runtimes/python)
- [Full Deployment Guide](VERCEL_DEPLOYMENT.md)
- [Quick Reference](VERCEL_QUICK_REFERENCE.md)
- [Deployment Checklist](VERCEL_CHECKLIST.md)

---

**Last Updated**: February 2024
**Configuration Version**: 1.0
