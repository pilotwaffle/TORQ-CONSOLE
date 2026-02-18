# TORQ Console Operational Guide

This guide covers the hardened operational tools for TORQ Console backend.

## Quick Start

### 1. Preflight Check (Before Starting)

Validate your environment before launching the backend:

```bash
# Basic check (no LLM call)
python -m torq_console.preflight --provider deepseek

# With smoke test (includes real LLM call)
python -m torq_console.preflight --provider deepseek --smoke

# JSON output for CI/CD
python -m torq_console.preflight --provider deepseek --json
```

**What it checks:**
- ✅ Python interpreter (detects WindowsApps stub)
- ✅ .env file loading
- ✅ Required API keys for provider
- ✅ LLM provider initialization
- ✅ Prince Flowers agent loading
- ✅ Optional: Direct LLM smoke test

### 2. Launch Backend (Hardened)

Start the backend with preflight and proper logging:

```bash
# Standard start
python -m torq_console.launch --host 127.0.0.1 --port 8899

# With smoke test before starting
python -m torq_console.launch --host 127.0.0.1 --port 8899 --preflight-smoke

# Debug logging
python -m torq_console.launch --host 127.0.0.1 --port 8899 --log-level debug
```

**Features:**
- Runs preflight before starting
- Enables debug logging
- Shows tracebacks on startup failures
- Works on Windows + production

### 3. Confidence Test (After Starting)

Verify backend health with HTTP tests:

```bash
# Quick test (2+2 prompts)
python -m torq_console.confidence_test --base-url http://127.0.0.1:8899 --direct-n 2 --research-n 2

# Full test (10+10 prompts)
python -m torq_console.confidence_test --base-url http://127.0.0.1:8899

# Custom timeout
python -m torq_console.confidence_test --base-url http://127.0.0.1:8899 --timeout 120
```

**What it validates:**
- ✅ HTTP 200 responses
- ✅ success flag in responses
- ✅ No banned placeholder substrings
- ✅ Latency stats (avg, p95, max)
- ✅ Optional: RSS memory delta

## Configuration

### Environment Variables

Set in `.env` or environment:

```bash
# Provider selection
LLM_PROVIDER=deepseek  # claude, openai, deepseek, ollama, etc.

# API keys (provider-specific)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=...
GLM_API_KEY=...

# Logging
TORQ_LOG_LEVEL=debug  # debug, info, warning, error
PYTHONUNBUFFERED=1    # Always set for production
```

### Provider Configuration

Each provider requires specific environment variables:

| Provider  | Required Variables                 |
|-----------|-------------------------------------|
| claude    | `ANTHROPIC_API_KEY`                 |
| openai    | `OPENAI_API_KEY`                    |
| deepseek  | `DEEPSEEK_API_KEY`                  |
| glm       | `GLM_API_KEY`                       |
| ollama    | `OLLAMA_BASE_URL` (no key required) |

## Troubleshooting

### Preflight Failures

**Error: "Detected disallowed Python interpreter path"**
- You're using the Windows Store Python stub
- Solution: Use your installed Python: `C:\Python312\python.exe` or venv

**Error: "Missing/invalid env for provider 'claude'"**
- Required API keys are missing or look like placeholders
- Solution: Set the required environment variables in `.env`

**Error: "LLMManager could not return provider 'claude'"**
- Provider failed to initialize (check logs for config errors)
- Solution: Verify provider configuration, try a different provider

### Confidence Test Failures

**Error: "Connection refused"**
- Backend is not running
- Solution: Start backend with `python -m torq_console.launch`

**Error: "Banned substring 'placeholder'"**
- Placeholder responses detected
- Solution: Check reasoning engine implementation, ensure LLM is called

### Startup Failures

**Error: "Preflight failed; refusing to start"**
- Preflight checks detected an issue
- Solution: Run `python -m torq_console.preflight` to see details

**Error: Exit code 1 with no output**
- Silent failure due to buffered output or wrong interpreter
- Solution: Set `PYTHONUNBUFFERED=1` and use correct Python path

## CI/CD Integration

### GitHub Actions Example

```yaml
name: TORQ Console Tests

on: [push, pull_request]

jobs:
  preflight:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run preflight
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python -m torq_console.preflight --provider claude --json

  confidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start backend
        run: python -m torq_console.launch &
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Wait for backend
        run: sleep 10
      - name: Run confidence test
        run: python -m torq_console.confidence_test
```

## Performance Baselines

Based on confidence test results:

| Mode      | Avg Latency | P95 Latency | Max Latency |
|-----------|-------------|-------------|-------------|
| Direct    | ~0.035s     | ~0.022s     | ~0.12s      |
| Research  | ~0.012s     | ~0.015s     | ~0.026s     |

*Results from 5+5 prompts on local machine*

## Maintenance

### Regular Checks

Run these commands regularly to ensure system health:

```bash
# Weekly health check
python -m torq_console.preflight --provider deepseek --smoke
python -m torq_console.confidence_test

# Before deploying
python -m torq_console.preflight --json | jq '.ok'
```

### Log Monitoring

Key log patterns to watch:

- `LLMManager could not return provider` → Provider config issue
- `Failed to load Prince Flowers agent` → Agent initialization issue
- `Banned substring 'placeholder'` → Placeholder response bug
- `Connection refused` → Backend not running

## Support

For issues or questions:

1. Check preflight output: `python -m torq_console.preflight --json`
2. Check backend logs in console output
3. Run confidence test: `python -m torq_console.confidence_test`
4. Review this guide's troubleshooting section
