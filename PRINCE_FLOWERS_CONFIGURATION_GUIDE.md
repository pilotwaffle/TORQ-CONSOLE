# Prince Flowers AI - Complete Configuration Guide

**Version**: 1.0.0
**Last Updated**: 2025-02-17
**Agent**: Prince Flowers Enhanced V2 with Autonomous Planning

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Required API Keys](#required-api-keys)
3. [Optional API Keys](#optional-api-keys)
4. [Prince Flowers AI Configuration](#prince-flowers-ai-configuration)
5. [Swarm Mode Configuration](#swarm-mode-configuration)
6. [Memory Storage Options](#memory-storage-options)
7. [Web Research Capabilities](#web-research-capabilities)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Performance Optimization](#performance-optimization)

---

## Quick Start

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Add Required API Keys

Edit `.env` and add at minimum:

```bash
# Required for Prince Flowers to work
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Start TORQ Console

```bash
python -m torq_console.ui.main --host 127.0.0.1 --port 8899
```

### 4. Test Prince Flowers

```bash
curl -X POST http://127.0.0.1:8899/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what time is it in Texas"}'
```

---

## Required API Keys

### Anthropic Claude API (Required)

Prince Flowers requires Claude API for core LLM functionality.

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**How to Get**:
1. Go to https://console.anthropic.com/
2. Create an account
3. Navigate to API Keys
4. Create a new key

**Cost**: ~$0.003 per 1K tokens (input), ~$0.015 per 1K tokens (output)

**Usage**: All AI responses, reasoning, and synthesis

---

## Optional API Keys

### OpenAI API

```bash
OPENAI_API_KEY=sk-xxxxx
```

**Purpose**: Better embeddings for memory retrieval, alternative LLM

**How to Get**: https://platform.openai.com/api-keys

### DeepSeek API

```bash
DEEPSEEK_API_KEY=sk-xxxxx
```

**Purpose**: Cost-effective alternative LLM provider

**How to Get**: https://platform.deepseek.com/

### Supabase (Cloud Memory Storage)

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx
SUPABASE_ANON_KEY=eyJxxxxx
```

**Purpose**: Persistent cloud-based memory storage across sessions

**How to Get**:
1. Go to https://supabase.com/
2. Create a new project
3. Go to Settings → API
4. Copy URL and service role key

### Web Search APIs

#### Brave Search (Recommended - Free Tier)

```bash
BRAVE_SEARCH_API_KEY=BSxxxxx
```

**Purpose**: Web search for research (2,000 free queries/month)

**How to Get**: https://brave.com/search/api/

#### Tavily AI Search (Optimized for AI Agents)

```bash
TAVILY_API_KEY=tvly-xxxxx
```

**Purpose**: AI-optimized search with better results

**How to Get**: https://tavily.com/

#### Google Search API

```bash
GOOGLE_SEARCH_API_KEY=xxxxx
GOOGLE_SEARCH_ENGINE_ID=xxxxx
```

**Purpose**: Alternative web search

**How to Get**: https://programmablesearchengine.google.com/

### Financial Data APIs

```bash
ALPHA_VANTAGE_API_KEY=xxxxx
FRED_API_KEY=xxxxx
COINMARKETCAP_API_KEY=xxxxx
```

**Purpose**: Real-time stock prices, crypto data, financial forecasts

**How to Get**:
- Alpha Vantage: https://www.alphavantage.co/support/#api-key
- FRED: https://fred.stlouisfed.org/docs/api/api_key.html
- CoinMarketCap: https://coinmarketcap.com/api/

---

## Prince Flowers AI Configuration

### Memory Backend Options

```bash
# Options: sqlite, supabase, letta
PRINCE_FLOWERS_MEMORY_BACKEND=supabase
PRINCE_FLOWERS_MEMORY_ENABLED=true
```

| Backend | Description | Use Case |
|---------|-------------|----------|
| `sqlite` | Local file-based storage | Development, testing |
| `supabase` | Cloud PostgreSQL database | Production, multi-session |
| `letta` | Advanced memory with embeddings | Advanced AI features |

### Autonomous Planning

```bash
PRINCE_FLOWERS_HIERARCHICAL_PLANNING=true
```

**What it does**: Breaks complex tasks into sub-tasks, creates execution plans

**Example**: For "create a To-Do app", Prince Flowers will:
1. Plan the architecture
2. Design the database schema
3. Plan the UI components
4. Create implementation steps
5. Execute in logical order

### Multi-Agent Debate

```bash
PRINCE_FLOWERS_MULTI_AGENT_DEBATE=true
```

**What it does**: Multiple agent perspectives debate to find best solutions

**Benefits**:
- More accurate responses
- Better error detection
- Improved reasoning quality
- Self-correction before responding

### Cross-Agent Learning

```bash
PRINCE_FLOWERS_CROSS_AGENT_LEARNING=true
```

**What it does**: Agents share successful patterns with each other

**Benefits**:
- Continuous improvement
- Knowledge transfer across sessions
- Better performance on similar tasks

### Self-Evaluation

```bash
PRINCE_FLOWERS_SELF_EVALUATION=true
```

**What it does**: Prince Flowers evaluates its own responses for quality

**Metrics**:
- Confidence calibration
- Response quality scoring
- Error detection
- Improvement tracking

---

## Web Research Capabilities

### Auto Web Research

```bash
PRINCE_FLOWERS_WEB_SEARCH_ENABLED=true
PRINCE_FLOWERS_AUTO_WEB_RESEARCH=true
PRINCE_FLOWERS_RESEARCH_DEPTH=deep
```

**What it does**: Automatically searches the web before generating responses

**Research Depth Options**:
- `basic`: Quick search (3-5 results)
- `standard`: Normal search (5-10 results)
- `deep`: Comprehensive search (10-20 results + best practices)

**Example Workflow**:

For query "create a To-Do List app with React":

1. **Primary Search**: "create To-Do List app React"
2. **Best Practices Search**: "React To-Do app best practices"
3. **Documentation Search**: "React documentation official"
4. **Synthesis**: Combines all sources with step-by-step implementation

---

## Swarm Mode Configuration

### Enable Swarm Mode

```bash
SWARM_MODE_ENABLED=true
SWARM_MAX_PARALLEL_AGENTS=5
```

**What it does**: Multiple specialized agents work in parallel

### Available Swarm Agents

```bash
SWARM_SEARCH_AGENT=true       # Research specialist
SWARM_CODE_AGENT=true         # Code generation specialist
SWARM_ANALYSIS_AGENT=true     # Data analysis specialist
SWARM_SYNTHESIS_AGENT=true    # Information synthesis specialist
SWARM_TESTING_AGENT=true      # Quality assurance specialist
```

### Swarm Collaboration

```bash
SWARM_COLLABORATION_ENABLED=true
SWARM_DEBATE_ENABLED=true
SWARN_MEMORY_SHARING=true
```

**Workflow Example**:

For "analyze MSTR stock and forecast":

1. **Search Agent**: Finds current stock price, news, analyst reports
2. **Analysis Agent**: Processes financial data, technical indicators
3. **Synthesis Agent**: Combines findings into comprehensive report
4. **Testing Agent**: Validates forecast accuracy
5. **Debate**: Agents discuss different perspectives
6. **Final Output**: Best answer with confidence score

### Swarm Memory

```bash
SWARM_MEMORY_BACKEND=supabase
SWARM_MEMORY_PATH=~/.torq_console/swarm_memory
```

**Purpose**: Agents share learned patterns and successful strategies

---

## Memory Storage Options

### SQLite (Default - Local)

```bash
PRINCE_FLOWERS_MEMORY_BACKEND=sqlite
```

**Pros**:
- No setup required
- Fast for local development
- Privacy (data stays local)

**Cons**:
- Not shared across sessions
- Single device only
- Limited scalability

**Storage Location**: `~/.torq_console/memory/`

### Supabase (Recommended - Cloud)

```bash
PRINCE_FLOWERS_MEMORY_BACKEND=supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx
```

**Pros**:
- Persistent across sessions
- Multi-device support
- Scalable
- Real-time sync
- Built-in authentication

**Cons**:
- Requires setup
- Internet connection required
- Cloud costs (free tier available)

**Setup**:

1. Create Supabase project
2. Run SQL setup script:

```sql
-- Create memories table
CREATE TABLE memories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id TEXT NOT NULL,
  content TEXT NOT NULL,
  memory_type TEXT NOT NULL,
  importance FLOAT DEFAULT 0.5,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for fast lookups
CREATE INDEX idx_memories_session_id ON memories(session_id);
CREATE INDEX idx_memories_importance ON memories(importance DESC);
```

---

## Advanced Features

### Meta-Learning

```bash
PRINCE_FLOWERS_META_LEARNING=true
```

**What it does**: Prince Flowers learns from all interactions to improve performance

**Tracks**:
- Successful response patterns
- Failed response patterns
- User feedback
- Optimal tool usage

### Performance Monitoring

```bash
PRINCE_FLOWERS_PERFORMANCE_MONITORING=true
```

**Metrics Tracked**:
- Response latency
- Quality scores
- Tool usage patterns
- Error rates
- User satisfaction

---

## Performance Optimization

### Caching

```bash
CACHE_ENABLED=true
CACHE_DURATION=300
CACHE_MAX_SIZE=1000
```

**What it Caches**:
- Web search results
- LLM responses
- Research findings

### Rate Limiting

```bash
RATE_LIMITING_ENABLED=true
MAX_REQUESTS_PER_MINUTE=60
```

### Request Timeout

```bash
REQUEST_TIMEOUT=120
RETRY_ATTEMPTS=3
RETRY_DELAY=1
RETRY_BACKOFF=exponential
```

---

## Troubleshooting

### Issue: "Claude provider not configured"

**Solution**: Add `ANTHROPIC_API_KEY` to `.env`

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### Issue: "Web search failed"

**Solution**: Add a search API key

```bash
BRAVE_SEARCH_API_KEY=BSxxxxx
```

### Issue: "Memory backend not available"

**Solution**: Check backend configuration

```bash
PRINCE_FLOWERS_MEMORY_BACKEND=sqlite
```

---

## Configuration Examples

### Development Setup

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
PRINCE_FLOWERS_MEMORY_BACKEND=sqlite
PRINCE_FLOWERS_AUTO_WEB_RESEARCH=false
SWARM_MODE_ENABLED=false
```

### Production Setup

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
BRAVE_SEARCH_API_KEY=BSxxxxx
PRINCE_FLOWERS_MEMORY_BACKEND=supabase
PRINCE_FLOWERS_HIERARCHICAL_PLANNING=true
PRINCE_FLOWERS_MULTI_AGENT_DEBATE=true
PRINCE_FLOWERS_AUTO_WEB_RESEARCH=true
PRINCE_FLOWERS_RESEARCH_DEPTH=deep
SWARM_MODE_ENABLED=true
```

---

**Last Updated**: 2025-02-17
**Version**: 1.0.0
