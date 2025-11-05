# Viral X Posts App - Usage Examples

## Quick Start (Demo Mode - No Credentials Needed!)

### Example 1: Generate a Viral Post

```bash
# Generate a viral post about AI (demo mode)
python viral_x_posts_app.py --demo --mode=generate --topic="AI in 2025"
```

**Output**:
```
🚀 Viral X Posts Generator - TORQ Console
================================================================================
📢 Running in DEMO MODE - Posts will not be published
================================================================================

📝 Generating viral post about: AI in 2025

--------------------------------------------------------------------------------
Generated Content:
--------------------------------------------------------------------------------
💡 Most people don't realize that AI in 2025 isn't about what you think it is

#AI #MachineLearning #Innovation
--------------------------------------------------------------------------------
Style: insight
Characters: 112/280
Predicted Engagement: 78.0%
--------------------------------------------------------------------------------
```

### Example 2: Generate and Preview Different Styles

```bash
# Question style
python viral_x_posts_app.py --demo --mode=generate --topic="Productivity" --style=question

# List style
python viral_x_posts_app.py --demo --mode=generate --topic="Remote Work" --style=list

# Story style
python viral_x_posts_app.py --demo --mode=generate --topic="Career Growth" --style=story
```

### Example 3: Generate a Thread

```bash
# Generate a 5-tweet thread about AI trends
python viral_x_posts_app.py --demo --mode=thread --topic="AI Trends 2025" --num-tweets=5
```

**Output**:
```
🧵 Generating thread about: AI Trends 2025
Number of tweets: 5

--------------------------------------------------------------------------------
Thread Preview:
--------------------------------------------------------------------------------

Tweet 1/5:
🧵 Thread: AI Trends 2025

What if AI Trends 2025?

#AI #MachineLearning #Innovation

(1/5)
Characters: 94

Tweet 2/5:
💡 Most people don't realize that the real value of AI Trends 2025 is hidden in plain sight

(2/5)
Characters: 107

Tweet 3/5:
After learning AI Trends 2025, I learned that success with AI Trends 2025 requires this counterintuitive approach

(3/5)
Characters: 129

Tweet 4/5:
🧵 5 things about AI Trends 2025 that changed my perspective:

(4/5)
Characters: 70

Tweet 5/5:
If you found this thread valuable:

✅ Follow for more insights on AI Trends 2025
💬 Share your thoughts below
🔁 Retweet to help others

(5/5)
Characters: 143
--------------------------------------------------------------------------------
```

### Example 4: Save Generated Content

```bash
# Generate and save to file
python viral_x_posts_app.py --demo --mode=generate --topic="Machine Learning" --output=my_post.json
```

**Creates `my_post.json`**:
```json
{
  "content": "💡 Most people don't realize that Machine Learning works differently than expected\n\n#AI #MachineLearning #Tech",
  "hashtags": ["#AI", "#MachineLearning", "#Tech"],
  "style": "insight",
  "engagement_score": 0.78,
  "char_count": 108,
  "generated_at": "2025-01-05T20:45:00"
}
```

## Real Twitter Posting (Requires API Credentials)

### Prerequisites

1. Get Twitter API credentials (see `TWITTER_API_SETUP_GUIDE.md`)
2. Add to `.env` file:
   ```bash
   TWITTER_API_KEY=your_key
   TWITTER_API_SECRET=your_secret
   TWITTER_ACCESS_TOKEN=your_token
   TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
   ```
3. Install tweepy: `pip install tweepy`

### Example 5: Post Custom Content

```bash
# Post custom content to Twitter
python viral_x_posts_app.py --mode=post --content="Just launched my new AI project! 🚀 Check it out! #AI #Tech"
```

### Example 6: Generate and Post

```bash
# Generate viral content about a topic and post it
python viral_x_posts_app.py --mode=post --topic="Blockchain" --category=tech
```

### Example 7: Post a Thread

```bash
# Generate and post a thread
python viral_x_posts_app.py --mode=thread --topic="Python Tips for Developers" --num-tweets=7
```

**Interactive prompt**:
```
Post this thread? (y/n): y
```

## Advanced Usage

### Example 8: Custom Category Hashtags

```bash
# Business category
python viral_x_posts_app.py --demo --mode=generate --topic="Leadership" --category=business

# Motivation category
python viral_x_posts_app.py --demo --mode=generate --topic="Goals" --category=motivation

# Learning category
python viral_x_posts_app.py --demo --mode=generate --topic="Study Techniques" --category=learning
```

### Example 9: Different Post Styles

```bash
# Question hook (high engagement)
python viral_x_posts_app.py --demo --topic="Remote Work" --style=question

# Numbered list (shareable)
python viral_x_posts_app.py --demo --topic="Productivity Hacks" --style=list

# Personal story (relatable)
python viral_x_posts_app.py --demo --topic="Career Change" --style=story

# Announcement (news)
python viral_x_posts_app.py --demo --topic="New Product Launch" --style=announcement

# Insight (thought leadership)
python viral_x_posts_app.py --demo --topic="Future of AI" --style=insight
```

### Example 10: Batch Generation

