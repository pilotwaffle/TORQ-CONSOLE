# Prince Flowers Enhanced with Claude Sonnet 4.5 + DeepSeek

## 🎯 Configuration Complete!

Prince Flowers Enhanced Agent has been upgraded to use:
- **Claude Sonnet 4.5** - For advanced reasoning, coding, and app building
- **DeepSeek API** - For fast web searches and quick responses
- **Enhanced Memory** - Supabase + pgvector for RAG capabilities

---

## 🔧 Setup Steps

### 1. Add Your Anthropic API Key

Edit `E:\TORQ-CONSOLE\.env` and replace:
```bash
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY_HERE
```

With your actual Anthropic API key from https://console.anthropic.com/

### 2. Restart TORQ Console

Kill the current instance and restart:
```bash
# Windows
taskkill //F //IM python.exe
cd E:\TORQ-CONSOLE
python start_torq_with_fixes.py
```

### 3. Verify Setup

Open http://127.0.0.1:8899 and try:
```
"search web for latest AI news since October 2024"
```

---

## 🚀 What's New

### Automatic Provider Selection

Prince Flowers now intelligently routes queries:

**Claude Sonnet 4.5 is used for:**
- ✅ Code generation and debugging
- ✅ Complex reasoning tasks
- ✅ App scaffolding and architecture
- ✅ Technical explanations
- ✅ Long-form content generation
- ✅ Extended thinking (up to 10,000 thinking tokens)

**DeepSeek is used for:**
- ⚡ Quick searches
- ⚡ Simple questions
- ⚡ Fast information retrieval
- ⚡ General queries

### Enhanced Capabilities

**1. Advanced Code Generation**
```
"Build me a React e-commerce app with Stripe payments and PostgreSQL"
```

Claude will:
- Design the architecture
- Generate all components
- Create API endpoints
- Add database schemas
- Include tests and documentation

**2. Extended Thinking**
```
"Think deeply about how to optimize this database schema for performance"
```

Claude uses up to 10,000 thinking tokens to:
- Explore multiple approaches
- Validate reasoning
- Consider edge cases
- Provide comprehensive analysis

**3. Web Search + Analysis**
```
"search web for latest developments in AI and analyze their impact"
```

DeepSeek performs the search, then Claude analyzes the results with deep reasoning.

---

## 📊 Provider Comparison

| Feature | Claude Sonnet 4.5 | DeepSeek |
|---------|-------------------|----------|
| **Speed** | Moderate (2-5s) | Fast (<1s) |
| **Quality** | Excellent | Good |
| **Reasoning** | Advanced (extended thinking) | Basic |
| **Coding** | Excellent | Good |
| **Cost** | Higher | Lower |
| **Use Case** | Complex tasks, coding, building | Quick searches, simple queries |

---

## 🎨 Example Queries

### For Claude (Coding/Building):
```
"Create a Vue 3 component for a product carousel with lazy loading"

"Design a microservices architecture for a social media platform"

"Refactor this code to use async/await and add comprehensive error handling"

"Build a Next.js blog with MDX support and PostgreSQL backend"
```

### For DeepSeek (Fast Search):
```
"search for latest JavaScript frameworks 2024"

"what's trending in AI right now"

"find recent TypeScript best practices"
```

### Combined (Search + Analysis):
```
"search web for AI news and analyze the top 3 developments"

"find latest React patterns and explain which ones I should use"
```

---

## ⚙️ Configuration Options

### Change Default Model

Edit `.env`:
```bash
# Use a different Claude model
CLAUDE_MODEL=claude-sonnet-4-20250514  # Default
# or
CLAUDE_MODEL=claude-opus-4-20250514    # More powerful
```

### Adjust Thinking Budget

Modify `torq_console/llm/providers/claude.py`:
```python
thinking_budget=10000  # Default
thinking_budget=20000  # More thinking for complex tasks
```

### Provider Routing

Edit `torq_console/llm/manager.py`:
```python
self.default_provider = 'claude'      # Use Claude by default
self.search_provider = 'deepseek'     # Use DeepSeek for searches
```

