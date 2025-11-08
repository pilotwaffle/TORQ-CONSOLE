"""
Test Enhanced Prince Flowers via Maxim.ai Workflow Endpoint

This script calls your Maxim.ai workflow endpoint to test Enhanced Prince's behavior.

Endpoint: https://app.getmaxim.ai/workspace/cmhqimzv9007c11ofecpe69n1/workflow/endpoint/cmhqirw9e00aq11ofctjq7rp7

Usage:
1. Set your MAXIM_API_KEY environment variable
2. Run: python test_prince_maxim_endpoint.py
3. Review results
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import requests


@dataclass
class TestCase:
    """Represents a single test case for Enhanced Prince."""
    id: str
    name: str
    query: str
    expected_behavior: str  # "websearch", "ask_questions", "provide_options"
    expected_action: str  # "IMMEDIATE_ACTION", "ASK_CLARIFICATION", "PROVIDE_OPTIONS"
    should_generate_code: bool
    category: str
    severity: str = "normal"  # "normal", "critical"


class MaximEndpointTester:
    """Tests Enhanced Prince via Maxim.ai workflow endpoint."""

    def __init__(self, endpoint_url: str, api_key: Optional[str] = None):
        """
        Initialize tester.

        Args:
            endpoint_url: Maxim.ai workflow endpoint URL
            api_key: Optional API key (reads from env if not provided)
        """
        self.endpoint_url = endpoint_url
        self.api_key = api_key or os.getenv("MAXIM_API_KEY")
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })

    def create_test_cases(self) -> List[TestCase]:
        """Create test cases based on user's actual failures."""
        return [
            # CRITICAL: User's exact failure cases
            TestCase(
                id="critical_001",
                name="User's Exact Failure: Search AI News",
                query="Search the latest AI news 11/08/25",
                expected_behavior="websearch",
                expected_action="IMMEDIATE_ACTION",
                should_generate_code=False,
                category="type_a_research",
                severity="critical"
            ),
            TestCase(
                id="critical_002",
                name="Research Query That Failed",
                query="Research new updates coming to GLM-4.6",
                expected_behavior="websearch",
                expected_action="IMMEDIATE_ACTION",
                should_generate_code=False,
                category="type_a_research",
                severity="critical"
            ),
            TestCase(
                id="critical_003",
                name="Feedback Ignored Case",
                query="No that's not right",  # After wrong response
                expected_behavior="change_approach",
                expected_action="IMMEDIATE_ACTION",
                should_generate_code=False,
                category="feedback",
                severity="critical"
            ),

            # Type A: Research queries (should WebSearch)
            TestCase(
                id="type_a_001",
                name="Basic Search",
                query="search for top AI tools",
                expected_behavior="websearch",
                expected_action="IMMEDIATE_ACTION",
                should_generate_code=False,
                category="type_a_research"
            ),
            TestCase(
                id="type_a_002",
                name="Find Query",
                query="find the best React libraries",
                expected_behavior="websearch",
                expected_action="IMMEDIATE_ACTION",
                should_generate_code=False,
                category="type_a_research"
            ),
            TestCase(
                id="type_a_003",
                name="Show Me Query",
                query="show me trending GitHub repos",
                expected_behavior="websearch",
                expected_action="IMMEDIATE_ACTION",
                should_generate_code=False,
                category="type_a_research"
            ),
            TestCase(
                id="type_a_004",
                name="List Query",
                query="list top programming languages",
                expected_behavior="websearch",
                expected_action="IMMEDIATE_ACTION",
                should_generate_code=False,
                category="type_a_research"
            ),
            TestCase(
                id="type_a_005",
                name="Explore Query",
                query="explore AI agent frameworks",
                expected_behavior="websearch",
                expected_action="IMMEDIATE_ACTION",
                should_generate_code=False,
                category="type_a_research"
            ),

            # Type B: Build queries (should ask questions)
            TestCase(
                id="type_b_001",
                name="Build Todo App",
                query="build a todo app",
                expected_behavior="ask_questions",
                expected_action="ASK_CLARIFICATION",
                should_generate_code=False,  # Not immediately
                category="type_b_build"
            ),
            TestCase(
                id="type_b_002",
                name="Create Application",
                query="create an e-commerce site",
                expected_behavior="ask_questions",
                expected_action="ASK_CLARIFICATION",
                should_generate_code=False,
                category="type_b_build"
            ),
            TestCase(
                id="type_b_003",
                name="Build Game",
                query="build a tic-tac-toe game",
                expected_behavior="ask_questions",
                expected_action="ASK_CLARIFICATION",
                should_generate_code=False,
                category="type_b_build"
            ),
        ]

    def call_endpoint(self, query: str) -> Dict[str, Any]:
        """
        Call Maxim.ai workflow endpoint with query.

        Args:
            query: User query to test

        Returns:
            Response from endpoint
        """
        payload = {
            "query": query,
            "timestamp": time.time()
        }

        try:
            response = self.session.post(
                self.endpoint_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }

    def evaluate_response(self, test_case: TestCase, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate response against expected behavior.

        Args:
            test_case: Test case
            response: Agent response

        Returns:
            Evaluation results
        """
        result = {
            "test_id": test_case.id,
            "test_name": test_case.name,
            "query": test_case.query,
            "expected": test_case.expected_action,
            "severity": test_case.severity,
            "checks": {},
            "issues": [],
            "passed": False,
            "score": 0.0
        }

        # Handle error responses
        if "error" in response:
            result["issues"].append(f"Endpoint error: {response['error']}")
            return result

        # Extract agent response (adjust based on actual response format)
        agent_response = response.get("response", response.get("output", str(response)))
        agent_response_lower = str(agent_response).lower()

        # Check for code generation
        code_indicators = [
            "typescript", "javascript", "python", "```",
            "package.json", "npm install", "pip install",
            "class ", "function ", "interface ", "import "
        ]
        generated_code = any(ind in agent_response_lower for ind in code_indicators)

        # Check for WebSearch usage
        websearch_indicators = [
            "based on my search", "search results", "i found",
            "according to", "here are the", "sources:"
        ]
        used_websearch = any(ind in agent_response_lower for ind in websearch_indicators)

        # Check for questions
        has_questions = agent_response_lower.count("?") >= 2

        # Evaluate based on expected behavior
        if test_case.category.startswith("type_a"):
            # Type A: Should WebSearch, NOT generate code
            result["checks"]["used_websearch"] = used_websearch
            result["checks"]["generated_code"] = generated_code

            if not used_websearch:
                result["issues"].append("FAIL: Did not use WebSearch for research query")

            if generated_code:
                result["issues"].append("CRITICAL: Generated code for research query")

            score = 0.0
            if used_websearch:
                score += 0.7
            if not generated_code:
                score += 0.3

            result["score"] = score
            result["passed"] = score >= 0.7

        elif test_case.category.startswith("type_b"):
            # Type B: Should ask questions
            result["checks"]["asked_questions"] = has_questions
            result["checks"]["generated_code"] = generated_code

            if not has_questions:
                result["issues"].append("FAIL: Did not ask clarifying questions")

            if generated_code and not has_questions:
                result["issues"].append("WARNING: Generated code without asking questions")

            score = 0.0
            if has_questions:
                score += 0.8
            if not (generated_code and not has_questions):
                score += 0.2

            result["score"] = score
            result["passed"] = score >= 0.8

        result["response_preview"] = str(agent_response)[:200]
        return result

    def run_tests(self, test_cases: Optional[List[TestCase]] = None) -> Dict[str, Any]:
        """
        Run all test cases.

        Args:
            test_cases: Optional list of test cases (uses default if None)

        Returns:
            Test results summary
        """
        if test_cases is None:
            test_cases = self.create_test_cases()

        results = {
            "total": len(test_cases),
            "passed": 0,
            "failed": 0,
            "critical_failures": [],
            "test_results": []
        }

        print(f"\n{'='*80}")
        print(f"TESTING ENHANCED PRINCE VIA MAXIM.AI ENDPOINT")
        print(f"Endpoint: {self.endpoint_url[:60]}...")
        print(f"Tests: {len(test_cases)}")
        print(f"{'='*80}\n")

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] {test_case.name}")
            print(f"  Query: '{test_case.query}'")
            print(f"  Expected: {test_case.expected_action}")

            # Call endpoint
            print(f"  📡 Calling endpoint...")
            response = self.call_endpoint(test_case.query)

            # Evaluate
            evaluation = self.evaluate_response(test_case, response)
            results["test_results"].append(evaluation)

            if evaluation["passed"]:
                results["passed"] += 1
                print(f"  ✅ PASS (score: {evaluation['score']:.2f})")
            else:
                results["failed"] += 1
                print(f"  ❌ FAIL (score: {evaluation['score']:.2f})")
                for issue in evaluation["issues"]:
                    print(f"     • {issue}")

                if test_case.severity == "critical":
                    results["critical_failures"].append(evaluation)

            time.sleep(1)  # Rate limiting

        # Print summary
        self._print_summary(results)

        return results

    def _print_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}\n")

        print(f"Total Tests: {results['total']}")
        print(f"Passed: {results['passed']} ✅")
        print(f"Failed: {results['failed']} ❌")

        pass_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
        print(f"Pass Rate: {pass_rate:.1f}%\n")

        if results['critical_failures']:
            print(f"⚠️  CRITICAL FAILURES: {len(results['critical_failures'])}")
            for failure in results['critical_failures']:
                print(f"   • {failure['test_name']}")
                print(f"     Issues: {', '.join(failure['issues'])}")
            print()

        print(f"{'='*80}\n")


def main():
    """Main entry point."""
    # Your Maxim.ai workflow endpoint
    ENDPOINT_URL = "https://app.getmaxim.ai/workspace/cmhqimzv9007c11ofecpe69n1/workflow/endpoint/cmhqirw9e00aq11ofctjq7rp7"

    # Check for API key
    api_key = os.getenv("MAXIM_API_KEY")
    if not api_key:
        print("\n⚠️  MAXIM_API_KEY not found in environment")
        print("   Set it with: export MAXIM_API_KEY='your-key-here'\n")
        # Continue anyway - endpoint might not require it
        print("   Continuing without API key...\n")

    # Create tester
    tester = MaximEndpointTester(ENDPOINT_URL, api_key)

    # Run tests
    results = tester.run_tests()

    # Save results
    output_file = "maxim_test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"📄 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