```bash
# Generate multiple posts and save
for topic in "AI" "Blockchain" "Web3" "Cloud Computing" "Cybersecurity"; do
    python viral_x_posts_app.py --demo --mode=generate --topic="$topic" --output="${topic}_post.json"
done
```

## Integration with TORQ Console

### Use from TORQ Console CLI

```bash
# Through TORQ Console
torq-console run viral_x_posts_app.py --demo --topic="Your Topic"
```

### Use from Python

```python
from viral_x_posts_app import ViralContentGenerator

# Create generator
generator = ViralContentGenerator(demo_mode=True)

# Generate single post
post = generator.generate_viral_post("AI Trends", style="question", category="tech")
print(post.content)
print(f"Engagement Score: {post.engagement_score:.1%}")

# Generate thread
thread = generator.generate_thread("Python Tips", num_tweets=5, category="learning")
for i, tweet in enumerate(thread, 1):
    print(f"\nTweet {i}:")
    print(tweet.content)

# Post to Twitter (if credentials configured)
result = generator.post_to_twitter(post.content)
if result['success']:
    print(f"Posted! URL: {result.get('url')}")
```

## Content Categories & Hashtags

### Available Categories

1. **tech**: `#Tech #AI #Innovation #StartUp #FutureOfWork`
2. **business**: `#Business #Entrepreneur #Growth #Success #Leadership`
3. **learning**: `#Learning #Growth #SelfImprovement #Knowledge #Wisdom`
4. **motivation**: `#Motivation #Inspiration #Success #Goals #Mindset`
5. **ai**: `#AI #MachineLearning #ChatGPT #ArtificialIntelligence #ML`

### Post Styles

1. **question**: Engages audience with thought-provoking questions
2. **list**: Numbered insights (e.g., "5 things about X")
3. **story**: Personal narrative or experience
4. **announcement**: News or product launches
5. **insight**: Thought leadership and wisdom

## Tips for Maximum Virality

### 1. Use Questions
```bash
python viral_x_posts_app.py --demo --topic="AI Ethics" --style=question
```
Questions increase engagement by 40%

### 2. Create Threads
```bash
python viral_x_posts_app.py --demo --mode=thread --topic="Startup Lessons" --num-tweets=7
```
Threads get 3x more engagement than single posts

### 3. Optimize Hashtags
- Use 3 hashtags (sweet spot)
- Mix popular and niche tags
- Place hashtags at the end

### 4. Post Timing
- Tech audience: 9 AM - 12 PM EST
- Business: 8 AM - 10 AM EST
- General: 12 PM - 3 PM EST

### 5. Content Length
- Aim for 200-250 characters
- Leave room for engagement
- Use emojis strategically (💡🚀🧵✅)

## Troubleshooting

### Issue: "tweepy not installed"
```bash
pip install tweepy
```

### Issue: "Missing Twitter API credentials"
1. See `TWITTER_API_SETUP_GUIDE.md`
2. Or run with `--demo` flag

### Issue: "401 Unauthorized"
- Regenerate Twitter API tokens
- Verify credentials in `.env`

### Issue: "429 Too Many Requests"
- Hit rate limit (wait 15 minutes)
- Or use `--demo` mode for testing

## Examples Output

### Generated Question Post
```
What if AI Trends 2025 will change everything in 2025?

#AI #Innovation #FutureOfWork

Style: question
Characters: 84/280
Predicted Engagement: 73.0%
```

### Generated List Post
```
🧵 5 things about Machine Learning that changed my perspective:

#AI #MachineLearning #Tech

Style: list
Characters: 93/280
Predicted Engagement: 83.0%
```

### Generated Story Post
```
A year ago, I didn't know Python. Today, I build AI applications. Here's what changed:

#Learning #Growth #AI

Style: story
Characters: 115/280
Predicted Engagement: 81.0%
```

## Automated Scheduling

### Using Cron (Linux/Mac)

```bash
# Post every day at 9 AM
0 9 * * * cd /path/to/TORQ-CONSOLE && python viral_x_posts_app.py --mode=post --topic="Daily AI Tip"
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, 9:00 AM)
4. Action: Start a program
5. Program: `python`
6. Arguments: `E:\TORQ-CONSOLE\viral_x_posts_app.py --mode=post --topic="Daily Tip"`

## Best Practices

1. **Test in Demo Mode First**
   ```bash
   python viral_x_posts_app.py --demo --mode=thread --topic="Your Topic"
   ```

2. **Save Generated Content**
   ```bash
   python viral_x_posts_app.py --demo --output=posts.json
   ```

3. **Review Before Posting**
   - Always preview content
   - Check character count
   - Verify hashtags are relevant

4. **Respect Rate Limits**
   - Free tier: 1,500 posts/month
   - Add delays between posts
   - Monitor usage

5. **Follow Twitter Guidelines**
   - No spam or duplicates
   - Proper disclosures for AI content
   - Respect intellectual property

## Resources

- **Setup Guide**: `TWITTER_API_SETUP_GUIDE.md`
- **App Code**: `viral_x_posts_app.py`
- **Twitter Developer**: https://developer.twitter.com
- **Tweepy Docs**: https://docs.tweepy.org

---

**Need Help?** Open an issue at https://github.com/pilotwaffle/TORQ-CONSOLE/issues
