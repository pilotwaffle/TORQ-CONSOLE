# Deploying TORQ Console to Vercel

This guide explains how to deploy the TORQ Console Enhanced Prince API to Vercel.

## What Gets Deployed

The Vercel deployment focuses on the **Enhanced Prince Flowers API** (`enhanced_prince_api.py`), which provides:

- **REST API endpoints** for chat interactions with Enhanced Prince
- **Health check endpoint** for monitoring
- **Feedback system** for learning from user interactions
- **Action-oriented AI behavior** (immediate search vs. clarification)

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional but recommended):
   ```bash
   npm install -g vercel
   ```
3. **API Keys**: You need at least one of:
   - `ANTHROPIC_API_KEY` (Claude - recommended)
   - `OPENAI_API_KEY` (GPT models)

## Quick Deployment Methods

### Method 1: Deploy via Vercel CLI (Recommended)

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from the project root**:
   ```bash
   vercel
   ```

4. **Set environment variables**:
   ```bash
   # Add your Anthropic API key
   vercel env add ANTHROPIC_API_KEY production

   # Or add OpenAI API key
   vercel env add OPENAI_API_KEY production
   ```

5. **Deploy to production**:
   ```bash
   vercel --prod
   ```

### Method 2: Deploy via GitHub Integration

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Setup Vercel deployment"
   git push origin main
   ```

2. **Import project in Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Select your GitHub repository
   - Click "Import"

3. **Configure environment variables** in the Vercel dashboard:
   - Go to your project settings
   - Navigate to "Environment Variables"
   - Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
   - Set the value to your API key

4. **Deploy**:
   - Vercel will automatically deploy on every push to main
   - Manual deployments can be triggered from the Vercel dashboard

### Method 3: Deploy via Vercel Dashboard

1. **Visit** [vercel.com/new](https://vercel.com/new)
2. **Select "Import Git Repository"**
3. **Choose** your TORQ-CONSOLE repository
4. **Configure**:
   - Framework Preset: Other
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
5. **Add Environment Variables**:
   - `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
6. **Click Deploy**

## Configuration Files

### vercel.json

The project includes a `vercel.json` configuration that:

- Builds `enhanced_prince_api.py` as a Python serverless function
- Routes all requests to the API
- Configures environment variables
- Sets appropriate memory (3GB) and timeout (60s) limits

```json
{
  "version": 2,
  "builds": [
    {
      "src": "enhanced_prince_api.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "enhanced_prince_api.py"
    }
  ],
  "env": {
    "ANTHROPIC_API_KEY": "@anthropic_api_key",
    "OPENAI_API_KEY": "@openai_api_key",
    "PYTHON_VERSION": "3.11"
  },
  "functions": {
    "enhanced_prince_api.py": {
      "memory": 3008,
      "maxDuration": 60
    }
  }
}
```

### requirements-vercel.txt

A lightweight requirements file optimized for Vercel deployment:

```txt
# Core web framework
fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.8.0,<3.0.0

# AI clients
anthropic>=0.20.0
openai>=1.0.0

# Essential utilities
httpx>=0.24.0
aiohttp>=3.8.0
aiofiles>=23.0.0
python-dotenv>=1.0.0
```

## Environment Variables

Set these in your Vercel project settings:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | Claude API key for Enhanced Prince |
| `OPENAI_API_KEY` | Yes* | OpenAI API key (alternative to Anthropic) |

*At least one AI API key is required

### Adding Environment Variables via CLI

```bash
# Production environment
vercel env add ANTHROPIC_API_KEY production

# Preview/Development environments
vercel env add ANTHROPIC_API_KEY preview
vercel env add ANTHROPIC_API_KEY development
```

### Adding Environment Variables via Dashboard

1. Go to your project in Vercel
2. Click "Settings"
3. Navigate to "Environment Variables"
4. Add each variable with appropriate environments (Production, Preview, Development)

## Testing Your Deployment

Once deployed, you'll receive a URL like `https://your-project.vercel.app`

### 1. Health Check

```bash
curl https://your-project.vercel.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "enhanced_prince_available": true,
  "agent_memory_available": true,
  "api_key_configured": true
}
```

### 2. Chat Endpoint

```bash
curl -X POST https://your-project.vercel.app/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "search for top AI tools"}'
```

Expected response:
```json
{
  "response": "Here are the top AI tools...",
  "action_taken": "IMMEDIATE_ACTION",
  "interaction_id": "interaction_1",
  "debug_info": {
    "query_length": 25,
    "response_length": 500
  }
}
```

### 3. API Documentation

Visit `https://your-project.vercel.app/docs` to see the interactive API documentation.

## Usage Examples

### Example 1: Research Query (Immediate Action)

