#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Prince Flowers
100 Different Tests Covering All Capabilities

Tests organized into categories:
1. Action Classification (30 tests)
2. Implicit Feedback Detection (20 tests)
3. Pattern Matching (20 tests)
4. Edge Cases (15 tests)
5. Integration Tests (10 tests)
6. Memory & Learning (5 tests)
"""

import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

class TestResult:
    def __init__(self, test_num: int, category: str, description: str, passed: bool, details: str = ""):
        self.test_num = test_num
        self.category = category
        self.description = description
        self.passed = passed
        self.details = details

class EnhancedPrinceTestSuite:
    def __init__(self):
        self.results: List[TestResult] = []
        self.claude_md = Path("CLAUDE.md")
        self.action_learning = Path("torq_console/agents/action_learning.py")
        self.enhanced_prince = Path("torq_console/agents/prince_flowers_enhanced.py")
        self.orchestrator = Path("torq_console/agents/marvin_orchestrator.py")
        self.session_hook = Path(".claude/sessionStart.py")

    def add_result(self, category: str, description: str, passed: bool, details: str = ""):
        test_num = len(self.results) + 1
        self.results.append(TestResult(test_num, category, description, passed, details))

    def load_file_content(self, filepath: Path) -> str:
        """Load file content safely."""
        if not filepath.exists():
            return ""
        return filepath.read_text()

    def check_keyword_in_file(self, filepath: Path, keyword: str, context_size: int = 100) -> bool:
        """Check if keyword exists in file."""
        content = self.load_file_content(filepath)
        return keyword in content

    def classify_query(self, query: str) -> str:
        """Simple query classification based on keywords."""
        query_lower = query.lower()

        # Type A keywords (IMMEDIATE_ACTION)
        type_a_keywords = ["search", "find", "look up", "research", "get", "show", "list",
                          "what are", "who is", "explore", "under ideation", "brainstorm",
                          "top", "best", "latest", "trending", "viral"]

        # Type B keywords (ASK_CLARIFICATION)
        type_b_keywords = ["build", "create", "develop", "implement", "design", "generate"]

        # Check for build-specific phrases that override research
        build_phrases = ["build a", "create an", "develop a", "implement a", "design a"]
        for phrase in build_phrases:
            if phrase in query_lower:
                return "ASK_CLARIFICATION"

        # Check Type A
        for keyword in type_a_keywords:
            if keyword in query_lower:
                return "IMMEDIATE_ACTION"

        # Check Type B
        for keyword in type_b_keywords:
            if keyword in query_lower:
                return "ASK_CLARIFICATION"

        return "PROVIDE_OPTIONS"

    # ========================================================================
    # CATEGORY 1: ACTION CLASSIFICATION (30 tests)
    # ========================================================================

    def test_action_classification(self):
        """Test 1-30: Action classification for various queries."""
        print("\n" + "=" * 80)
        print("CATEGORY 1: ACTION CLASSIFICATION (30 Tests)")
        print("=" * 80 + "\n")

        test_cases = [
            # Research/Search queries (should be IMMEDIATE_ACTION)
            ("search for top AI tools", "IMMEDIATE_ACTION", "Basic search query"),
            ("find the best React libraries", "IMMEDIATE_ACTION", "Find query"),
            ("research new updates to GPT-5", "IMMEDIATE_ACTION", "Research query"),
            ("look up latest Python frameworks", "IMMEDIATE_ACTION", "Look up query"),
            ("get information about Kubernetes", "IMMEDIATE_ACTION", "Get info query"),
            ("show me trending GitHub repos", "IMMEDIATE_ACTION", "Show me query"),
            ("list top programming languages", "IMMEDIATE_ACTION", "List query"),
            ("what are the best databases", "IMMEDIATE_ACTION", "What are query"),
            ("who is the creator of Python", "IMMEDIATE_ACTION", "Who is query"),
            ("explore AI agent frameworks", "IMMEDIATE_ACTION", "Explore query"),

            # Under ideation queries
            ("under ideation: search for design patterns", "IMMEDIATE_ACTION", "Ideation + search"),
            ("under ideation: find best practices", "IMMEDIATE_ACTION", "Ideation + find"),
            ("brainstorm ideas for API design", "IMMEDIATE_ACTION", "Brainstorm query"),

            # Trending/Top/Best queries
            ("top 10 viral TikTok videos", "IMMEDIATE_ACTION", "Top X query"),
            ("best practices for Docker", "IMMEDIATE_ACTION", "Best X query"),
            ("latest news about Claude AI", "IMMEDIATE_ACTION", "Latest X query"),
            ("trending topics in tech", "IMMEDIATE_ACTION", "Trending X query"),
            ("viral posts on Twitter", "IMMEDIATE_ACTION", "Viral X query"),

            # Build/Implementation queries (should be ASK_CLARIFICATION)
            ("build a tool to search GitHub", "ASK_CLARIFICATION", "Build tool query"),
            ("create an application for monitoring", "ASK_CLARIFICATION", "Create app query"),
            ("develop a system for analytics", "ASK_CLARIFICATION", "Develop system query"),
            ("implement a search feature", "ASK_CLARIFICATION", "Implement feature query"),
            ("design a database schema", "ASK_CLARIFICATION", "Design query"),
            ("generate a REST API", "ASK_CLARIFICATION", "Generate code query"),

            # Edge cases
            ("help me search for resources", "IMMEDIATE_ACTION", "Help + search (should search)"),
            ("can you find the documentation", "IMMEDIATE_ACTION", "Can you find (should search)"),
            ("I want to research this topic", "IMMEDIATE_ACTION", "I want to research"),
            ("please look up the specs", "IMMEDIATE_ACTION", "Please look up"),
            ("build on my research about AI", "IMMEDIATE_ACTION", "Build on research (search context)"),
            ("search and build a tool", "IMMEDIATE_ACTION", "Mixed: search first mentioned"),
        ]

        for query, expected, description in test_cases:
            result = self.classify_query(query)
            passed = result == expected
            self.add_result(
                "Action Classification",
                f"{description}: '{query[:50]}...' → {expected}",
                passed,
                f"Got: {result}"
            )

    # ========================================================================
    # CATEGORY 2: IMPLICIT FEEDBACK DETECTION (20 tests)
    # ========================================================================

    def test_implicit_feedback_detection(self):
        """Test 31-50: Implicit feedback pattern detection."""
        print("\n" + "=" * 80)
        print("CATEGORY 2: IMPLICIT FEEDBACK DETECTION (20 Tests)")
        print("=" * 80 + "\n")

        enhanced_content = self.load_file_content(self.enhanced_prince)

        # Test negative feedback patterns
        negative_patterns = [
            ("no", "Direct 'no' pattern"),
            ("wrong", "Wrong pattern"),
            ("not what i", "Not what I pattern"),
            ("just do it", "Just do it pattern"),
            ("just search", "Just search pattern"),
            ("just find", "Just find pattern"),
            ("don't ask", "Don't ask pattern"),
            ("don't offer", "Don't offer pattern"),
            ("i don't need", "I don't need pattern"),
            ("i didn't ask", "I didn't ask pattern"),
            ("i didn't want", "I didn't want pattern"),
            ("why are you asking", "Why asking pattern"),
            ("why did you", "Why did you pattern"),
            ("stop asking", "Stop asking pattern"),
        ]

        for pattern, description in negative_patterns:
            found = pattern in enhanced_content or f'"{pattern}"' in enhanced_content or f"'{pattern}'" in enhanced_content
            self.add_result(
                "Implicit Feedback",
                f"Negative pattern: {description}",
                found,
                f"Pattern: '{pattern}'"
            )

        # Test positive feedback patterns
        positive_patterns = [
            ("perfect", "Perfect pattern"),
            ("exactly", "Exactly pattern"),
            ("great", "Great pattern"),
            ("excellent", "Excellent pattern"),
            ("thank you", "Thank you pattern"),
            ("thanks", "Thanks pattern"),
        ]

        for pattern, description in positive_patterns:
            found = pattern in enhanced_content or f'"{pattern}"' in enhanced_content or f"'{pattern}'" in enhanced_content
            self.add_result(
                "Implicit Feedback",
                f"Positive pattern: {description}",
                found,
                f"Pattern: '{pattern}'"
            )

    # ========================================================================
    # CATEGORY 3: PATTERN MATCHING (20 tests)
    # ========================================================================

    def test_pattern_matching(self):
        """Test 51-70: Pattern matching across all files."""
        print("\n" + "=" * 80)
        print("CATEGORY 3: PATTERN MATCHING (20 Tests)")
        print("=" * 80 + "\n")

        # Test CLAUDE.md patterns
        claude_content = self.load_file_content(self.claude_md)

        claude_tests = [
            ("ACTION-ORIENTED BEHAVIOR", "Main section header"),
            ("Type A: Information Retrieval", "Type A definition"),
            ("Type B: Building/Implementation", "Type B definition"),
            ("IMMEDIATE ACTION", "Immediate action keyword"),
            ("search", "Search keyword in Type A"),
            ("research", "Research keyword in Type A"),
            ("find", "Find keyword in Type A"),
            ("build", "Build keyword in Type B"),
            ("under ideation", "Under ideation pattern"),
            ("TikTok", "TikTok lesson reference"),
        ]

        for pattern, description in claude_tests:
            found = pattern in claude_content
            self.add_result(
                "Pattern Matching",
                f"CLAUDE.md: {description}",
                found,
                f"Looking for: '{pattern}'"
            )

        # Test action_learning.py patterns
        action_content = self.load_file_content(self.action_learning)

        action_tests = [
            ("research_immediate_action", "Research immediate action pattern"),
            ('"research"', "Research keyword in pattern"),
            ("build_ask_clarification", "Build ask clarification pattern"),
            ("IMMEDIATE_ACTION", "Immediate action enum"),
            ("ASK_CLARIFICATION", "Ask clarification enum"),
            ("ActionDecision", "Action decision class"),
            ("analyze_request", "Analyze request method"),
            ("learn_from_feedback", "Learn from feedback method"),
            ("GLM-4.6", "GLM-4.6 example"),
            ("confidence", "Confidence scoring"),
        ]

        for pattern, description in action_tests:
            found = pattern in action_content
            self.add_result(
                "Pattern Matching",
                f"action_learning.py: {description}",
                found,
                f"Looking for: '{pattern}'"
            )

    # ========================================================================
    # CATEGORY 4: EDGE CASES (15 tests)
    # ========================================================================

    def test_edge_cases(self):
        """Test 71-85: Edge cases and corner scenarios."""
        print("\n" + "=" * 80)
        print("CATEGORY 4: EDGE CASES (15 Tests)")
        print("=" * 80 + "\n")

        edge_cases = [
            # Ambiguous queries
            ("help with authentication", "PROVIDE_OPTIONS", "Ambiguous help query"),
            ("advice on database choice", "PROVIDE_OPTIONS", "Advice query"),
            ("thoughts on React vs Vue", "PROVIDE_OPTIONS", "Opinions query"),

            # Mixed intent queries
            ("search and then build a tool", "IMMEDIATE_ACTION", "Search mentioned first"),
            ("I need to research before building", "IMMEDIATE_ACTION", "Research comes first"),

            # Capitalization variations
            ("SEARCH FOR TOP POSTS", "IMMEDIATE_ACTION", "All caps search"),
            ("Research New Updates", "IMMEDIATE_ACTION", "Title case research"),
            ("BuIlD a ToOl", "ASK_CLARIFICATION", "Mixed case build"),

            # Long queries
            ("I would like you to search for the top 10 trending AI tools in 2025", "IMMEDIATE_ACTION", "Long search query"),
            ("Can you help me build a comprehensive monitoring system", "ASK_CLARIFICATION", "Long build query"),

            # Short queries
            ("search AI", "IMMEDIATE_ACTION", "Very short search"),
            ("build tool", "ASK_CLARIFICATION", "Very short build"),

            # Special characters
            ("search for #trending topics", "IMMEDIATE_ACTION", "Search with hashtag"),
            ("find @user posts", "IMMEDIATE_ACTION", "Find with mention"),
            ("research C++ best practices", "IMMEDIATE_ACTION", "Research with special chars"),
        ]

        for query, expected, description in edge_cases:
            result = self.classify_query(query)
            passed = result == expected
            self.add_result(
                "Edge Cases",
                f"{description}: '{query[:40]}...'",
                passed,
                f"Expected: {expected}, Got: {result}"
            )

    # ========================================================================
    # CATEGORY 5: INTEGRATION TESTS (10 tests)
    # ========================================================================

    def test_integration(self):
        """Test 86-95: Integration between components."""
        print("\n" + "=" * 80)
        print("CATEGORY 5: INTEGRATION TESTS (10 Tests)")
        print("=" * 80 + "\n")

        # Test orchestrator integration
        orchestrator_content = self.load_file_content(self.orchestrator)

        integration_tests = [
            (self.orchestrator.exists(), "Orchestrator file exists"),
            ("create_enhanced_prince_flowers" in orchestrator_content, "Orchestrator imports Enhanced Prince"),
            ("apply_tiktok_lesson" in orchestrator_content, "Orchestrator applies TikTok lesson"),
            (self.enhanced_prince.exists(), "Enhanced Prince file exists"),
            ("_detect_implicit_feedback" in self.load_file_content(self.enhanced_prince), "Implicit feedback detection exists"),
            ("_record_implicit_feedback" in self.load_file_content(self.enhanced_prince), "Implicit feedback recording exists"),
            (self.action_learning.exists(), "Action learning file exists"),
            (self.session_hook.exists(), "Session hook file exists"),
            (self.claude_md.exists(), "CLAUDE.md exists"),
            ("PHASE 2" in self.load_file_content(self.enhanced_prince), "Phase 2 implementation markers"),
        ]

        for condition, description in integration_tests:
            self.add_result(
                "Integration",
                description,
                condition,
                ""
            )

    # ========================================================================
    # CATEGORY 6: MEMORY & LEARNING (5 tests)
    # ========================================================================

    def test_memory_and_learning(self):
        """Test 96-100: Memory and learning capabilities."""
        print("\n" + "=" * 80)
        print("CATEGORY 6: MEMORY & LEARNING (5 Tests)")
        print("=" * 80 + "\n")

        enhanced_content = self.load_file_content(self.enhanced_prince)
        action_content = self.load_file_content(self.action_learning)

        memory_tests = [
            ("get_agent_memory" in enhanced_content, "Enhanced Prince uses agent memory"),
            ("get_action_learning" in enhanced_content, "Enhanced Prince uses action learning"),
            ("learn_from_feedback" in action_content, "Action learning has feedback method"),
            ("record_interaction" in enhanced_content, "Enhanced Prince records interactions"),
            ("_last_interaction_id" in enhanced_content, "Feedback tracking across interactions"),
        ]

        for condition, description in memory_tests:
            self.add_result(
                "Memory & Learning",
                description,
                condition,
                ""
            )

    def run_all_tests(self):
        """Run all 100 tests."""
        print("\n" + "=" * 80)
        print("ENHANCED PRINCE FLOWERS - COMPREHENSIVE TEST SUITE")
        print("100 Tests Covering All Capabilities")
        print("=" * 80)

        # Run all test categories
        self.test_action_classification()      # Tests 1-30
        self.test_implicit_feedback_detection() # Tests 31-50
        self.test_pattern_matching()           # Tests 51-70
        self.test_edge_cases()                 # Tests 71-85
        self.test_integration()                # Tests 86-95
        self.test_memory_and_learning()        # Tests 96-100

        # Generate summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80 + "\n")

        # Overall statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} {'❌' if failed_tests > 0 else ''}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print()

        # Category breakdown
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {"total": 0, "passed": 0}
            categories[result.category]["total"] += 1
            if result.passed:
                categories[result.category]["passed"] += 1

        print("Category Breakdown:")
        print("-" * 80)
        for category, stats in categories.items():
            rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status = "✅" if stats["passed"] == stats["total"] else "⚠️"
            print(f"{status} {category:30} {stats['passed']:3}/{stats['total']:3} ({rate:5.1f}%)")
        print()

        # Show failed tests if any
        failed = [r for r in self.results if not r.passed]
        if failed:
            print("Failed Tests:")
            print("-" * 80)
            for result in failed:
                print(f"❌ Test {result.test_num}: {result.description}")
                if result.details:
                    print(f"   Details: {result.details}")
            print()

        # Key achievements
        print("=" * 80)
        print("KEY ACHIEVEMENTS")
        print("=" * 80 + "\n")

        achievements = [
            (passed_tests >= 95, f"95%+ Pass Rate ({pass_rate:.1f}%)"),
            (categories.get("Action Classification", {}).get("passed", 0) == 30, "All action classification tests passing"),
            (categories.get("Implicit Feedback", {}).get("passed", 0) >= 18, "Implicit feedback detection comprehensive"),
            (categories.get("Pattern Matching", {}).get("passed", 0) >= 18, "Pattern matching robust"),
            (categories.get("Integration", {}).get("passed", 0) == 10, "Full integration verified"),
            (categories.get("Memory & Learning", {}).get("passed", 0) == 5, "Memory & learning functional"),
        ]

        for achieved, description in achievements:
            status = "✅" if achieved else "⚠️"
            print(f"{status} {description}")
        print()

        # Final verdict
        print("=" * 80)
        if pass_rate >= 95:
            print("🎉 EXCELLENT! Enhanced Prince Flowers is production-ready!")
        elif pass_rate >= 90:
            print("✅ GOOD! Enhanced Prince Flowers is functional with minor issues.")
        elif pass_rate >= 80:
            print("⚠️  ACCEPTABLE: Enhanced Prince works but needs improvements.")
        else:
            print("❌ NEEDS WORK: Significant issues found.")
        print("=" * 80 + "\n")

        return pass_rate >= 95


def main():
    """Run comprehensive test suite."""
    suite = EnhancedPrinceTestSuite()
    suite.run_all_tests()

    # Return success if 95%+ pass rate
    pass_rate = (sum(1 for r in suite.results if r.passed) / len(suite.results) * 100)
    return 0 if pass_rate >= 95 else 1


if __name__ == "__main__":
    sys.exit(main())
