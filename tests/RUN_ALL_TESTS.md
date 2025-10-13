# TORQ Console - Comprehensive Test Suite
## Testing Commit d7e3d5b: Query Cleaning + Multi-Source Search

**Date:** October 11, 2025
**Commits Tested:** d7e3d5b, 4cd7cc5, 4de960f, f9575a4
**Status:** ✅ READY FOR EXECUTION

---

## Test Execution Order

Run tests in the following order for best results:

```bash
# 1. Server Restart Test (Foundational)
cd E:/TORQ-CONSOLE
python tests/test_01_server_restart.py

# 2. Query Cleaning Test (Core Functionality)
python tests/test_02_query_cleaning.py

# 3. Multi-Source Search Test (Integration)
python tests/test_03_multi_source_search.py

# 4. Recency Filter Test (Date Handling)
python tests/test_04_recency_filter.py

# 5. Result Quality Test (End-to-End)
python tests/test_05_result_quality.py

# 6. UI Functionality Test (Frontend)
python tests/test_06_ui_functionality.py
```

---

## Test Scenario Details

### 1. Server Restart Test (`test_01_server_restart.py`)
**Purpose:** Verify server properly restarts with latest code

**Tests:**
- ✅ Old processes killed completely
- ✅ New server loads commit d7e3d5b code
- ✅ SearchMaster uses 3 sources (not 1)
- ✅ Query cleaning patterns present

**Expected Results:**
- All TORQ processes terminated
- Latest code loaded from git
- Multi-source search enabled for general queries
- Query cleaning regex patterns active

**Pass Criteria:** 4/4 tests passing

---

### 2. Query Cleaning Test (`test_02_query_cleaning.py`)
**Purpose:** Verify query cleaning works correctly

**Tests:**
- ✅ Pattern matching removes "Prince search" prefixes
- ✅ Date keywords preserved (since, from, after, before)
- ✅ Case-insensitive matching
- ✅ Edge cases handled
- ✅ Integration with SearchMaster

**Test Input:** "Prince search for ElevenLabs UI since 10/01/25"
**Expected Cleaned:** "ElevenLabs UI since 10/01/25"

**Pass Criteria:** 5/5 tests passing

---

### 3. Multi-Source Search Test (`test_03_multi_source_search.py`)
**Purpose:** Verify SearchMaster uses multiple sources

**Tests:**
- ✅ Tavily API called for general queries
- ✅ Perplexity API called for general queries
- ✅ Brave API called for general queries
- ✅ Total 2-3 sources used (not just 1)
- ✅ Results aggregated from multiple APIs

**Expected Sources:** Tavily + Perplexity + Brave
**Expected Results:** 10-15 results total
**Expected Confidence:** 0.75-0.90

**Pass Criteria:** 5/5 tests passing

---

### 4. Recency Filter Test (`test_04_recency_filter.py`)
**Purpose:** Verify recency filter behaves correctly

**Tests:**
- ✅ 7-day filter applied by default for news
- ✅ Explicit dates skip auto-filter
- ✅ "since 10/01/25" preserves date range
- ✅ Results span October 1-11, 2025
- ✅ Filter logging works correctly

**Test Query:** "latest news on ElevenLabs UI since 10/01/25"
**Expected Behavior:** NO 7-day filter applied (explicit date present)
**Expected Results:** Articles from Oct 1-11, 2025

**Pass Criteria:** 5/5 tests passing

---

### 5. Result Quality Test (`test_05_result_quality.py`)
**Purpose:** Compare TORQ results with manual Google search

**Tests:**
- ✅ ElevenLabs UI component library found
- ✅ ElevenLabs Workflows information found
- ✅ Subagents feature mentioned
- ✅ Response time < 60 seconds
- ✅ Relevance matches or exceeds Google

**Baseline:** User's manual Google search results
**Expected Quality:** 60%+ fact coverage
**Expected Speed:** <60 seconds total

**Pass Criteria:** 5/5 tests passing

---

### 6. UI Functionality Test (`test_06_ui_functionality.py`)
**Purpose:** Verify frontend works correctly

**Tests:**
- ✅ Bottom left UI fully visible
- ✅ MCP Connect button working
- ✅ No WebSocket errors (or harmless warnings only)
- ✅ Chat interface responsive
- ✅ Search results display correctly

**Known Issues:**
- WebSocket polling warnings are acceptable (harmless)
- Socket.IO migration completed (commit 4de960f)

**Pass Criteria:** 5/5 tests passing

---

## Validation Criteria

### Overall Test Success Criteria
- **Minimum Pass Rate:** 28/30 tests (93%+)
- **Critical Tests:** All server restart and query cleaning tests must pass
- **Performance:** Average response time < 60 seconds
- **Quality:** Search results comparable to manual Google search

### Test Result Summary Format
```
TEST SUITE SUMMARY
==================
Total Tests: 30
Passed: XX
Failed: XX
Success Rate: XX%

Critical Issues: [None/List]
Warnings: [None/List]
Recommendations: [List]
```

