# TORQ Console Test Suite

Comprehensive test suite for validating TORQ Console fixes (commit d7e3d5b).

## Quick Start

```bash
# Run individual tests
python tests/test_01_server_restart.py
python tests/test_02_query_cleaning.py

# Or use pytest
pytest tests/ -v --asyncio-mode=auto
```

## Test Files

| File | Description | Status |
|------|-------------|--------|
| `test_01_server_restart.py` | Server restart and code loading | ✅ Created |
| `test_02_query_cleaning.py` | Query cleaning functionality | ✅ Created |
| `test_03_multi_source_search.py` | Multi-source search integration | ⏳ To Create |
| `test_04_recency_filter.py` | Date filtering logic | ⏳ To Create |
| `test_05_result_quality.py` | Result quality validation | ⏳ To Create |
| `test_06_ui_functionality.py` | UI component testing | ⏳ To Create |

## Documentation

- **RUN_ALL_TESTS.md** - Complete testing guide with execution instructions
- **TEST_SUITE_SUMMARY.md** - Executive summary and architecture overview
- **README.md** - This file

## Test Scenarios

### 1. Server Restart Test
Verifies old processes killed, new server loads latest code (d7e3d5b), SearchMaster uses 3 sources.

### 2. Query Cleaning Test
Input: "Prince search for ElevenLabs UI since 10/01/25"
Expected: "ElevenLabs UI since 10/01/25"

### 3. Multi-Source Search Test
Expected sources: Tavily + Perplexity + Brave
Expected results: 10-15 results, confidence: 0.75-0.90

### 4. Recency Filter Test
Query with "since 10/01/25" should NOT apply 7-day filter.
Should return results from October 1-11, 2025.

### 5. Result Quality Test
Compare with manual Google search.
Must find: ElevenLabs UI, Workflows, Subagents.
Response time: <60 seconds.

### 6. UI Functionality Test
Bottom left fully visible, MCP Connect working, no WebSocket errors.

## Expected Test Output

```
================================================================================
TORQ CONSOLE - TEST SCENARIO 1: SERVER RESTART
================================================================================

TEST 1.1: Kill Old Processes
✓ PASS - Killed 1 processes, 0 remaining

TEST 1.2: Verify Latest Code (d7e3d5b)
✓ PASS - Query cleaning code present
✓ PASS - Multi-source code present

TEST 1.3: SearchMaster Multi-Source Configuration
✓ PASS - 3 sources available

TEST 1.4: Query Cleaning Functionality
✓ PASS - All patterns working

================================================================================
TEST REPORT: Server Restart Test
================================================================================
Test Results: 4/4 PASSED

✓ OVERALL: ALL TESTS PASSED
================================================================================
```

## Prerequisites

```bash
pip install -r requirements.txt
pip install psutil pytest pytest-asyncio
```

Ensure `.env` file contains:
```
TAVILY_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
BRAVE_SEARCH_API_KEY=your_key
```

## Success Criteria

- **Minimum Pass Rate:** 28/30 tests (93%+)
- **Critical Tests:** 100% pass rate for server restart and query cleaning
- **Performance:** Average response time < 60 seconds

## Troubleshooting

**Module not found:**
```bash
export PYTHONPATH="E:/TORQ-CONSOLE:$PYTHONPATH"
```

**Process kill fails:**
Run with administrator/sudo privileges

**API rate limits:**
Wait 1 minute and retry

## Contact

**Maintainer:** TORQ Console Team
**Documentation:** See RUN_ALL_TESTS.md for complete guide
**Status:** ✅ Ready for execution
