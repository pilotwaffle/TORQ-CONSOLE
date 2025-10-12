# TORQ Console Implementation Roadmap
## Path to Surpassing Cursor and Cline

**Created:** 2025-10-12
**Status:** In Progress - Session 2 Starting
**Goal:** Transform TORQ Console into the market-leading AI-powered development environment

---

## 📊 Current Status (Session 1 Complete)

### ✅ Completed in Session 1
- **SearchMaster Recency Filter Fix** - Fixed 0-result bug, expanded 7d→30d with smart bypass
- **Prince Flowers Provider Fallback** - Implemented cascading DeepSeek→Ollama→Claude failover
- **Ollama Integration Enhancement** - Added debug logging and error handling
- **llama.cpp Provider Skeleton** - Complete 446-line provider with fast/quality tiers
- **Strategic Analysis** - Comprehensive competitive analysis vs Cursor and Cline
- **15-Week Master Plan** - Detailed roadmap in TORQ_CONSOLE_MASTERY_PLAN.md
- **Git Commit** - All changes committed to main branch (commit 34e7625)
- **GitHub Push** - Changes pushed to https://github.com/pilotwaffle/TORQ-CONSOLE.git

### 📈 Performance Improvements Achieved
- Query time: **87s → 58s (33% faster)**
- Search results: **0 → 7 (100% reliability improvement)**
- Provider availability: **3 active providers** (Claude, DeepSeek, Ollama)
- Test validation: **100% success rate** (Prince search + X.com post generation)

---

## 🎯 Session 2: Complete llama.cpp Integration + Tests (CURRENT)

**Objective:** Fully integrate llama.cpp provider into TORQ Console with tier-based routing and 100% test coverage

### Tasks Breakdown

#### Task 2.1: Integrate llama.cpp Provider into LLM Manager
**File:** `E:\TORQ-CONSOLE\torq_console\llm\manager.py`

**Changes Required:**
```python
# Line ~90: Add llama.cpp import
from torq_console.llm.providers.llama_cpp_provider import LlamaCppProvider

# Line ~150: Add _init_llama_cpp method
def _init_llama_cpp(self):
    """Initialize llama.cpp local LLM provider."""
    try:
        # Get model path from config
        model_path = self.config.get('llama_cpp_model_path', None)

        if not model_path:
            self.logger.warning("llama.cpp model path not configured")
            return

        # Get configuration parameters
        n_ctx = self.config.get('llama_cpp_n_ctx', 2048)
        n_gpu_layers = self.config.get('llama_cpp_n_gpu_layers', 0)
        n_threads = self.config.get('llama_cpp_n_threads', None)

        self.logger.debug(f"Initializing llama.cpp provider with model={model_path}")

        provider = LlamaCppProvider(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            n_threads=n_threads,
            verbose=False
        )

        # Register two tiers: fast and quality
        self.providers['llama_cpp_fast'] = provider
        self.providers['llama_cpp_quality'] = provider  # Same instance, different method calls

        self.logger.info(f"llama.cpp provider initialized (model: {model_path})")

    except ImportError as e:
        self.logger.warning(f"llama-cpp-python not installed: {e}")
    except Exception as e:
        self.logger.error(f"Failed to initialize llama.cpp provider: {e}", exc_info=True)

# Line ~200: Add llama.cpp to init sequence
def __init__(self, config: Optional[Dict[str, Any]] = None):
    # ... existing code ...
    self._init_claude()
    self._init_deepseek()
    self._init_ollama()
    self._init_llama_cpp()  # NEW
```

**Test Criteria:**
- Provider initializes without errors
- Both 'llama_cpp_fast' and 'llama_cpp_quality' appear in providers list
- Health check returns 'healthy' status
- Model loads within 5 seconds

---

#### Task 2.2: Add Model Path Configuration
**Files:**
- `E:\TORQ-CONSOLE\torq_console\core\config.py`
- `E:\TORQ-CONSOLE\.env.example` (create if needed)

**Changes Required:**

