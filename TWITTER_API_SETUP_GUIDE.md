# Twitter (X) API Setup Guide for TORQ Console

## Quick Start: Get Twitter API Credentials

### Step 1: Apply for Twitter Developer Account

1. Go to https://developer.twitter.com/en/portal/dashboard
2. Sign in with your Twitter/X account
3. Click "Sign up for Free Account" or "Apply for Elevated"
4. Fill out the application:
   - **Use case**: Select "Building tools for Twitter users" or "Exploring the API"
   - **Description**: "Building automated content creation tools for educational/testing purposes"
   - **Will you make Twitter content available to government?**: No (unless applicable)

### Step 2: Create an App

1. After approval, go to https://developer.twitter.com/en/portal/projects-and-apps
2. Click "Create App" or "Add App"
3. Fill in app details:
   - **App name**: "TORQ-Viral-Posts-Generator" (or your choice)
   - **Description**: "AI-powered viral content generator for X/Twitter"
   - **Website**: Your website or GitHub repo URL
   - **Callback URL**: `http://localhost:8899/callback` (for testing)

### Step 3: Get API Keys

1. Go to your app's "Keys and tokens" tab
2. Copy the following credentials:
   - **API Key** (also called Consumer Key)
   - **API Secret** (also called Consumer Secret)
   - Click "Generate" under "Access Token and Secret":
     - **Access Token**
     - **Access Token Secret**
   - Click "Generate" under "Bearer Token":
     - **Bearer Token**

### Step 4: Set Permissions

1. Go to app "Settings" tab
2. Under "App permissions", click "Edit"
3. Select "Read and Write" (required for posting)
4. Save changes

### Step 5: Configure TORQ Console

Add these lines to your `.env` file:

```bash
# Twitter (X) API Configuration
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Optional: Twitter Rate Limiting
TWITTER_RATE_LIMIT_ENABLED=true
TWITTER_MAX_POSTS_PER_HOUR=50
```

## Important Notes

### Rate Limits (Free Tier)

- **Basic Access**: 1,500 tweets per month
- **Posting**: Limited to specific endpoints
- **Reading**: 10,000 requests per month

### Content Guidelines

- Follow Twitter's [Automation Rules](https://help.twitter.com/en/rules-and-policies/twitter-automation)
- Don't spam or post duplicate content
- Include proper disclosures if using AI-generated content
- Respect rate limits and use delays between posts

### Security Best Practices

1. **Never commit credentials to Git**:
   ```bash
   # Verify .env is in .gitignore
   cat .gitignore | grep .env
   ```

2. **Rotate credentials regularly**:
   - Generate new tokens every 90 days
   - Revoke old tokens after rotation

3. **Use environment-specific credentials**:
   - Development: Test account
   - Production: Main account

## Troubleshooting

### Error: "401 Unauthorized"
- **Cause**: Invalid or expired credentials
- **Fix**: Regenerate tokens in Twitter Developer Portal

### Error: "403 Forbidden"
- **Cause**: App doesn't have write permissions
- **Fix**: Enable "Read and Write" in app settings

### Error: "429 Too Many Requests"
- **Cause**: Rate limit exceeded
- **Fix**: Wait for rate limit reset (15 minutes)

### Error: "duplicate content"
- **Cause**: Twitter detects repeated posts
- **Fix**: Add timestamp or variation to posts

## Testing Without Credentials

TORQ Console includes a **demo mode** for testing without real API credentials:

```bash
# In .env file
TWITTER_DEMO_MODE=enabled
```

This will simulate posting without actually connecting to Twitter API.

## Upgrading Access

For production use, consider upgrading to:

- **Basic**: $100/month - 10,000 tweets/month
- **Pro**: $5,000/month - 1M tweets/month
- **Enterprise**: Custom pricing - Unlimited

Apply at: https://developer.twitter.com/en/portal/products

## Alternative: Use Twitter API v2

TORQ Console supports both API v1.1 and v2:

```bash
# In .env file
TWITTER_API_VERSION=v2  # or v1.1 (default)
```

API v2 advantages:
- Better rate limits
- More features
- Modern endpoints

## Resources

- **Developer Portal**: https://developer.twitter.com/en/portal/dashboard
- **API Documentation**: https://developer.twitter.com/en/docs
- **Rate Limits**: https://developer.twitter.com/en/docs/twitter-api/rate-limits
- **Automation Rules**: https://help.twitter.com/en/rules-and-policies/twitter-automation
- **Community Forum**: https://twittercommunity.com/

## Quick Test

After configuration, test your setup:

```bash
# Test credentials
torq-console test-twitter-credentials

# Test posting (demo mode)
torq-console twitter-post "Test post from TORQ Console!" --demo

# Test posting (real)
torq-console twitter-post "Hello from TORQ Console! 🚀" --confirm
```

---

**Need Help?** Open an issue at https://github.com/pilotwaffle/TORQ-CONSOLE/issues