---

## Quick Test Script

Create and run all tests automatically:

```bash
# Create quick test runner
cat > E:/TORQ-CONSOLE/tests/run_all.py << 'EOF'
#!/usr/bin/env python3
"""Run all TORQ Console tests"""
import asyncio
import subprocess
import sys
from pathlib import Path

async def main():
    test_dir = Path(__file__).parent
    test_files = [
        'test_01_server_restart.py',
        'test_02_query_cleaning.py',
        # Add others as they're created
    ]

    results = []
    for test_file in test_files:
        print(f"\nRunning {test_file}...")
        result = subprocess.run(
            [sys.executable, str(test_dir / test_file)],
            capture_output=True,
            text=True
        )
        results.append((test_file, result.returncode == 0))
        print(result.stdout)

    # Summary
    print("\n" + "=" * 80)
    print("OVERALL TEST SUMMARY")
    print("=" * 80)
    passed = sum(1 for _, success in results if success)
    print(f"Tests Passed: {passed}/{len(results)}")

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {test_name}: {status}")

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Run all tests
python E:/TORQ-CONSOLE/tests/run_all.py
```

---

## Test Environment Requirements

### Required Dependencies
```bash
pip install -r requirements.txt  # TORQ Console dependencies
pip install psutil  # For process management tests
pip install pytest pytest-asyncio  # For test framework
```

### Environment Variables
Ensure `.env` file contains:
```
TAVILY_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here
BRAVE_SEARCH_API_KEY=your_key_here
COINGECKO_API_KEY=your_key_here  # Optional
```

### System Requirements
- Python 3.8+
- Git (for commit verification)
- Active internet connection (for API tests)
- Windows/Linux/Mac compatible

---

## Troubleshooting

### Common Issues

**Issue 1: Tests fail with "No module named 'torq_console'"**
```bash
# Solution: Add TORQ-CONSOLE to PYTHONPATH
export PYTHONPATH="E:/TORQ-CONSOLE:$PYTHONPATH"  # Linux/Mac
set PYTHONPATH=E:/TORQ-CONSOLE;%PYTHONPATH%  # Windows
```

**Issue 2: API rate limits**
```
# Solution: Use API keys and respect rate limits
# Tavily: 1000 requests/month free tier
# Perplexity: 5 requests/minute
# Brave: 2000 requests/month free tier
```

**Issue 3: Process kill fails**
```bash
# Solution: Run with administrator/sudo privileges
sudo python tests/test_01_server_restart.py  # Linux/Mac
# Run PowerShell as Administrator  # Windows
```

---

## Expected Test Output

### Successful Test Run
```
================================================================================
TORQ CONSOLE - TEST SCENARIO 1: SERVER RESTART
================================================================================
Testing commit d7e3d5b: Query cleaning + Multi-source search
================================================================================

================================================================================
TEST 1.1: Kill Old Processes
================================================================================
Found TORQ process: PID=12345
  Command: python torq_console\ui\main.py
  ✓ Killed PID 12345

Result: Killed 1 processes, 0 remaining
Status: ✓ PASS

================================================================================
TEST 1.2: Verify Latest Code (d7e3d5b)
================================================================================
Current commit: d7e3d5b
Expected commit: d7e3d5b

Query cleaning code present: True
Multi-source code present: True
Status: ✓ PASS

... [additional test output] ...

================================================================================
TEST REPORT: Server Restart Test
================================================================================

Test Results: 4/4 PASSED

  old_processes_killed: ✓ PASS
  latest_code_loaded: ✓ PASS
  multi_source_enabled: ✓ PASS
  query_cleaning_active: ✓ PASS

================================================================================
✓ OVERALL: ALL TESTS PASSED
Server is properly restarted with latest code (d7e3d5b)
================================================================================
```

---

## Next Steps After Testing

1. **All Tests Pass (✓)**
   - Proceed to production deployment
   - Update CHANGELOG.md with test results
   - Tag release as `v1.1.0-tested`

2. **Some Tests Fail (✗)**
   - Review failed test details
   - Fix issues in code
   - Re-run failed tests
   - Update documentation if needed

3. **Performance Issues**
   - Review API response times
   - Check network connectivity
   - Optimize query processing
   - Consider caching strategies

---

## Test Maintenance

### Adding New Tests
1. Create test file: `test_XX_description.py`
2. Follow existing test structure
3. Add to this document
4. Update `run_all.py` script

### Updating Existing Tests
1. Maintain backward compatibility
2. Update expected values if code changes
3. Document any breaking changes
4. Re-run full test suite

---

## Contact and Support

**Test Suite Maintainer:** TORQ Console Team
**Last Updated:** October 11, 2025
**Version:** 1.0.0
**Status:** ✅ Production Ready

For issues or questions:
- GitHub: https://github.com/yourusername/TORQ-CONSOLE
- Email: support@torq-console.dev
- Documentation: E:/TORQ-CONSOLE/README.md

---

**END OF TEST DOCUMENTATION**
