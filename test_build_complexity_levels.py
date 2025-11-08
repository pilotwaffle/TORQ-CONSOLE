#!/usr/bin/env python3
"""
Test Enhanced Prince: Building Apps/Games of Different Complexities

This test validates that Prince correctly asks clarifying questions
for build requests across different complexity levels.

Expected Behavior:
- ALL build requests → ASK_CLARIFICATION
- Simple builds → Ask 2-3 basic questions
- Complex builds → Ask detailed, comprehensive questions
- NEVER → Immediate implementation without questions
"""

import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

class BuildComplexityTest:
    def __init__(self):
        self.results = []
        self.claude_md = Path("CLAUDE.md")
        self.action_learning = Path("torq_console/agents/action_learning.py")
        self.enhanced_prince = Path("torq_console/agents/prince_flowers_enhanced.py")

    def classify_query(self, query: str) -> str:
        """Classify query based on keywords."""
        query_lower = query.lower()

        # Build/implementation keywords
        build_keywords = [
            "build", "create", "develop", "implement", "design",
            "make", "generate", "construct", "code", "write"
        ]

        # Check if it's a build request
        for keyword in build_keywords:
            if keyword in query_lower:
                # Make sure it's not just "build on research" (research context)
                if "build on" in query_lower and any(r in query_lower for r in ["research", "study", "findings"]):
                    continue
                return "ASK_CLARIFICATION"

        # Research keywords
        research_keywords = [
            "search", "find", "research", "look up", "explore",
            "show", "list", "what are", "under ideation"
        ]

        for keyword in research_keywords:
            if keyword in query_lower:
                return "IMMEDIATE_ACTION"

        return "PROVIDE_OPTIONS"

    def verify_patterns_exist(self) -> Dict[str, bool]:
        """Verify that build patterns exist in code."""
        results = {}

        # Check CLAUDE.md
        if self.claude_md.exists():
            content = self.claude_md.read_text()
            results['claude_type_b'] = "Type B: Building/Implementation" in content
            results['claude_ask_clarification'] = "ASK CLARIFICATION" in content
            results['claude_build_keyword'] = "build" in content.lower()

        # Check action_learning.py
        if self.action_learning.exists():
            content = self.action_learning.read_text()
            results['action_build_pattern'] = "build_ask_clarification" in content
            results['action_ask_clarification'] = "ASK_CLARIFICATION" in content

        # Check enhanced_prince.py
        if self.enhanced_prince.exists():
            content = self.enhanced_prince.read_text()
            results['prince_build_instructions'] = "build" in content.lower()
            results['prince_ask_clarification'] = "ASK CLARIFICATION" in content

        return results

    def run_tests(self):
        """Run comprehensive build complexity tests."""
        print("\n" + "=" * 80)
        print("ENHANCED PRINCE: BUILD COMPLEXITY TESTS")
        print("Testing ASK_CLARIFICATION behavior across complexity levels")
        print("=" * 80 + "\n")

        # First, verify patterns exist
        print("=" * 80)
        print("VERIFICATION: Build Patterns Exist in Code")
        print("=" * 80 + "\n")

        patterns = self.verify_patterns_exist()
        all_patterns_exist = all(patterns.values())

        for key, exists in patterns.items():
            status = "✅" if exists else "❌"
            print(f"{status} {key}: {exists}")

        print()
        if not all_patterns_exist:
            print("⚠️  WARNING: Some patterns missing. Tests may not be fully valid.\n")

        # Test different complexity levels
        self.test_simple_apps()
        self.test_medium_apps()
        self.test_complex_apps()
        self.test_simple_games()
        self.test_medium_games()
        self.test_complex_games()
        self.test_edge_cases()

        # Print summary
        self.print_summary()

    def test_simple_apps(self):
        """Test simple application builds."""
        print("=" * 80)
        print("CATEGORY 1: Simple Apps (10 tests)")
        print("Expected: ASK_CLARIFICATION with 2-3 basic questions")
        print("=" * 80 + "\n")

        test_cases = [
            ("build a todo app", "Basic CRUD app"),
            ("create a calculator", "Simple utility"),
            ("make a note-taking app", "Basic text storage"),
            ("develop a timer application", "Simple counter app"),
            ("build a weather app", "API integration app"),
            ("create a color picker", "Simple UI tool"),
            ("make a random quote generator", "Content display app"),
            ("build a unit converter", "Calculation app"),
            ("create a stopwatch", "Time tracking app"),
            ("develop a password generator", "Utility app"),
        ]

        for query, description in test_cases:
            result = self.classify_query(query)
            passed = result == "ASK_CLARIFICATION"
            status = "✅" if passed else "❌"
            self.results.append((query, result, "ASK_CLARIFICATION", passed))
            print(f"{status} {description}: '{query}'")
            print(f"   Expected: ASK_CLARIFICATION, Got: {result}")

            if passed:
                print(f"   Should ask: What features? Storage type? UI framework?")
            print()

    def test_medium_apps(self):
        """Test medium complexity applications."""
        print("=" * 80)
        print("CATEGORY 2: Medium Complexity Apps (10 tests)")
        print("Expected: ASK_CLARIFICATION with detailed questions")
        print("=" * 80 + "\n")

        test_cases = [
            ("build a blog platform", "Multi-user content system"),
            ("create an e-commerce site", "Shopping cart system"),
            ("develop a task management system", "Team collaboration app"),
            ("build a chat application", "Real-time messaging"),
            ("create a social media dashboard", "Multi-platform aggregator"),
            ("make a file sharing service", "Upload/download system"),
            ("build a booking system", "Reservation management"),
            ("develop a CRM tool", "Customer management"),
            ("create a project tracking app", "Kanban/agile tool"),
            ("build an inventory system", "Stock management"),
        ]

        for query, description in test_cases:
            result = self.classify_query(query)
            passed = result == "ASK_CLARIFICATION"
            status = "✅" if passed else "❌"
            self.results.append((query, result, "ASK_CLARIFICATION", passed))
            print(f"{status} {description}: '{query}'")
            print(f"   Expected: ASK_CLARIFICATION, Got: {result}")

            if passed:
                print(f"   Should ask: Architecture? Database? Auth? Scaling? Features?")
            print()

    def test_complex_apps(self):
        """Test complex application builds."""
        print("=" * 80)
        print("CATEGORY 3: Complex Apps (10 tests)")
        print("Expected: ASK_CLARIFICATION with comprehensive questions")
        print("=" * 80 + "\n")

        test_cases = [
            ("build a video streaming platform", "Netflix-like system"),
            ("create a cloud storage service", "Dropbox-like platform"),
            ("develop a ride-sharing app", "Uber-like application"),
            ("build a cryptocurrency exchange", "Trading platform"),
            ("create an AI-powered analytics platform", "ML/data system"),
            ("make a microservices e-commerce platform", "Distributed system"),
            ("build a real-time collaboration tool", "Google Docs-like"),
            ("develop a food delivery marketplace", "Multi-vendor platform"),
            ("create a healthcare management system", "HIPAA-compliant platform"),
            ("build a enterprise resource planning system", "Full ERP suite"),
        ]

        for query, description in test_cases:
            result = self.classify_query(query)
            passed = result == "ASK_CLARIFICATION"
            status = "✅" if passed else "❌"
            self.results.append((query, result, "ASK_CLARIFICATION", passed))
            print(f"{status} {description}: '{query}'")
            print(f"   Expected: ASK_CLARIFICATION, Got: {result}")

            if passed:
                print(f"   Should ask: Architecture? Microservices? Scaling? Security?")
                print(f"                Database? Caching? CDN? Compliance? Budget?")
            print()

    def test_simple_games(self):
        """Test simple game builds."""
        print("=" * 80)
        print("CATEGORY 4: Simple Games (10 tests)")
        print("Expected: ASK_CLARIFICATION with game-specific questions")
        print("=" * 80 + "\n")

        test_cases = [
            ("build a tic-tac-toe game", "2-player board game"),
            ("create a snake game", "Classic arcade"),
            ("make a memory card game", "Match pairs"),
            ("develop a rock-paper-scissors game", "Simple choice game"),
            ("build a number guessing game", "Random number game"),
            ("create a whack-a-mole game", "Timing game"),
            ("make a Simon Says game", "Pattern memory"),
            ("build a word guessing game", "Hangman-style"),
            ("create a pong game", "2-player paddle"),
            ("develop a minesweeper clone", "Grid puzzle"),
        ]

        for query, description in test_cases:
            result = self.classify_query(query)
            passed = result == "ASK_CLARIFICATION"
            status = "✅" if passed else "❌"
            self.results.append((query, result, "ASK_CLARIFICATION", passed))
            print(f"{status} {description}: '{query}'")
            print(f"   Expected: ASK_CLARIFICATION, Got: {result}")

            if passed:
                print(f"   Should ask: Single/multiplayer? Graphics library? Difficulty?")
            print()

    def test_medium_games(self):
        """Test medium complexity games."""
        print("=" * 80)
        print("CATEGORY 5: Medium Complexity Games (10 tests)")
        print("Expected: ASK_CLARIFICATION with detailed game questions")
        print("=" * 80 + "\n")

        test_cases = [
            ("build a platformer game", "Mario-style game"),
            ("create a tower defense game", "Strategy game"),
            ("develop a card battle game", "TCG-style"),
            ("build a racing game", "Top-down racer"),
            ("make a puzzle platformer", "Portal-style"),
            ("create a dungeon crawler", "Roguelike game"),
            ("build a rhythm game", "Music timing"),
            ("develop a turn-based RPG", "Classic JRPG"),
            ("create a sandbox building game", "Minecraft-lite"),
            ("build a physics puzzle game", "Angry Birds-style"),
        ]

        for query, description in test_cases:
            result = self.classify_query(query)
            passed = result == "ASK_CLARIFICATION"
            status = "✅" if passed else "❌"
            self.results.append((query, result, "ASK_CLARIFICATION", passed))
            print(f"{status} {description}: '{query}'")
            print(f"   Expected: ASK_CLARIFICATION, Got: {result}")

            if passed:
                print(f"   Should ask: Game engine? 2D/3D? Art style? Mechanics?")
                print(f"                Levels? Progression? Multiplayer?")
            print()

    def test_complex_games(self):
        """Test complex game builds."""
        print("=" * 80)
        print("CATEGORY 6: Complex Games (10 tests)")
        print("Expected: ASK_CLARIFICATION with comprehensive game questions")
        print("=" * 80 + "\n")

        test_cases = [
            ("build an MMORPG", "Massively multiplayer online"),
            ("create a battle royale game", "100-player PvP"),
            ("develop a real-time strategy game", "StarCraft-like"),
            ("build a 3D open-world RPG", "Skyrim-style"),
            ("create a multiplayer FPS", "Counter-Strike-like"),
            ("make a city-building simulation", "SimCity-style"),
            ("build a survival crafting game", "Rust-like"),
            ("develop a MOBA game", "League of Legends-style"),
            ("create a space simulation game", "Elite Dangerous-like"),
            ("build a narrative-driven adventure", "Telltale-style"),
        ]

        for query, description in test_cases:
            result = self.classify_query(query)
            passed = result == "ASK_CLARIFICATION"
            status = "✅" if passed else "❌"
            self.results.append((query, result, "ASK_CLARIFICATION", passed))
            print(f"{status} {description}: '{query}'")
            print(f"   Expected: ASK_CLARIFICATION, Got: {result}")

            if passed:
                print(f"   Should ask: Engine (Unity/Unreal)? Server architecture?")
                print(f"                Graphics quality? Platform? Team size? Budget?")
                print(f"                Timeline? Monetization? Anti-cheat?")
            print()

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        print("=" * 80)
        print("CATEGORY 7: Edge Cases (10 tests)")
        print("Expected: ASK_CLARIFICATION for all build variants")
        print("=" * 80 + "\n")

        test_cases = [
            ("build me an app", "Vague build request"),
            ("create something cool", "Very vague"),
            ("make a game", "No specifics"),
            ("I want to build a tool", "Indirect build request"),
            ("help me create an application", "Help + create"),
            ("can you build a system for me", "Polite build request"),
            ("let's develop a new app together", "Collaborative build"),
            ("I need you to implement a feature", "Implement request"),
            ("please design and build a website", "Design + build"),
            ("generate a web application", "Generate request"),
        ]

        for query, description in test_cases:
            result = self.classify_query(query)
            passed = result == "ASK_CLARIFICATION"
            status = "✅" if passed else "❌"
            self.results.append((query, result, "ASK_CLARIFICATION", passed))
            print(f"{status} {description}: '{query}'")
            print(f"   Expected: ASK_CLARIFICATION, Got: {result}")
            print()

    def print_summary(self):
        """Print comprehensive summary."""
        print("\n" + "=" * 80)
        print("BUILD COMPLEXITY TEST SUMMARY")
        print("=" * 80 + "\n")

        total = len(self.results)
        passed = sum(1 for _, _, _, p in self.results if p)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} {'❌' if failed > 0 else ''}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print()

        # Category breakdown
        categories = [
            ("Simple Apps", 0, 10),
            ("Medium Apps", 10, 20),
            ("Complex Apps", 20, 30),
            ("Simple Games", 30, 40),
            ("Medium Games", 40, 50),
            ("Complex Games", 50, 60),
            ("Edge Cases", 60, 70),
        ]

        print("Category Breakdown:")
        print("-" * 80)
        for name, start, end in categories:
            cat_results = self.results[start:end]
            cat_passed = sum(1 for _, _, _, p in cat_results if p)
            cat_total = len(cat_results)
            cat_rate = (cat_passed / cat_total * 100) if cat_total > 0 else 0
            status = "✅" if cat_passed == cat_total else "⚠️"
            print(f"{status} {name:20} {cat_passed:2}/{cat_total:2} ({cat_rate:5.1f}%)")
        print()

        # Show failures
        failures = [(q, g, e) for q, g, e, p in self.results if not p]
        if failures:
            print("Failed Tests:")
            print("-" * 80)
            for query, got, expected in failures:
                print(f"❌ '{query}'")
                print(f"   Expected: {expected}, Got: {got}")
            print()

        # Key insights
        print("=" * 80)
        print("KEY INSIGHTS")
        print("=" * 80 + "\n")

        insights = [
            (pass_rate == 100, f"Perfect classification ({pass_rate:.1f}%)"),
            (pass_rate >= 95, f"Excellent classification ({pass_rate:.1f}%)"),
            (failed == 0, "All build requests trigger ASK_CLARIFICATION"),
            (passed >= 60, "Strong Type B (build) detection"),
        ]

        for achieved, description in insights:
            status = "✅" if achieved else "⚠️"
            print(f"{status} {description}")
        print()

        # Expected behavior
        print("=" * 80)
        print("EXPECTED PRINCE BEHAVIOR")
        print("=" * 80 + "\n")

        print("When user says: 'build a todo app'")
        print("Prince should ASK:")
        print("  1. What features? (add, edit, delete, categories, etc.)")
        print("  2. Storage type? (local, cloud, database)")
        print("  3. UI framework? (React, Vue, vanilla JS)")
        print()

        print("When user says: 'create an MMORPG'")
        print("Prince should ASK:")
        print("  1. Game engine? (Unity, Unreal, custom)")
        print("  2. Server architecture? (authoritative, P2P, hybrid)")
        print("  3. Graphics quality? (realistic, stylized, pixel art)")
        print("  4. Platform? (PC, console, mobile)")
        print("  5. Team size? Budget? Timeline?")
        print("  6. Monetization? (F2P, premium, subscription)")
        print()

        print("Prince should NEVER:")
        print("  ❌ Immediately start generating code")
        print("  ❌ Make assumptions about requirements")
        print("  ❌ Skip clarification questions")
        print()

        # Final verdict
        print("=" * 80)
        if pass_rate == 100:
            print("🎉 PERFECT! All build requests correctly trigger ASK_CLARIFICATION!")
        elif pass_rate >= 95:
            print("✅ EXCELLENT! Nearly all builds trigger clarification questions.")
        elif pass_rate >= 90:
            print("✅ GOOD! Most builds trigger clarification questions.")
        else:
            print("⚠️  NEEDS IMPROVEMENT: Some builds not triggering clarification.")
        print("=" * 80 + "\n")

        return pass_rate >= 95


def main():
    """Run build complexity tests."""
    tester = BuildComplexityTest()
    tester.run_tests()

    # Return success if 95%+ pass rate
    passed = sum(1 for _, _, _, p in tester.results if p)
    total = len(tester.results)
    pass_rate = (passed / total * 100) if total > 0 else 0

    return 0 if pass_rate >= 95 else 1


if __name__ == "__main__":
    sys.exit(main())
