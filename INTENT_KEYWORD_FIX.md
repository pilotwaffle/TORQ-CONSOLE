# 🔧 Intent Detection Keyword Fix

## Problem Discovered:

User query **"Latest AI news"** was generating TypeScript code instead of using WebSearch.

## Root Cause Analysis:

### Scoring Algorithm:
```python
score = (keyword_matches / total_keywords) * 0.6  # Keywords = 60% weight
      + (context_matches / total_contexts) * 0.4  # Context = 40% weight
```

### Before Fix:

**Query:** `"Latest AI news"`

**Pattern:** `research_general`
```python
keywords = ['research', 'find', 'search', 'look up', 'information about', 'tell me about']
# Matches: 0 ("latest" and "news" NOT in keywords)
# Score: 0 * 0.6 = 0.0

context_markers = ['web for', 'online', 'internet', 'latest', 'current', 'recent']
# Matches: 1 ("latest")
# Score: (1/6) * 0.4 = 0.0667

Total: 0.0667 * 0.85 (confidence) = 0.0567
```

**Result:** `0.0567 < 0.1 threshold` → **REJECTED** → Falls back to "general" → BUILD MODE ❌

---

## The Fix:

Added high-value research keywords to the **keywords** list (60% weight):

```python
'research_general': IntentPattern(
    keywords=[
        # Original
        'research', 'find', 'search', 'look up', 'information about', 'tell me about',
        # ✅ ADDED (moved from context_markers or new)
        'latest', 'top', 'trending', 'best', 'new', 'show', 'get', 'news', 'article', 'what are', 'list'
    ],
    context_markers=['web for', 'online', 'internet', 'current', 'recent', 'today', 'this week', 'this month'],
    ...
)
```

### After Fix:

**Query:** `"Latest AI news"`

```python
keywords = [..., 'latest', 'news', ...]  # 17 keywords total
# Matches: 2 ("latest", "news")
# Score: (2/17) * 0.6 = 0.0706

context_markers = [...]  # 8 markers
# Matches: 0 (no additional matches)
# Score: 0 * 0.4 = 0.0

Total: 0.0706 * 0.85 (confidence) = 0.0600
```

**Wait, that's still below 0.1!** Let me recalculate...

Actually, with both keywords matching:
```python
keywords = ['research', 'find', 'search', ..., 'latest', 'news', ...]  # 17 total
# Matches in "Latest AI news": 'latest', 'news' = 2 matches
# Score: (2/17) * 0.6 = 0.0706

context_markers = ['web for', 'online', ..., 'today']  # 8 total
# Matches in "Latest AI news": none additional
# Score: 0 * 0.4 = 0.0

Total: 0.0706 * 0.85 = 0.0600
```

Hmm, still `0.0600 < 0.1`. But wait - let me check if "latest" is also in context_markers...

Actually, I removed "latest" from context_markers since it's now in keywords. Let me verify the calculation assumes no duplication:

```python
keywords matching: "latest", "news" = 2/17 = 0.1176
Score: 0.1176 * 0.6 = 0.0706

context_markers matching: nothing new = 0/8 = 0
Score: 0 * 0.4 = 0.0

Total: 0.0706 * 0.85 (confidence) = 0.06

# Still below 0.1!
```

**Hmm, we need to either:**
1. Lower the threshold further (0.05?)
2. Add MORE keywords
3. Increase the weight

Let me check what "Latest AI news" should actually score with this fix...

Actually, let me reconsider. If "AI" doesn't match any keyword, then:
- "Latest" matches → 1 keyword match
- "news" matches → 1 keyword match
- "AI" doesn't match anything

So 2 out of 17 keywords = 0.1176 * 0.6 = 0.0706
0.0706 * 0.85 = 0.0600

**This is STILL below 0.1 threshold!**

I need to ALSO lower the threshold to 0.05, OR make the pattern match better.

Let me think... Actually, the real issue is the threshold is too high even at 0.1. Let me check what "Search for the latest Article news" scored (which DID work).

"Search for the latest Article news" has:
- "search" → keyword match
- "latest" → keyword match (now)
- "news" → keyword match (now)

That's 3 out of 17 = 0.1765 * 0.6 = 0.1059
0.1059 * 0.85 = 0.0900

**Still below 0.1!** Unless... wait, maybe context_markers also matched?

Let me recalculate more carefully. The query was "Search for the latest Article news 11/11/25":
- Keywords matching: "search", "latest", "news" = 3/17 = 0.1765
- Context matching: maybe "latest"? But that's now in keywords, not context...

Actually I removed "latest" from context_markers. So:
- keywords: 0.1765 * 0.6 = 0.1059
- context: 0 * 0.4 = 0.0
- Total: 0.1059 * 0.85 = 0.0900

**That's BELOW 0.1!** But the user said the first query worked...

Wait, maybe the deployment doesn't have my 0.1 threshold change yet? Or maybe there's another pattern matching?

Let me re-read the user's feedback. They said "Search for the latest Article news 11/11/25" at 6:13 AM WORKED. But the logs I saw earlier showed it was from when they tested at 5:42 AM and it failed.

Actually, I think the threshold needs to be even LOWER, like 0.05. Or we need to add even MORE keywords.

Let me add more keywords and also check if we should lower threshold to 0.05.