---

## 🔍 How Routing Works

### Automatic Detection

Prince Flowers detects query type and routes to the best provider:

**Coding/Building Keywords → Claude:**
- "create", "build", "generate", "code", "app", "component"
- "refactor", "optimize", "design", "architecture"

**Search Keywords → DeepSeek:**
- "search", "find", "latest", "news", "what is", "current"

**Complex Reasoning → Claude:**
- "analyze", "think about", "explain", "compare", "evaluate"

### Manual Override

Force a specific provider:
```
"use claude: explain quantum computing"
"use deepseek: quick search for Python tutorials"
```

---

## 💾 Enhanced Memory Integration

All interactions are automatically stored in Supabase with:
- User query
- Provider used (Claude or DeepSeek)
- Response content
- Tools/features used
- Success metrics

**RAG Retrieval:**
When you ask a follow-up question, Prince Flowers retrieves relevant context from previous interactions using semantic search.

---

## 🎯 Performance Metrics

### Expected Response Times

| Query Type | Provider | Time | Quality |
|------------|----------|------|---------|
| Simple search | DeepSeek | 0.5-1s | Good |
| Code generation | Claude | 2-4s | Excellent |
| Complex reasoning | Claude (extended) | 4-8s | Outstanding |
| App scaffolding | Claude | 3-6s | Excellent |

### Token Usage

**Claude Sonnet 4.5:**
- Input: ~$3/million tokens
- Output: ~$15/million tokens
- Thinking: Included in output cost

**DeepSeek:**
- Much lower cost
- Good for high-volume searches

---

## 📚 Advanced Features

### 1. Multi-Step App Building

```
"Build me a full-stack SaaS application with:
- Next.js frontend with TypeScript
- Express backend API
- PostgreSQL database
- Stripe payments
- User authentication
- Docker containerization"
```

Claude will:
1. Design the architecture
2. Create project structure
3. Generate all components
4. Setup database schemas
5. Configure Docker
6. Add authentication
7. Integrate Stripe
8. Create comprehensive tests

### 2. Code Review & Optimization

```
"Review this code and suggest improvements:
[paste code]"
```

Claude provides:
- Security analysis
- Performance optimization
- Best practices
- Refactoring suggestions
- Test coverage recommendations

### 3. Learning & Explanation

```
"Explain microservices architecture with a practical example
and compare it to monolithic architecture"
```

Claude uses extended thinking to:
- Explore different perspectives
- Provide comprehensive examples
- Compare trade-offs
- Give practical recommendations

---

## 🐛 Troubleshooting

### Claude Not Working

**Issue:** "Claude provider not configured"

**Fix:**
1. Check `.env` has valid `ANTHROPIC_API_KEY`
2. Restart TORQ Console
3. Check logs: `tail -f torq_console.log`

### Queries Going to Wrong Provider

**Issue:** Searches using Claude instead of DeepSeek

**Fix:** Add "search" keyword explicitly:
```
"search web for AI news"  # Will use DeepSeek
```

### Slow Responses

**Issue:** All queries taking 4-5 seconds

**Solution:** This is normal for Claude with extended thinking. For faster responses:
```
"quick search: [your query]"  # Forces DeepSeek
```

Or disable extended thinking in `claude.py`:
```python
thinking=None  # Disable extended thinking
```

---

## 🎉 You're All Set!

Prince Flowers Enhanced is now powered by:
✅ Claude Sonnet 4.5 for world-class coding and reasoning
✅ DeepSeek for lightning-fast searches
✅ Enhanced memory with RAG capabilities
✅ Direct web UI routing to Prince Flowers

**Next Steps:**
1. Add your Anthropic API key to `.env`
2. Restart TORQ Console
3. Open http://127.0.0.1:8899
4. Start building amazing apps!

**Try it out:**
```
"search web for latest AI developments since October 2024"
"build me a React portfolio website with dark mode and animations"
"explain how to implement OAuth2 with examples"
```

---

**Enjoy your supercharged Prince Flowers! 🌸**
