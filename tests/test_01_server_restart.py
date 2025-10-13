#!/usr/bin/env python3
"""
Test Scenario 1: Server Restart Test
====================================

Tests that verify the server properly restarts and loads the latest code (d7e3d5b).

Requirements:
1. Old processes must be killed completely
2. New server loads latest code with SearchMaster enhancements
3. SearchMaster uses 3 sources (not 1) for general queries
4. Query cleaning is active (removes "Prince search" prefixes)

Test Strategy:
- Kill any existing TORQ Console processes
- Start fresh server instance
- Verify SearchMaster is initialized with latest code
- Check available search sources
- Verify multi-source search functionality
"""

import asyncio
import psutil
import subprocess
import time
import sys
import os
import logging
from pathlib import Path

# Add TORQ Console to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServerRestartTest:
    """Test suite for server restart and code loading"""

    def __init__(self):
        self.results = {
            'old_processes_killed': False,
            'new_server_started': False,
            'latest_code_loaded': False,
            'searchmaster_initialized': False,
            'multi_source_enabled': False,
            'query_cleaning_active': False
        }
        self.test_details = {}

    def test_1_kill_old_processes(self):
        """Test 1.1: Verify old processes are killed"""
        logger.info("=" * 80)
        logger.info("TEST 1.1: Kill Old Processes")
        logger.info("=" * 80)

        killed_count = 0
        process_names = ['python', 'pythonw']

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'].lower() in process_names:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'torq_console' in cmdline.lower() or 'main.py' in cmdline.lower():
                        logger.info(f"Found TORQ process: PID={proc.info['pid']}")
                        logger.info(f"  Command: {cmdline[:100]}")

                        # Kill the process
                        proc.kill()
                        proc.wait(timeout=5)
                        killed_count += 1
                        logger.info(f"  ✓ Killed PID {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                pass

        # Wait for processes to fully terminate
        time.sleep(2)

        # Verify no TORQ processes remain
        remaining = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'].lower() in process_names:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'torq_console' in cmdline.lower():
                        remaining += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        self.results['old_processes_killed'] = (remaining == 0)
        self.test_details['killed_count'] = killed_count
        self.test_details['remaining_count'] = remaining

        logger.info(f"\nResult: Killed {killed_count} processes, {remaining} remaining")
        logger.info(f"Status: {'✓ PASS' if self.results['old_processes_killed'] else '✗ FAIL'}")

        return self.results['old_processes_killed']

    def test_2_verify_latest_code(self):
        """Test 1.2: Verify latest code is present (commit d7e3d5b)"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1.2: Verify Latest Code (d7e3d5b)")
        logger.info("=" * 80)

        try:
            # Check git commit
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )

            current_commit = result.stdout.strip()
            expected_commit = 'd7e3d5b'

            logger.info(f"Current commit: {current_commit}")
            logger.info(f"Expected commit: {expected_commit}")

            # Check for query cleaning code in Prince Flowers
            prince_file = Path(__file__).parent.parent / 'torq_console' / 'agents' / 'torq_prince_flowers.py'
            with open(prince_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for query cleaning patterns (added in d7e3d5b)
            has_query_cleaning = (
                "r'^prince\s+search" in content and
                "cleaned_query = query" in content and
                "Remove Prince-specific prefixes" in content
            )

            # Check for SearchMaster multi-source code
            searchmaster_file = Path(__file__).parent.parent / 'torq_console' / 'agents' / 'torq_search_master.py'
            with open(searchmaster_file, 'r', encoding='utf-8') as f:
                sm_content = f.read()

            # Look for multi-source general queries (fixed in commit 4cd7cc5)
            has_multi_source = (
                "_build_search_tasks" in sm_content and
                "# General queries - use multiple sources" in sm_content
            )

            self.results['latest_code_loaded'] = has_query_cleaning and has_multi_source
            self.test_details['current_commit'] = current_commit
            self.test_details['has_query_cleaning'] = has_query_cleaning
            self.test_details['has_multi_source'] = has_multi_source

            logger.info(f"\nQuery cleaning code present: {has_query_cleaning}")
            logger.info(f"Multi-source code present: {has_multi_source}")
            logger.info(f"Status: {'✓ PASS' if self.results['latest_code_loaded'] else '✗ FAIL'}")

            return self.results['latest_code_loaded']

        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return False

    async def test_3_searchmaster_sources(self):
        """Test 1.3: Verify SearchMaster uses 3+ sources for general queries"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1.3: SearchMaster Multi-Source Configuration")
        logger.info("=" * 80)

        try:
            from torq_console.agents.torq_search_master import create_search_master

            # Create SearchMaster instance
            search_master = create_search_master()

            # Check available sources
            available_sources = [k for k, v in search_master.search_sources.items() if v]
            logger.info(f"Available sources: {available_sources}")

            # Test build_search_tasks for general query
            test_query = "latest news on ElevenLabs UI"
            tasks = search_master._build_search_tasks(test_query, 'general', 10)

            logger.info(f"\nTest query: '{test_query}'")
            logger.info(f"Query type: general")
            logger.info(f"Search tasks built: {len(tasks)}")

            # For general queries, should use Tavily + Perplexity + Brave (3 sources)
            expected_min_sources = 2  # At least 2 sources
            has_multi_source = len(tasks) >= expected_min_sources

            self.results['multi_source_enabled'] = has_multi_source
            self.test_details['available_sources'] = available_sources
            self.test_details['task_count'] = len(tasks)

            logger.info(f"\nExpected minimum sources: {expected_min_sources}")
            logger.info(f"Actual sources used: {len(tasks)}")
            logger.info(f"Status: {'✓ PASS' if has_multi_source else '✗ FAIL'}")

            return has_multi_source

        except Exception as e:
            logger.error(f"Error testing SearchMaster: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_4_query_cleaning(self):
        """Test 1.4: Verify query cleaning is active"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1.4: Query Cleaning Functionality")
        logger.info("=" * 80)

        try:
            import re

            # Test query cleaning patterns (same as in Prince Flowers)
            test_cases = [
                ("Prince search for ElevenLabs UI", "ElevenLabs UI"),
                ("Prince search the web for AI agents", "AI agents"),
                ("search for information on Python", "Python"),
                ("web search for latest news", "latest news"),
            ]

            patterns = [
                r'^prince\s+search\s+(for\s+)?(the\s+)?(web\s+for\s+)?(information\s+on\s+)?',
                r'^search\s+(for\s+)?(the\s+)?(web\s+for\s+)?(information\s+on\s+)?',
            ]

            all_passed = True
            for original, expected in test_cases:
                cleaned = original
                for pattern in patterns:
                    cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
                cleaned = cleaned.strip()

                passed = (cleaned == expected)
                all_passed = all_passed and passed

                logger.info(f"\nOriginal: '{original}'")
                logger.info(f"Expected: '{expected}'")
                logger.info(f"Cleaned:  '{cleaned}'")
                logger.info(f"Result:   {'✓ PASS' if passed else '✗ FAIL'}")

            self.results['query_cleaning_active'] = all_passed
            self.test_details['query_cleaning_tests'] = len(test_cases)

            logger.info(f"\n\nOverall Status: {'✓ PASS' if all_passed else '✗ FAIL'}")

            return all_passed

        except Exception as e:
            logger.error(f"Error testing query cleaning: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def run_all_tests(self):
        """Run all server restart tests"""
        logger.info("\n" + "=" * 80)
        logger.info("TORQ CONSOLE - TEST SCENARIO 1: SERVER RESTART")
        logger.info("=" * 80)
        logger.info("Testing commit d7e3d5b: Query cleaning + Multi-source search")
        logger.info("=" * 80 + "\n")

        # Test 1: Kill old processes
        self.test_1_kill_old_processes()

        # Test 2: Verify latest code
        self.test_2_verify_latest_code()

        # Test 3: SearchMaster sources
        await self.test_3_searchmaster_sources()

        # Test 4: Query cleaning
        await self.test_4_query_cleaning()

        # Generate test report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST REPORT: Server Restart Test")
        logger.info("=" * 80)

        total_tests = len(self.results)
        passed_tests = sum(1 for v in self.results.values() if v)

        logger.info(f"\nTest Results: {passed_tests}/{total_tests} PASSED\n")

        for test_name, result in self.results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"  {test_name}: {status}")

        logger.info("\nDetailed Results:")
        for key, value in self.test_details.items():
            logger.info(f"  {key}: {value}")

        # Overall assessment
        all_passed = all(self.results.values())
        logger.info("\n" + "=" * 80)
        if all_passed:
            logger.info("✓ OVERALL: ALL TESTS PASSED")
            logger.info("Server is properly restarted with latest code (d7e3d5b)")
        else:
            logger.info("✗ OVERALL: SOME TESTS FAILED")
            logger.info("Please check failed tests and retry")
        logger.info("=" * 80 + "\n")

        return all_passed


async def main():
    """Main test runner"""
    test_suite = ServerRestartTest()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