```bash
curl -X POST https://your-project.vercel.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search for latest AI news",
    "session_id": "user123",
    "user_id": "john_doe"
  }'
```

Enhanced Prince will immediately search and return results.

### Example 2: Build Request (Clarification)

```bash
curl -X POST https://your-project.vercel.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "build a todo app",
    "session_id": "user123"
  }'
```

Enhanced Prince will ask clarifying questions before proceeding.

### Example 3: Submitting Feedback

```bash
curl -X POST https://your-project.vercel.app/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": "interaction_1",
    "score": 0.9,
    "comment": "Very helpful response!"
  }'
```

## Vercel-Specific Considerations

### Function Limits

- **Max Function Size**: 50MB (configured in vercel.json)
- **Max Execution Time**: 60 seconds (configured)
- **Memory**: 3GB (configured)
- **Concurrent Executions**: Based on your Vercel plan

### Cold Starts

Serverless functions on Vercel may experience cold starts (1-3 seconds). To minimize impact:

- First request may be slower
- Subsequent requests are faster
- Consider implementing warming strategies for production

### Costs

Vercel's free tier includes:

- 100GB bandwidth
- 100GB-Hours serverless function execution
- Unlimited API requests

For production use with high traffic, consider upgrading to a paid plan.

## Troubleshooting

### "Enhanced Prince not available"

**Cause**: Missing or invalid API key

**Solution**:
1. Check environment variables in Vercel dashboard
2. Ensure `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set
3. Verify the API key is valid

```bash
# Test API key locally
export ANTHROPIC_API_KEY=your_key_here
python enhanced_prince_api.py
```

### "Module not found" errors

**Cause**: Missing dependencies

**Solution**:
1. Ensure `requirements-vercel.txt` is in project root
2. Vercel automatically installs from `requirements.txt`
3. If using custom name, update vercel.json:

```json
{
  "builds": [{
    "src": "enhanced_prince_api.py",
    "use": "@vercel/python",
    "config": {
      "requirementsFilename": "requirements-vercel.txt"
    }
  }]
}
```

### Function timeout

**Cause**: Request taking longer than 60 seconds

**Solution**:
1. Optimize queries to be faster
2. Increase timeout in vercel.json (Pro plan required for >60s)
3. Break complex requests into smaller parts

### Memory limit exceeded

**Cause**: Function using more than 3GB memory

**Solution**:
1. The configuration already sets memory to 3008MB (max for Pro)
2. Optimize code to use less memory
3. Consider moving heavy operations to external services

## Custom Domain

To add a custom domain:

1. Go to your project in Vercel
2. Click "Settings" → "Domains"
3. Add your domain (e.g., `api.yourdomain.com`)
4. Update DNS records as instructed by Vercel

## Continuous Deployment

Once set up with GitHub integration:

- **Automatic Deployments**: Every push to main triggers production deployment
- **Preview Deployments**: Every pull request gets a preview URL
- **Instant Rollbacks**: Revert to previous deployments with one click

## Monitoring

### View Logs

```bash
# View real-time logs
vercel logs your-project.vercel.app --follow

# View recent logs
vercel logs your-project.vercel.app
```

### Vercel Dashboard

Monitor your deployment health at:
- **Overview**: Request metrics, errors, bandwidth
- **Deployments**: History and status
- **Logs**: Real-time function logs
- **Analytics**: Traffic and performance insights (Pro plan)

## Security Best Practices

1. **Environment Variables**: Never commit API keys to Git
2. **CORS**: Configure `allow_origins` in `enhanced_prince_api.py` for production
3. **Rate Limiting**: Consider adding rate limiting for public APIs
4. **API Keys**: Rotate keys regularly
5. **HTTPS**: Vercel provides automatic HTTPS for all deployments

## Next Steps

After deployment:

1. **Test all endpoints** to ensure functionality
2. **Monitor performance** in Vercel dashboard
3. **Set up custom domain** for professional API endpoint
4. **Configure CORS** based on your client applications
5. **Add rate limiting** if exposing publicly
6. **Implement monitoring** and alerting for production use

## Support

- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **TORQ Console Issues**: [GitHub Issues](https://github.com/pilotwaffle/TORQ-CONSOLE/issues)
- **Vercel Support**: support@vercel.com (Pro plans)

## Alternative Deployment Options

If Vercel doesn't meet your needs, consider:

- **Railway**: See `RAILWAY-DEPLOYMENT.md`
- **AWS Lambda**: Similar serverless approach
- **Google Cloud Run**: Container-based deployment
- **DigitalOcean App Platform**: Simple PaaS deployment
- **Heroku**: Traditional PaaS deployment

---

**Need help?** Open an issue on GitHub or consult the Vercel documentation for more advanced configurations.
