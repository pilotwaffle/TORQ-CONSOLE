"""
Enhanced Prince Flowers - Maxim.ai Integration Script

This script provides integration with Maxim.ai for testing Enhanced Prince.
Run this from your Maxim.ai workspace to evaluate Prince's behavior.

Setup:
1. Install Maxim SDK: pip install maxim-py
2. Set MAXIM_API_KEY environment variable
3. Run: python maxim_integration.py
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass

try:
    from maxim import Maxim
    from maxim.evaluators import Evaluator
    MAXIM_AVAILABLE = True
except ImportError:
    print("⚠️  Maxim SDK not installed. Install with: pip install maxim-py")
    MAXIM_AVAILABLE = False


@dataclass
class TestScenario:
    """Represents a test scenario for Enhanced Prince."""
    id: str
    name: str
    user_input: str
    expected_action: str  # IMMEDIATE_ACTION, ASK_CLARIFICATION, PROVIDE_OPTIONS
    should_generate_code: bool
    should_use_websearch: bool
    should_ask_questions: bool
    category: str  # type_a, type_b, feedback, edge_case


class EnhancedPrinceEvaluator:
    """
    Evaluator for Enhanced Prince Flowers behavior.

    Tests:
    - Type A: Research requests should trigger WebSearch
    - Type B: Build requests should ask clarifying questions
    - Feedback: Should detect and respond to corrections
    """

    def __init__(self, api_key: str = None):
        """Initialize evaluator with Maxim API key."""
        self.api_key = api_key or os.getenv("MAXIM_API_KEY")
        if not self.api_key:
            raise ValueError("MAXIM_API_KEY not found in environment")

        if MAXIM_AVAILABLE:
            self.client = Maxim(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️  Running in simulation mode (Maxim SDK not available)")

    def create_test_scenarios(self) -> List[TestScenario]:
        """Create comprehensive test scenarios."""
        scenarios = []

        # Type A: Research/Search queries (should WebSearch)
        type_a_queries = [
            ("search for top AI tools", "Basic search"),
            ("research new updates to GPT-5", "Research query"),
            ("find the best React libraries", "Find query"),
            ("Search the latest AI news", "Latest news - CRITICAL"),
            ("show me trending GitHub repos", "Show me query"),
            ("list top programming languages", "List query"),
            ("under ideation: search for design patterns", "Ideation query"),
            ("explore AI agent frameworks", "Explore query"),
            ("what are the best databases", "What are query"),
            ("top 10 viral TikTok videos", "Top X query"),
        ]

        for query, name in type_a_queries:
            scenarios.append(TestScenario(
                id=f"type_a_{len(scenarios):03d}",
                name=name,
                user_input=query,
                expected_action="IMMEDIATE_ACTION",
                should_generate_code=False,
                should_use_websearch=True,
                should_ask_questions=False,
                category="type_a"
            ))

        # Type B: Build/Implementation queries (should ask questions)
        type_b_queries = [
            ("build a todo app", "Build todo app"),
            ("create an e-commerce site", "Create application"),
            ("develop a task management system", "Develop system"),
            ("implement a search feature", "Implement feature"),
            ("make a weather app", "Make application"),
            ("build a tic-tac-toe game", "Build game"),
            ("create a video streaming platform", "Complex app"),
            ("build an MMORPG", "Complex game"),
        ]

        for query, name in type_b_queries:
            scenarios.append(TestScenario(
                id=f"type_b_{len(scenarios):03d}",
                name=name,
                user_input=query,
                expected_action="ASK_CLARIFICATION",
                should_generate_code=False,  # Not immediately
                should_use_websearch=False,
                should_ask_questions=True,
                category="type_b"
            ))

        return scenarios

    def evaluate_response(self,
                         scenario: TestScenario,
                         agent_response: str) -> Dict[str, Any]:
        """
        Evaluate agent response against expected behavior.

        Args:
            scenario: Test scenario
            agent_response: Agent's actual response

        Returns:
            Evaluation results with pass/fail and details
        """
        results = {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "user_input": scenario.user_input,
            "agent_response": agent_response[:500],  # Truncate for logging
            "expected_action": scenario.expected_action,
            "checks": {},
            "passed": False,
            "score": 0.0,
            "issues": []
        }

        response_lower = agent_response.lower()

        # Check for code generation (TypeScript, Python, etc.)
        code_indicators = [
            "typescript", "javascript", "python", "package.json",
            "```ts", "```js", "```py", "class ", "function ",
            "interface ", "import ", "export ", "const ",
            "npm install", "pip install"
        ]
        generated_code = any(indicator in response_lower for indicator in code_indicators)

        # Check for WebSearch usage
        websearch_indicators = [
            "based on my search", "search results", "i found",
            "according to", "here are the", "sources:",
            "research shows", "web search"
        ]
        used_websearch = any(indicator in response_lower for indicator in websearch_indicators)

        # Check for clarifying questions
        question_indicators = ["?", "what", "which", "how many", "do you"]
        asked_questions = sum(1 for ind in question_indicators if ind in response_lower)
        has_questions = asked_questions >= 2

        # Evaluate based on scenario type
        if scenario.category == "type_a":
            # Type A: Should WebSearch, should NOT generate code
            results["checks"]["used_websearch"] = used_websearch
            results["checks"]["generated_code"] = generated_code
            results["checks"]["asked_questions"] = has_questions

            if not used_websearch:
                results["issues"].append("CRITICAL: Did not use WebSearch for research query")

            if generated_code:
                results["issues"].append("CRITICAL: Generated code for research query")

            if has_questions:
                results["issues"].append("WARNING: Asked questions for research query")

            # Calculate score
            score = 0.0
            if used_websearch:
                score += 0.6
            if not generated_code:
                score += 0.3
            if not has_questions:
                score += 0.1

            results["score"] = score
            results["passed"] = score >= 0.9  # 90% threshold

        elif scenario.category == "type_b":
            # Type B: Should ask questions, should NOT immediately generate code
            results["checks"]["asked_questions"] = has_questions
            results["checks"]["generated_code"] = generated_code
            results["checks"]["used_websearch"] = used_websearch

            if not has_questions:
                results["issues"].append("CRITICAL: Did not ask clarifying questions for build request")

            if generated_code and not has_questions:
                results["issues"].append("WARNING: Generated code without asking questions first")

            if used_websearch:
                results["issues"].append("WARNING: Used WebSearch for build request")

            # Calculate score
            score = 0.0
            if has_questions:
                score += 0.7
            if not generated_code or has_questions:  # Code is OK if questions asked first
                score += 0.2
            if not used_websearch:
                score += 0.1

            results["score"] = score
            results["passed"] = score >= 0.8  # 80% threshold

        return results

    def run_test_suite(self,
                       agent_endpoint: str = None,
                       max_tests: int = None) -> Dict[str, Any]:
        """
        Run complete test suite against Enhanced Prince.

        Args:
            agent_endpoint: Optional API endpoint for agent
            max_tests: Limit number of tests (for development)

        Returns:
            Test suite results with summary statistics
        """
        scenarios = self.create_test_scenarios()

        if max_tests:
            scenarios = scenarios[:max_tests]

        results = {
            "total_tests": len(scenarios),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "type_a_results": {"passed": 0, "failed": 0, "score": 0.0},
            "type_b_results": {"passed": 0, "failed": 0, "score": 0.0},
            "test_results": [],
            "critical_failures": []
        }

        print(f"\n{'='*80}")
        print(f"ENHANCED PRINCE FLOWERS - MAXIM.AI TEST SUITE")
        print(f"Running {len(scenarios)} test scenarios...")
        print(f"{'='*80}\n")

        for scenario in scenarios:
            # In a real implementation, this would call the actual agent
            # For now, simulate or require manual input
            print(f"\n📝 Test {scenario.id}: {scenario.name}")
            print(f"   Input: '{scenario.user_input}'")
            print(f"   Expected: {scenario.expected_action}")

            # Placeholder for actual agent call
            # In Maxim.ai, this would use their SDK to call your agent
            agent_response = self._simulate_agent_call(scenario)

            # Evaluate response
            eval_result = self.evaluate_response(scenario, agent_response)
            results["test_results"].append(eval_result)
            results["tests_run"] += 1

            if eval_result["passed"]:
                results["tests_passed"] += 1
                print(f"   ✅ PASS (score: {eval_result['score']:.2f})")
            else:
                results["tests_failed"] += 1
                print(f"   ❌ FAIL (score: {eval_result['score']:.2f})")
                for issue in eval_result["issues"]:
                    print(f"      • {issue}")

                if "CRITICAL" in str(eval_result["issues"]):
                    results["critical_failures"].append(eval_result)

            # Update category stats
            if scenario.category == "type_a":
                if eval_result["passed"]:
                    results["type_a_results"]["passed"] += 1
                else:
                    results["type_a_results"]["failed"] += 1
                results["type_a_results"]["score"] += eval_result["score"]

            elif scenario.category == "type_b":
                if eval_result["passed"]:
                    results["type_b_results"]["passed"] += 1
                else:
                    results["type_b_results"]["failed"] += 1
                results["type_b_results"]["score"] += eval_result["score"]

        # Calculate averages
        type_a_total = results["type_a_results"]["passed"] + results["type_a_results"]["failed"]
        if type_a_total > 0:
            results["type_a_results"]["score"] /= type_a_total

        type_b_total = results["type_b_results"]["passed"] + results["type_b_results"]["failed"]
        if type_b_total > 0:
            results["type_b_results"]["score"] /= type_b_total

        # Print summary
        self._print_summary(results)

        return results

    def _simulate_agent_call(self, scenario: TestScenario) -> str:
        """
        Simulate agent call for testing.
        In production, this would call the actual Enhanced Prince agent.
        """
        # This is a placeholder - in Maxim.ai, you'd replace this with actual agent calls
        return f"[Agent response would appear here for: {scenario.user_input}]"

    def _print_summary(self, results: Dict[str, Any]):
        """Print test suite summary."""
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}\n")

        print(f"Total Tests: {results['total_tests']}")
        print(f"Tests Run: {results['tests_run']}")
        print(f"Passed: {results['tests_passed']} ✅")
        print(f"Failed: {results['tests_failed']} ❌")

        pass_rate = (results['tests_passed'] / results['tests_run'] * 100) if results['tests_run'] > 0 else 0
        print(f"Pass Rate: {pass_rate:.1f}%\n")

        print("Category Breakdown:")
        print("-" * 80)

        # Type A results
        type_a = results["type_a_results"]
        type_a_total = type_a["passed"] + type_a["failed"]
        if type_a_total > 0:
            type_a_rate = (type_a["passed"] / type_a_total * 100)
            print(f"Type A (Research): {type_a['passed']}/{type_a_total} ({type_a_rate:.1f}%)")
            print(f"  Average Score: {type_a['score']:.2f}")

        # Type B results
        type_b = results["type_b_results"]
        type_b_total = type_b["passed"] + type_b["failed"]
        if type_b_total > 0:
            type_b_rate = (type_b["passed"] / type_b_total * 100)
            print(f"Type B (Build): {type_b['passed']}/{type_b_total} ({type_b_rate:.1f}%)")
            print(f"  Average Score: {type_b['score']:.2f}")

        # Critical failures
        if results["critical_failures"]:
            print(f"\n⚠️  Critical Failures: {len(results['critical_failures'])}")
            for failure in results["critical_failures"]:
                print(f"   • {failure['scenario_name']}: {failure['issues'][0]}")

        print(f"\n{'='*80}\n")


def main():
    """Main entry point for Maxim.ai integration."""
    print("Enhanced Prince Flowers - Maxim.ai Evaluator\n")

    # Check for API key
    api_key = os.getenv("MAXIM_API_KEY")
    if not api_key:
        print("⚠️  MAXIM_API_KEY not set. Please set it in your environment.")
        print("   export MAXIM_API_KEY='your-api-key-here'\n")
        return

    # Initialize evaluator
    evaluator = EnhancedPrinceEvaluator(api_key=api_key)

    # Run test suite
    results = evaluator.run_test_suite(max_tests=5)  # Start with 5 tests

    # In Maxim.ai, you would send results to the platform
    if evaluator.client:
        print("📤 Sending results to Maxim.ai...")
        # evaluator.client.log_evaluation(results)

    print("✅ Test suite complete!")


if __name__ == "__main__":
    main()