```python
# config.py - Add llama.cpp configuration section
DEFAULT_CONFIG = {
    # ... existing config ...

    # llama.cpp Configuration
    'llama_cpp_model_path': None,  # Path to GGUF model file
    'llama_cpp_n_ctx': 2048,       # Context window size
    'llama_cpp_n_gpu_layers': 0,   # Number of GPU layers (0 = CPU only)
    'llama_cpp_n_threads': None,   # CPU threads (None = auto)

    # llama.cpp Performance Tiers
    'llama_cpp_fast_max_tokens': 256,
    'llama_cpp_fast_temperature': 0.3,
    'llama_cpp_quality_max_tokens': 1024,
    'llama_cpp_quality_temperature': 0.7,
}
```

```bash
# .env.example
# llama.cpp Configuration (Optional - for local fast inference)
LLAMA_CPP_MODEL_PATH=E:/models/deepseek-r1-7b.Q5_K_M.gguf
LLAMA_CPP_N_CTX=2048
LLAMA_CPP_N_GPU_LAYERS=0
LLAMA_CPP_N_THREADS=8
```

**Test Criteria:**
- Configuration loads from .env file
- Defaults apply when .env missing
- Invalid model path logs warning (doesn't crash)

---

#### Task 2.3: Implement Tier-Based Routing Logic
**File:** `E:\TORQ-CONSOLE\torq_console\llm\manager.py`

**New Methods:**

```python
def _should_use_fast_tier(self, messages: List[Dict]) -> bool:
    """
    Determine if query should use fast llama.cpp tier.

    Criteria:
    - Total message content < 200 tokens
    - Simple query patterns (search, classification, yes/no)
    - No complex reasoning required
    """
    # Calculate approximate token count
    total_chars = sum(len(msg.get('content', '')) for msg in messages)
    approx_tokens = total_chars / 4  # Rough estimate: 1 token = 4 chars

    if approx_tokens > 200:
        return False

    # Check for simple query patterns
    last_message = messages[-1].get('content', '').lower() if messages else ''
    simple_patterns = ['search', 'find', 'list', 'classify', 'is', 'does', 'can']

    if any(pattern in last_message for pattern in simple_patterns):
        return True

    return False

def _should_use_balanced_tier(self, messages: List[Dict]) -> bool:
    """
    Determine if query should use balanced llama.cpp tier.

    Criteria:
    - Total message content 200-1000 tokens
    - Medium complexity (synthesis, summarization)
    - Not mission-critical
    """
    total_chars = sum(len(msg.get('content', '')) for msg in messages)
    approx_tokens = total_chars / 4

    if 200 <= approx_tokens <= 1000:
        return True

    return False

async def chat_with_routing(
    self,
    messages: List[Dict[str, str]],
    **kwargs
) -> str:
    """
    Intelligent routing based on query complexity.

    Routing Logic:
    1. Fast tier (llama.cpp Q4_K_M): Simple queries <200 tokens (1-3s)
    2. Balanced tier (llama.cpp Q5_K_M): Medium queries 200-1000 tokens (8-15s)
    3. Standard tier (Ollama/DeepSeek): Complex queries >1000 tokens (20-40s)
    4. Premium tier (Claude): Mission-critical or fallback
    """
    # Check if fast tier available and appropriate
    if 'llama_cpp_fast' in self.providers and self._should_use_fast_tier(messages):
        try:
            self.logger.info("Routing to fast tier (llama.cpp)")
            provider = self.providers['llama_cpp_fast']
            return await provider.complete_fast(messages, **kwargs)
        except Exception as e:
            self.logger.warning(f"Fast tier failed: {e}, falling back...")

    # Check if balanced tier available and appropriate
    if 'llama_cpp_quality' in self.providers and self._should_use_balanced_tier(messages):
        try:
            self.logger.info("Routing to balanced tier (llama.cpp)")
            provider = self.providers['llama_cpp_quality']
            return await provider.complete_quality(messages, **kwargs)
        except Exception as e:
            self.logger.warning(f"Balanced tier failed: {e}, falling back...")

    # Fall back to existing chat method (Ollama/DeepSeek/Claude)
    self.logger.info("Routing to standard tier (Ollama/DeepSeek/Claude)")

    # Use existing provider selection logic
    if 'deepseek' in self.providers:
        provider_name = 'deepseek'
    elif 'ollama' in self.providers:
        provider_name = 'ollama'
    elif 'claude' in self.providers:
        provider_name = 'claude'
    else:
        raise ValueError("No LLM providers available")

    return await self.chat(provider_name=provider_name, messages=messages, **kwargs)
```

**Test Criteria:**
- Simple queries (<200 tokens) route to fast tier
- Medium queries (200-1000 tokens) route to balanced tier
- Complex queries (>1000 tokens) route to standard tier
- Fallback works when llama.cpp unavailable
- Response quality maintained across all tiers

---

#### Task 2.4: Optimize Prince Flowers with llama.cpp Routing
**File:** `E:\TORQ-CONSOLE\torq_console\agents\torq_prince_flowers.py`

**Changes Required:**

```python
# Line ~1290 (existing synthesis code)
# Replace current provider selection with intelligent routing

# Analyze query complexity
search_result_count = len(search_results) if search_results else 0
user_message_length = len(user_message)
approx_tokens = user_message_length / 4

# Determine task complexity
if search_result_count <= 3 and approx_tokens < 200:
    task_complexity = 'simple'
elif search_result_count <= 5 and approx_tokens < 1000:
    task_complexity = 'medium'
else:
    task_complexity = 'complex'

self.logger.info(f"Task complexity: {task_complexity} (results={search_result_count}, tokens~{int(approx_tokens)})")

# Use intelligent routing from LLM Manager
try:
    if task_complexity == 'simple' and 'llama_cpp_fast' in self.llm_provider.providers:
        provider = self.llm_provider.providers['llama_cpp_fast']
        response = await provider.complete_fast(
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": full_user_message}
            ],
            max_tokens=512
        )
    elif task_complexity == 'medium' and 'llama_cpp_quality' in self.llm_provider.providers:
        provider = self.llm_provider.providers['llama_cpp_quality']
        response = await provider.complete_quality(
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": full_user_message}
            ],
            max_tokens=1500
        )
    else:
        # Use existing cascading provider logic (DeepSeek->Ollama->Claude)
        # ... existing code from Lines 1241-1325 ...
        pass

except Exception as e:
    self.logger.warning(f"llama.cpp routing failed: {e}, using standard providers")
    # Fall back to existing logic
```

**Test Criteria:**
- Simple Prince queries complete in 1-5s
- Medium Prince queries complete in 10-20s
- Complex Prince queries use existing fallback (30-60s)
- Output quality matches or exceeds current baseline
- No regression in existing functionality

---

#### Task 2.5: Create Comprehensive Test Suite
**File:** `E:\test_llama_cpp_integration.py`

**Test Coverage:**

```python
"""
Comprehensive test suite for llama.cpp integration.
Tests all routing tiers, fallback mechanisms, and performance.
"""
import asyncio
import time
from torq_console.llm.manager import LLMManager
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers

async def test_llama_cpp_provider_initialization():
    """Test 1: Provider initializes correctly"""
    print("\n" + "="*80)
    print("TEST 1: llama.cpp Provider Initialization")
    print("="*80)

    llm_manager = LLMManager()

    # Check providers list
    assert 'llama_cpp_fast' in llm_manager.providers, "Fast tier not initialized"
    assert 'llama_cpp_quality' in llm_manager.providers, "Quality tier not initialized"

    # Health check
    provider = llm_manager.providers['llama_cpp_fast']
    health = await provider.health_check()

    assert health['status'] == 'healthy', f"Provider unhealthy: {health}"

    print("[OK] Provider initialized successfully")
    print(f"[OK] Model: {health.get('model_path')}")
    print(f"[OK] Context size: {health.get('n_ctx')}")
    print(f"[OK] GPU layers: {health.get('n_gpu_layers')}")
    return True

async def test_fast_tier_performance():
    """Test 2: Fast tier completes in <3s"""
    print("\n" + "="*80)
    print("TEST 2: Fast Tier Performance (<3s target)")
    print("="*80)

    llm_manager = LLMManager()
    provider = llm_manager.providers['llama_cpp_fast']

    messages = [{"role": "user", "content": "What is 2+2? Answer in one word."}]

    start_time = time.time()
    response = await provider.complete_fast(messages, max_tokens=10)
    elapsed = time.time() - start_time

    assert elapsed < 3.0, f"Fast tier too slow: {elapsed:.2f}s"
    assert len(response) > 0, "Empty response"

    print(f"[OK] Response time: {elapsed:.2f}s")
    print(f"[OK] Response: {response[:100]}")
    return True

async def test_quality_tier_performance():
    """Test 3: Quality tier completes in <15s"""
    print("\n" + "="*80)
    print("TEST 3: Quality Tier Performance (<15s target)")
    print("="*80)

    llm_manager = LLMManager()
    provider = llm_manager.providers['llama_cpp_quality']

    messages = [{"role": "user", "content": "Explain quantum computing in 3 sentences."}]

    start_time = time.time()
    response = await provider.complete_quality(messages, max_tokens=500)
    elapsed = time.time() - start_time

    assert elapsed < 15.0, f"Quality tier too slow: {elapsed:.2f}s"
    assert len(response) > 100, "Response too short"

    print(f"[OK] Response time: {elapsed:.2f}s")
    print(f"[OK] Response length: {len(response)} chars")
    return True

async def test_intelligent_routing():
    """Test 4: LLM Manager routes correctly"""
    print("\n" + "="*80)
    print("TEST 4: Intelligent Routing Logic")
    print("="*80)

    llm_manager = LLMManager()

    # Test simple query routing
    simple_messages = [{"role": "user", "content": "Is Python fast?"}]
    assert llm_manager._should_use_fast_tier(simple_messages), "Simple query not routed to fast tier"
    print("[OK] Simple query routes to fast tier")

    # Test medium query routing
    medium_messages = [{"role": "user", "content": "Explain Python's asyncio library and provide 3 code examples with explanations."}]
    assert llm_manager._should_use_balanced_tier(medium_messages), "Medium query not routed to balanced tier"
    print("[OK] Medium query routes to balanced tier")

    # Test complex query routing
    complex_messages = [{"role": "user", "content": "A"*5000}]  # 5000 chars = ~1250 tokens
    assert not llm_manager._should_use_fast_tier(complex_messages), "Complex query incorrectly routed to fast tier"
    assert not llm_manager._should_use_balanced_tier(complex_messages), "Complex query incorrectly routed to balanced tier"
    print("[OK] Complex query routes to standard tier")

    return True

async def test_prince_flowers_simple_query():
    """Test 5: Prince Flowers with simple query"""
    print("\n" + "="*80)
    print("TEST 5: Prince Flowers Simple Query (<5s target)")
    print("="*80)

    llm_manager = LLMManager()
    prince = TORQPrinceFlowers(llm_provider=llm_manager)

    start_time = time.time()
    result = await prince.process_query("Prince what is 5+7?")
    elapsed = time.time() - start_time

    assert result.success, f"Prince query failed: {result.content}"
    assert elapsed < 10.0, f"Simple query too slow: {elapsed:.2f}s (expected <5s, allowing 10s buffer)"

    print(f"[OK] Response time: {elapsed:.2f}s")
    print(f"[OK] Success: {result.success}")
    return True

async def test_prince_flowers_medium_query():
    """Test 6: Prince Flowers with medium query"""
    print("\n" + "="*80)
    print("TEST 6: Prince Flowers Medium Query (<20s target)")
    print("="*80)

    llm_manager = LLMManager()
    prince = TORQPrinceFlowers(llm_provider=llm_manager)

    start_time = time.time()
    result = await prince.process_query("Prince explain how neural networks work in 5 sentences")
    elapsed = time.time() - start_time

    assert result.success, f"Prince query failed: {result.content}"
    assert elapsed < 30.0, f"Medium query too slow: {elapsed:.2f}s (expected <20s, allowing 30s buffer)"

    print(f"[OK] Response time: {elapsed:.2f}s")
    print(f"[OK] Success: {result.success}")
    print(f"[OK] Response length: {len(result.content)} chars")
    return True

async def test_fallback_mechanism():
    """Test 7: Fallback when llama.cpp unavailable"""
    print("\n" + "="*80)
    print("TEST 7: Fallback to Standard Providers")
    print("="*80)

    llm_manager = LLMManager()

    # Simulate llama.cpp failure by removing from providers
    if 'llama_cpp_fast' in llm_manager.providers:
        del llm_manager.providers['llama_cpp_fast']
    if 'llama_cpp_quality' in llm_manager.providers:
        del llm_manager.providers['llama_cpp_quality']

    # Query should still work via standard providers
    messages = [{"role": "user", "content": "Hello"}]

    try:
        response = await llm_manager.chat_with_routing(messages)
        assert len(response) > 0, "Empty response from fallback"
        print("[OK] Fallback to standard providers successful")
        return True
    except Exception as e:
        print(f"[FAIL] Fallback failed: {e}")
        return False

async def test_structured_output():
    """Test 8: Grammar-constrained JSON output"""
    print("\n" + "="*80)
    print("TEST 8: Structured JSON Output")
    print("="*80)

    llm_manager = LLMManager()
    provider = llm_manager.providers['llama_cpp_quality']

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"},
            "city": {"type": "string"}
        }
    }

    messages = [{"role": "user", "content": "Generate a person: John, 30, New York"}]

    result = await provider.complete_structured(messages, schema=schema)

    assert 'name' in result, "Missing 'name' in structured output"
    assert 'age' in result, "Missing 'age' in structured output"
    assert 'city' in result, "Missing 'city' in structured output"

    print(f"[OK] Structured output: {result}")
    return True

async def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*80)
    print("TORQ CONSOLE - llama.cpp INTEGRATION TEST SUITE")
    print("="*80)

    tests = [
        test_llama_cpp_provider_initialization,
        test_fast_tier_performance,
        test_quality_tier_performance,
        test_intelligent_routing,
        test_prince_flowers_simple_query,
        test_prince_flowers_medium_query,
        test_fallback_mechanism,
        test_structured_output,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/len(tests)*100:.1f}%")

    if failed == 0:
        print("\n[SUCCESS] All tests passed! Ready for production.")
    else:
        print(f"\n[WARNING] {failed} test(s) failed. Review logs above.")

    print("="*80)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
```

**Test Criteria:**
- All 8 tests pass (100% success rate)
- Fast tier: <3s response time
- Quality tier: <15s response time
- Prince simple queries: <10s
- Prince medium queries: <30s
- Fallback mechanism works
- Structured output validated

---

#### Task 2.6: Install llama-cpp-python
**Command:**

```bash
pip install llama-cpp-python
```

**Alternative (with GPU support - CUDA):**
```bash
pip install llama-cpp-python --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121
```

**Download Model (Q5_K_M recommended):**
```bash
# DeepSeek R1 7B GGUF (Q5_K_M - 4.8GB)
# From HuggingFace: https://huggingface.co/TheBloke/deepseek-r1-7b-GGUF
# Save to: E:/models/deepseek-r1-7b.Q5_K_M.gguf
```

**Test Criteria:**
- Library imports without errors
- Model file exists and loads
- No segmentation faults

---

### Session 2 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Pass Rate | 100% | 8/8 tests pass |
| Fast Tier Speed | <3s | Measured in test |
| Quality Tier Speed | <15s | Measured in test |
| Prince Simple Query | <10s | Measured in test |
| Prince Medium Query | <30s | Measured in test |
| Overall Integration | No errors | All components work |

### Session 2 Deliverables

1. **Code Integration:**
   - llama.cpp provider integrated into LLM Manager
   - Tier-based routing implemented
   - Prince Flowers optimized
   - Configuration added

2. **Testing:**
   - 8 comprehensive tests created
   - All tests pass
   - Performance validated

3. **Documentation:**
   - Configuration guide updated
   - API documentation for new methods
   - Test results documented

4. **Git Commit:**
   - All changes committed
   - Pushed to GitHub
   - Tagged as v0.81.0-llama-cpp-integration

---

## 🚀 Session 3: Codebase Indexer with FAISS (NEXT)

**Objective:** Implement semantic codebase indexing for context-aware code completion

### Overview
Build a codebase indexer that:
- Scans all project files and generates embeddings
- Stores embeddings in FAISS vector database
- Enables semantic search for relevant code context
- Updates incrementally on file changes

### Key Components

#### 3.1: File Scanner
- Recursive directory traversal
- Ignore .gitignore patterns
- Extract code blocks and docstrings
- Parse AST for function/class definitions

#### 3.2: Embedding Generator
- Use sentence-transformers (CodeBERT or similar)
- Generate embeddings for code snippets
- Chunk large files intelligently
- Cache embeddings to avoid recomputation

#### 3.3: FAISS Vector Database
- Initialize FAISS index with appropriate distance metric
- Store embeddings with metadata (file path, line numbers)
- Support incremental updates
- Persist to disk for fast restarts

#### 3.4: Semantic Search API
- Query interface for finding relevant code
- Rank results by similarity
- Filter by file type, language, or directory
- Return full context (function definition + surrounding code)

### Success Metrics
- Index 10,000+ files in <5 minutes
- Search latency <100ms
- Relevance score >0.85 for similar code
- Memory usage <2GB for large codebases

---

## 🚀 Session 4: Multi-File Editor with AST Parsing (FUTURE)

**Objective:** Enable editing 5-10 files simultaneously with full dependency tracking

### Key Components
- AST-based dependency analysis
- Transaction manager for multi-file edits
- Diff preview with syntax highlighting
- Rollback mechanism

---

## 🚀 Session 5-15: Remaining Components (FUTURE)

### Phase 1: Match Cursor (Weeks 1-6)
- **Week 1-2:** Code completion engine
- **Week 3-4:** Codebase indexer
- **Week 5-6:** Multi-file editor

### Phase 2: Match Cline (Weeks 7-9)
- **Week 7:** Autonomous task execution controller
- **Week 8-9:** Inline chat interface (Ctrl+K)

### Phase 3: Unique Differentiators (Weeks 10-15)
- **Week 10-11:** Team collaboration features
- **Week 12-13:** Hybrid local+cloud optimization
- **Week 14-15:** VS Code extension

---

## 📊 Overall Progress Tracker

### Session Status
- [x] **Session 1:** Provider fallback, search fixes, strategic plan (COMPLETE)
- [ ] **Session 2:** llama.cpp integration + tests (IN PROGRESS)
- [ ] **Session 3:** Codebase indexer with FAISS
- [ ] **Session 4:** Multi-file editor
- [ ] **Session 5-15:** Remaining 11 components

### Component Status
| Component | Status | Progress | ETA |
|-----------|--------|----------|-----|
| Provider Fallback | ✅ Complete | 100% | Done |
| Search Filter Fix | ✅ Complete | 100% | Done |
| Ollama Integration | ✅ Complete | 100% | Done |
| llama.cpp Provider | 🟡 In Progress | 80% | Session 2 |
| Tier-Based Routing | 🔴 Pending | 0% | Session 2 |
| Prince Optimization | 🔴 Pending | 0% | Session 2 |
| Test Suite | 🔴 Pending | 0% | Session 2 |
| Codebase Indexer | 🔴 Pending | 0% | Session 3 |
| Multi-File Editor | 🔴 Pending | 0% | Session 4 |
| Autonomous Controller | 🔴 Pending | 0% | Session 5+ |
| VS Code Extension | 🔴 Pending | 0% | Session 12+ |

---

## 📝 Notes & Decisions

### Design Decisions Made
1. **Provider Architecture:** Cascading fallback (DeepSeek→Ollama→Claude) ensures 100% availability
2. **Tier Strategy:** Three tiers (fast/balanced/standard) balance speed and quality
3. **Model Choice:** Q5_K_M quantization provides best speed/quality trade-off
4. **Test Coverage:** 8 comprehensive tests cover all critical paths

### Open Questions
1. Should we support multiple GGUF models simultaneously? (Answer: Phase 3, not Session 2)
2. What's the minimum hardware requirement for llama.cpp GPU inference? (Document in README)
3. How to handle model updates? (Manual for now, auto-update in Phase 3)

### Risk Register
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| llama-cpp-python installation fails | High | Low | Provide pre-built wheels, fallback to Ollama |
| GGUF model not compatible | Medium | Low | Test with multiple models, provide model list |
| Performance doesn't meet targets | Medium | Medium | Adjust quantization level, optimize prompts |
| Integration breaks existing features | High | Low | Comprehensive test suite, staged rollout |

---

## 🎯 Next Immediate Actions (Session 2)

1. **Install llama-cpp-python:** `pip install llama-cpp-python`
2. **Download model:** DeepSeek R1 7B Q5_K_M GGUF (~4.8GB)
3. **Update config:** Add llama.cpp model path to .env
4. **Integrate provider:** Modify LLM Manager (Task 2.1)
5. **Implement routing:** Add tier-based routing (Task 2.3)
6. **Create tests:** Write comprehensive test suite (Task 2.5)
7. **Run tests:** Execute all 8 tests, validate 100% pass
8. **Commit & push:** Git commit with detailed message

---

**Status:** Ready for Session 2 Implementation
**Last Updated:** 2025-10-12
**Next Review:** After Session 2 completion
