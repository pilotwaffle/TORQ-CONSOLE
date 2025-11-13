"""
Test Generation Agent for Enhanced Prince Flowers.

Automatically generates test cases based on:
- Failure analysis (learning from failed tests)
- Edge case discovery (boundary conditions)
- Adversarial scenarios (challenging queries)
- Pattern-based generation (query type variations)

This agent extends test coverage beyond manual test creation.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import re

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of generated tests."""
    EDGE_CASE = "edge_case"
    ADVERSARIAL = "adversarial"
    FAILURE_DERIVED = "failure_derived"
    PATTERN_VARIATION = "pattern_variation"
    BOUNDARY_CONDITION = "boundary_condition"


@dataclass
class GeneratedTest:
    """A generated test case."""
    query: str
    test_type: TestType
    category: str
    expected_behavior: Dict[str, Any]
    reasoning: str
    difficulty: float  # 0-1
    test_id: str


@dataclass
class TestGenerationResult:
    """Result of test generation."""
    generated_tests: List[GeneratedTest]
    total_generated: int
    by_type: Dict[str, int]
    by_category: Dict[str, int]
    generation_time: float


class TestGenerationAgent:
    """
    Agent that generates test cases automatically.

    Features:
    - Learn from failed tests to generate similar edge cases
    - Create adversarial scenarios
    - Generate boundary condition tests
    - Pattern-based query variations
    """

    def __init__(self):
        self.logger = logging.getLogger('TestGenerationAgent')

        # Test patterns by category
        self.patterns = {
            "debate": {
                "comparison": [
                    "What's better: {a} or {b}?",
                    "Compare {a} vs {b} for {context}",
                    "Which is more suitable: {a} or {b}?",
                    "Should I choose {a} or {b}?",
                    "{a} versus {b}: which one?",
                ],
                "decision": [
                    "Should I use {a}?",
                    "Is {a} better than {b}?",
                    "Would {a} be appropriate for {context}?",
                    "Is it worth using {a}?",
                    "When should I use {a} over {b}?",
                ],
            },
            "complex": {
                "multi_part": [
                    "{action1} and then {action2}",
                    "First {action1}, also {action2}",
                    "{action1}, {action2}, and finally {action3}",
                ],
                "conditional": [
                    "If {condition}, should I {action}?",
                    "When {condition}, what about {action}?",
                ],
            },
            "planning": {
                "build": [
                    "Build {system} with {feature1} and {feature2}",
                    "Create {system} that includes {feature1}",
                    "Design {system} with {constraint}",
                ],
            },
        }

        # Vocabulary for generation
        self.vocabulary = {
            "technologies": [
                "Python", "JavaScript", "TypeScript", "Rust", "Go",
                "React", "Vue", "Angular", "Svelte",
                "Docker", "Kubernetes", "Terraform",
                "PostgreSQL", "MongoDB", "Redis", "Cassandra",
                "GraphQL", "REST", "gRPC",
                "AWS", "Azure", "GCP",
                "Node.js", "Django", "FastAPI", "Express",
            ],
            "systems": [
                "API", "microservice", "database", "cache",
                "message queue", "load balancer", "monitoring system",
                "authentication system", "search engine", "analytics platform",
            ],
            "features": [
                "authentication", "authorization", "rate limiting",
                "caching", "monitoring", "logging", "error handling",
                "data validation", "API versioning", "documentation",
            ],
            "contexts": [
                "web applications", "mobile apps", "enterprise systems",
                "real-time applications", "microservices", "data pipelines",
                "high-traffic systems", "distributed systems",
            ],
        }

        # Edge case patterns
        self.edge_cases = [
            # Very short queries
            "Help",
            "Yes",
            "No",
            "Why?",

            # Very long queries (100+ words)
            "single_word_repeated",

            # Empty/whitespace
            "",
            "   ",
            "\n\n\n",

            # Special characters
            "!@#$%^&*()",
            "<<<<<>>>>>",

            # Numbers only
            "12345",
            "0.123",

            # Mixed languages (if applicable)
            # Code snippets
            "def func(): pass",

            # Ambiguous queries
            "What about it?",
            "Can you?",
            "Tell me more",
        ]

        # Adversarial patterns
        self.adversarial_patterns = [
            "contradictory_instructions",
            "impossible_requirements",
            "circular_logic",
            "extreme_constraints",
            "conflicting_goals",
        ]

    async def generate_tests(
        self,
        failed_tests: Optional[List[Dict]] = None,
        num_tests: int = 50,
        categories: Optional[List[str]] = None
    ) -> TestGenerationResult:
        """
        Generate test cases automatically.

        Args:
            failed_tests: Previously failed tests to learn from
            num_tests: Number of tests to generate
            categories: Specific categories to focus on

        Returns:
            TestGenerationResult with generated tests
        """
        import time
        start_time = time.time()

        generated_tests = []

        # 1. Generate from failures (if provided)
        if failed_tests:
            failure_tests = await self._generate_from_failures(failed_tests)
            generated_tests.extend(failure_tests)
            self.logger.info(f"Generated {len(failure_tests)} tests from failures")

        # 2. Generate edge cases
        edge_tests = await self._generate_edge_cases(num_tests // 4)
        generated_tests.extend(edge_tests)
        self.logger.info(f"Generated {len(edge_tests)} edge case tests")

        # 3. Generate adversarial scenarios
        adversarial_tests = await self._generate_adversarial(num_tests // 4)
        generated_tests.extend(adversarial_tests)
        self.logger.info(f"Generated {len(adversarial_tests)} adversarial tests")

        # 4. Generate pattern variations
        remaining = num_tests - len(generated_tests)
        pattern_tests = await self._generate_pattern_variations(remaining, categories)
        generated_tests.extend(pattern_tests)
        self.logger.info(f"Generated {len(pattern_tests)} pattern variation tests")

        # Calculate statistics
        by_type = {}
        by_category = {}
        for test in generated_tests:
            by_type[test.test_type.value] = by_type.get(test.test_type.value, 0) + 1
            by_category[test.category] = by_category.get(test.category, 0) + 1

        generation_time = time.time() - start_time

        return TestGenerationResult(
            generated_tests=generated_tests,
            total_generated=len(generated_tests),
            by_type=by_type,
            by_category=by_category,
            generation_time=generation_time
        )

    async def _generate_from_failures(
        self,
        failed_tests: List[Dict]
    ) -> List[GeneratedTest]:
        """Generate tests similar to failed tests to explore failure boundaries."""
        generated = []

        for idx, failed_test in enumerate(failed_tests[:10]):  # Limit to 10
            query = failed_test.get("query", "")
            category = failed_test.get("category", "unknown")
            failure_reason = failed_test.get("reason", "")

            # Generate variations
            variations = self._create_query_variations(query)

            for var_idx, variation in enumerate(variations[:3]):  # 3 variations each
                test = GeneratedTest(
                    query=variation,
                    test_type=TestType.FAILURE_DERIVED,
                    category=category,
                    expected_behavior={
                        "should_pass": True,
                        "derived_from": query,
                        "original_failure": failure_reason
                    },
                    reasoning=f"Variation of failed test to explore failure boundary",
                    difficulty=0.8,
                    test_id=f"fail_derived_{idx}_{var_idx}"
                )
                generated.append(test)

        return generated

    async def _generate_edge_cases(self, num_tests: int) -> List[GeneratedTest]:
        """Generate edge case tests (boundary conditions)."""
        generated = []

        edge_scenarios = [
            # Length boundaries
            ("Help", "basic", "Minimal query (1 word)", 0.3),
            ("What is machine learning and how does it work and what are the applications?", "complex", "Long query (no punctuation)", 0.5),

            # Empty/whitespace
            ("", "basic", "Empty query", 0.9),
            ("   ", "basic", "Whitespace only", 0.9),

            # Special characters
            ("What is AI???", "basic", "Multiple punctuation", 0.4),
            ("Compare A vs. B (in detail)", "debate", "Parenthetical clause", 0.5),

            # Numbers
            ("What is 2+2?", "basic", "Simple math", 0.3),
            ("Explain algorithm with O(n log n) complexity", "complex", "Technical notation", 0.6),

            # Ambiguous
            ("Tell me about it", "basic", "Ambiguous reference", 0.7),
            ("What about that?", "basic", "Vague query", 0.8),
            ("Can you?", "basic", "Incomplete question", 0.9),

            # Code-like
            ("def hello(): print('hi')", "basic", "Code snippet", 0.6),
            ("SELECT * FROM users WHERE id = 1", "basic", "SQL query", 0.6),

            # Mixed case / formatting
            ("wHaT iS pYtHoN", "basic", "Mixed case", 0.4),
            ("SHOULD I USE DOCKER", "debate", "All caps", 0.4),
        ]

        for idx, (query, category, reasoning, difficulty) in enumerate(edge_scenarios[:num_tests]):
            test = GeneratedTest(
                query=query,
                test_type=TestType.EDGE_CASE,
                category=category,
                expected_behavior={
                    "should_handle_gracefully": True,
                    "min_quality": 0.5
                },
                reasoning=reasoning,
                difficulty=difficulty,
                test_id=f"edge_{idx}"
            )
            generated.append(test)

        return generated

    async def _generate_adversarial(self, num_tests: int) -> List[GeneratedTest]:
        """Generate adversarial test scenarios."""
        generated = []

        adversarial_scenarios = [
            # Contradictory instructions
            ("Build a simple yet complex system", "planning", "Contradictory requirements", 0.8),
            ("Make it fast but don't optimize", "planning", "Conflicting goals", 0.8),

            # Impossible requirements
            ("Create a zero-latency distributed system", "planning", "Physically impossible", 0.9),
            ("Build infinitely scalable system with no resources", "planning", "Resource contradiction", 0.9),

            # Circular logic
            ("Which is better: the better one or the worse one?", "debate", "Circular reasoning", 0.7),
            ("Should I use the tool I should use?", "debate", "Self-referential", 0.8),

            # Extreme constraints
            ("Build enterprise system in 1 line of code", "planning", "Extreme constraint", 0.9),
            ("Explain quantum physics in 3 words", "complex", "Extreme brevity", 0.8),

            # Conflicting context
            ("I love Python but hate Python, should I use it?", "debate", "Contradictory preferences", 0.7),
            ("Build secure system with no security features", "planning", "Contradictory specification", 0.9),

            # Nonsensical comparisons
            ("Is Docker better than Tuesday?", "debate", "Category error", 0.9),
            ("Compare databases to feelings", "debate", "Type mismatch", 0.9),

            # Recursive/infinite
            ("Explain how to explain things", "basic", "Meta-recursive", 0.6),
            ("What is the definition of definition?", "basic", "Self-defining", 0.6),
        ]

        for idx, (query, category, reasoning, difficulty) in enumerate(adversarial_scenarios[:num_tests]):
            test = GeneratedTest(
                query=query,
                test_type=TestType.ADVERSARIAL,
                category=category,
                expected_behavior={
                    "should_detect_issue": True,
                    "should_not_crash": True,
                    "min_confidence": 0.5
                },
                reasoning=reasoning,
                difficulty=difficulty,
                test_id=f"adversarial_{idx}"
            )
            generated.append(test)

        return generated

    async def _generate_pattern_variations(
        self,
        num_tests: int,
        categories: Optional[List[str]] = None
    ) -> List[GeneratedTest]:
        """Generate tests using pattern variations."""
        generated = []
        categories = categories or ["debate", "complex", "planning"]

        for idx in range(num_tests):
            category = random.choice(categories)

            if category == "debate":
                test = self._generate_debate_test(idx)
            elif category == "complex":
                test = self._generate_complex_test(idx)
            elif category == "planning":
                test = self._generate_planning_test(idx)
            else:
                continue

            generated.append(test)

        return generated

    def _generate_debate_test(self, idx: int) -> GeneratedTest:
        """Generate a debate-category test."""
        pattern_type = random.choice(["comparison", "decision"])
        pattern = random.choice(self.patterns["debate"][pattern_type])

        tech_a = random.choice(self.vocabulary["technologies"])
        tech_b = random.choice([t for t in self.vocabulary["technologies"] if t != tech_a])
        context = random.choice(self.vocabulary["contexts"])

        query = pattern.format(a=tech_a, b=tech_b, context=context)

        return GeneratedTest(
            query=query,
            test_type=TestType.PATTERN_VARIATION,
            category="debate",
            expected_behavior={
                "should_activate_debate": True,
                "min_consensus": 0.5
            },
            reasoning=f"Pattern-based {pattern_type} query",
            difficulty=0.5,
            test_id=f"debate_pattern_{idx}"
        )

    def _generate_complex_test(self, idx: int) -> GeneratedTest:
        """Generate a complex-category test."""
        pattern_type = random.choice(["multi_part", "conditional"])
        pattern = random.choice(self.patterns["complex"][pattern_type])

        if pattern_type == "multi_part":
            action1 = f"explain {random.choice(self.vocabulary['technologies'])}"
            action2 = f"compare it to {random.choice(self.vocabulary['technologies'])}"
            action3 = f"recommend for {random.choice(self.vocabulary['contexts'])}"
            query = pattern.format(action1=action1, action2=action2, action3=action3)
        else:
            condition = f"working with {random.choice(self.vocabulary['contexts'])}"
            action = f"use {random.choice(self.vocabulary['technologies'])}"
            query = pattern.format(condition=condition, action=action)

        return GeneratedTest(
            query=query,
            test_type=TestType.PATTERN_VARIATION,
            category="complex",
            expected_behavior={
                "min_quality": 0.6
            },
            reasoning=f"Pattern-based {pattern_type} query",
            difficulty=0.6,
            test_id=f"complex_pattern_{idx}"
        )

    def _generate_planning_test(self, idx: int) -> GeneratedTest:
        """Generate a planning-category test."""
        pattern = random.choice(self.patterns["planning"]["build"])

        system = random.choice(self.vocabulary["systems"])
        feature1 = random.choice(self.vocabulary["features"])
        feature2 = random.choice([f for f in self.vocabulary["features"] if f != feature1])
        constraint = f"for {random.choice(self.vocabulary['contexts'])}"

        query = pattern.format(system=system, feature1=feature1, feature2=feature2, constraint=constraint)

        return GeneratedTest(
            query=query,
            test_type=TestType.PATTERN_VARIATION,
            category="planning",
            expected_behavior={
                "should_use_planning": True,
                "min_quality": 0.6
            },
            reasoning="Pattern-based build query",
            difficulty=0.6,
            test_id=f"planning_pattern_{idx}"
        )

    def _create_query_variations(self, query: str) -> List[str]:
        """Create variations of a query."""
        variations = []

        # Rephrase variations
        if "?" in query:
            variations.append(query.replace("?", ""))
        else:
            variations.append(query + "?")

        # Add context
        variations.append(f"For web development: {query}")

        # Simplify
        words = query.split()
        if len(words) > 5:
            variations.append(" ".join(words[:len(words)//2]))

        # Make more specific
        variations.append(query.replace("system", "microservice"))

        return variations[:3]


# Global instance
_test_generation_agent: Optional[TestGenerationAgent] = None


def get_test_generation_agent() -> TestGenerationAgent:
    """Get or create global test generation agent."""
    global _test_generation_agent

    if _test_generation_agent is None:
        _test_generation_agent = TestGenerationAgent()

    return _test_generation_agent
