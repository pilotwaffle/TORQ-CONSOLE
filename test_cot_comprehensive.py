#!/usr/bin/env python3
"""
Comprehensive Test Suite for TORQ Console Chain-of-Thought (CoT) Reasoning Framework

This test suite validates all components of the CoT implementation:
- Core framework (ReasoningStep, ReasoningChain, CoTReasoning)
- Templates (ResearchTemplate, AnalysisTemplate, DecisionTemplate, Phase templates)
- Validator (CoTValidator and validation rules)
- Enhancers (PerplexityCoTEnhancer, AgentCoTEnhancer, SpecKitCoTEnhancer)
"""

import asyncio
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, Any, List

# Test imports
try:
    from torq_console.reasoning.core import (
        CoTReasoning, ReasoningStep, ReasoningChain,
        ReasoningType, StepStatus
    )
    from torq_console.reasoning.templates import (
        ResearchTemplate, AnalysisTemplate, DecisionTemplate,
        Phase1SpecTemplate, Phase2AdaptiveTemplate,
        Phase3EcosystemTemplate, Phase4AutonomousTemplate
    )
    from torq_console.reasoning.validator import (
        CoTValidator, ValidationSeverity, ValidationResult
    )
    from torq_console.reasoning.enhancers import (
        PerplexityCoTEnhancer, AgentCoTEnhancer, SpecKitCoTEnhancer,
        enhance_perplexity_search, enhance_agent_task, enhance_spec_kit_operation
    )
except ImportError as e:
    print(f"ERROR: Could not import CoT modules: {e}")
    sys.exit(1)


class CoTTestSuite:
    """Comprehensive test suite for CoT reasoning framework."""

    def __init__(self):
        """Initialize the test suite."""
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        self.start_time = None
        self.verbose = True

    def log(self, message: str, level: str = "INFO"):
        """Log a test message."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    async def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and record results."""
        self.log(f"Running test: {test_name}")
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func(*args, **kwargs)
            else:
                result = test_func(*args, **kwargs)

            end_time = time.time()
            execution_time = end_time - start_time

            if result:
                self.tests_passed += 1
                self.log(f"[PASS] PASSED: {test_name} ({execution_time:.3f}s)", "PASS")
            else:
                self.tests_failed += 1
                self.log(f"[FAIL] FAILED: {test_name} ({execution_time:.3f}s)", "FAIL")

            self.test_results.append({
                "name": test_name,
                "passed": result,
                "execution_time": execution_time,
                "error": None
            })

            return result

        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time

            self.tests_failed += 1
            self.log(f"[ERROR] ERROR: {test_name} - {str(e)} ({execution_time:.3f}s)", "ERROR")

            if self.verbose:
                self.log(f"Traceback: {traceback.format_exc()}", "DEBUG")

            self.test_results.append({
                "name": test_name,
                "passed": False,
                "execution_time": execution_time,
                "error": str(e)
            })

            return False

    # ========== CORE FRAMEWORK TESTS ==========

    async def test_core_reasoning_step(self) -> bool:
        """Test ReasoningStep creation and execution."""
        try:
            # Test basic step creation
            step = ReasoningStep(
                step_id="test_step_001",
                description="Test reasoning step",
                reasoning="This step tests basic functionality",
                confidence=0.8
            )

            if step.step_id != "test_step_001":
                return False

            if step.status != StepStatus.PENDING:
                return False

            # Test step execution
            async def test_action(**kwargs):
                return {"result": "success", "value": 42}

            step.action = test_action
            success = await step.execute()

            if not success:
                return False

            if step.status != StepStatus.COMPLETED:
                return False

            if step.outputs.get("result") != "success":
                return False

            return True

        except Exception as e:
            self.log(f"Core reasoning step test failed: {e}")
            return False

    async def test_core_reasoning_chain(self) -> bool:
        """Test ReasoningChain creation and execution."""
        try:
            # Create chain
            chain = ReasoningChain(
                chain_id="test_chain_001",
                title="Test Chain",
                reasoning_type=ReasoningType.ANALYSIS
            )

            # Add steps
            step1 = ReasoningStep(
                step_id="step1",
                description="First step",
                reasoning="Initial processing",
                action=lambda **kwargs: {"step1_output": "completed"}
            )

            step2 = ReasoningStep(
                step_id="step2",
                description="Second step",
                reasoning="Depends on first step",
                dependencies=["step1"],
                action=lambda **kwargs: {"step2_output": "completed", "used_step1": kwargs.get("step1_output")}
            )

            chain.add_step(step1)
            chain.add_step(step2)

            # Execute chain
            success = await chain.execute()

            if not success:
                return False

            # Verify execution order
            if step1.status != StepStatus.COMPLETED:
                return False

            if step2.status != StepStatus.COMPLETED:
                return False

            # Verify dependency passing
            if step2.outputs.get("used_step1") != "completed":
                return False

            return True

        except Exception as e:
            self.log(f"Core reasoning chain test failed: {e}")
            return False

    async def test_core_cot_framework(self) -> bool:
        """Test CoTReasoning framework."""
        try:
            # Create framework
            cot = CoTReasoning()

            # Create chain
            chain = await cot.create_chain(
                chain_id="framework_test_001",
                title="Framework Test",
                reasoning_type=ReasoningType.RESEARCH,
                context={"test_context": "framework_test"}
            )

            if chain.chain_id != "framework_test_001":
                return False

            # Add a simple step
            step = ReasoningStep(
                step_id="framework_step",
                description="Framework test step",
                reasoning="Testing framework integration",
                action=lambda **kwargs: {"framework_result": "success"}
            )

            chain.add_step(step)

            # Execute through framework
            success = await cot.execute_chain("framework_test_001")

            if not success:
                return False

            # Verify history
            history = cot.get_execution_history()
            if len(history) != 1:
                return False

            return True

        except Exception as e:
            self.log(f"Core CoT framework test failed: {e}")
            return False

    # ========== TEMPLATE TESTS ==========

    async def test_research_template(self) -> bool:
        """Test ResearchTemplate functionality."""
        try:
            cot = CoTReasoning()
            template = ResearchTemplate()

            # Create research chain
            chain = await template.create_chain(
                cot_framework=cot,
                chain_id="research_test_001",
                context={
                    "query": "test research query",
                    "max_sources": 5,
                    "depth": "comprehensive"
                }
            )

            if len(chain.steps) == 0:
                return False

            # Verify expected steps exist
            expected_steps = ["analyze_query", "plan_research", "gather_information",
                            "validate_sources", "synthesize_information", "assess_quality"]

            actual_step_ids = [step.step_id for step in chain.steps]

            for expected_step in expected_steps:
                if expected_step not in actual_step_ids:
                    self.log(f"Missing expected step: {expected_step}")
                    return False

            # Execute chain
            success = await chain.execute()

            if not success:
                return False

            return True

        except Exception as e:
            self.log(f"Research template test failed: {e}")
            return False

    async def test_analysis_template(self) -> bool:
        """Test AnalysisTemplate functionality."""
        try:
            cot = CoTReasoning()
            template = AnalysisTemplate()

            # Create analysis chain
            chain = await template.create_chain(
                cot_framework=cot,
                chain_id="analysis_test_001",
                context={
                    "subject": "test analysis subject",
                    "type": "technical"
                }
            )

            if len(chain.steps) == 0:
                return False

            # Execute chain
            success = await chain.execute()

            if not success:
                return False

            return True

        except Exception as e:
            self.log(f"Analysis template test failed: {e}")
            return False

    async def test_decision_template(self) -> bool:
        """Test DecisionTemplate functionality."""
        try:
            cot = CoTReasoning()
            template = DecisionTemplate()

            # Create decision chain
            chain = await template.create_chain(
                cot_framework=cot,
                chain_id="decision_test_001",
                context={
                    "decision": "test decision scenario"
                }
            )

            if len(chain.steps) == 0:
                return False

            # Execute chain
            success = await chain.execute()

            if not success:
                return False

            return True

        except Exception as e:
            self.log(f"Decision template test failed: {e}")
            return False

    async def test_phase_templates(self) -> bool:
        """Test all phase-specific templates."""
        try:
            cot = CoTReasoning()

            # Test Phase 1 template
            phase1_template = Phase1SpecTemplate()
            phase1_chain = await phase1_template.create_chain(
                cot_framework=cot,
                chain_id="phase1_test_001",
                context={"type": "constitution"}
            )

            if len(phase1_chain.steps) == 0:
                return False

            # Test Phase 2 template
            phase2_template = Phase2AdaptiveTemplate()
            phase2_chain = await phase2_template.create_chain(
                cot_framework=cot,
                chain_id="phase2_test_001",
                context={}
            )

            if len(phase2_chain.steps) == 0:
                return False

            # Test Phase 3 template
            phase3_template = Phase3EcosystemTemplate()
            phase3_chain = await phase3_template.create_chain(
                cot_framework=cot,
                chain_id="phase3_test_001",
                context={}
            )

            if len(phase3_chain.steps) == 0:
                return False

            # Test Phase 4 template
            phase4_template = Phase4AutonomousTemplate()
            phase4_chain = await phase4_template.create_chain(
                cot_framework=cot,
                chain_id="phase4_test_001",
                context={}
            )

            if len(phase4_chain.steps) == 0:
                return False

            return True

        except Exception as e:
            self.log(f"Phase templates test failed: {e}")
            return False

    # ========== VALIDATOR TESTS ==========

    async def test_validator_basic(self) -> bool:
        """Test basic validator functionality."""
        try:
            validator = CoTValidator()

            # Create a simple valid chain
            cot = CoTReasoning()
            chain = await cot.create_chain(
                chain_id="validator_test_001",
                title="Validator Test",
                reasoning_type=ReasoningType.VALIDATION
            )

            step = ReasoningStep(
                step_id="validation_step",
                description="Test validation step",
                reasoning="This step tests validation functionality",
                confidence=0.8,
                action=lambda **kwargs: {"validation_result": "passed"}
            )

            chain.add_step(step)
            await chain.execute()

            # Validate the chain
            result = await validator.validate_chain(chain)

            if not isinstance(result, ValidationResult):
                return False

            if result.chain_id != "validator_test_001":
                return False

            if not result.is_valid:
                self.log(f"Chain validation failed: {result.issues}")
                return False

            return True

        except Exception as e:
            self.log(f"Validator basic test failed: {e}")
            return False

    async def test_validator_dependency_validation(self) -> bool:
        """Test validator dependency checking."""
        try:
            validator = CoTValidator()

            # Create chain with invalid dependency
            cot = CoTReasoning()
            chain = await cot.create_chain(
                chain_id="dependency_test_001",
                title="Dependency Test",
                reasoning_type=ReasoningType.VALIDATION
            )

            # Step with non-existent dependency
            step = ReasoningStep(
                step_id="dependent_step",
                description="Step with invalid dependency",
                reasoning="This step depends on a non-existent step",
                dependencies=["non_existent_step"],
                action=lambda **kwargs: {"result": "completed"}
            )

            chain.add_step(step)

            # Validate the chain (should find dependency issue)
            result = await validator.validate_chain(chain)

            if result.is_valid:
                self.log("Validator should have detected invalid dependency")
                return False

            # Check for dependency-related issues
            dependency_issues = [issue for issue in result.issues
                               if issue.category == "dependency"]

            if len(dependency_issues) == 0:
                self.log("Validator should have reported dependency issues")
                return False

            return True

        except Exception as e:
            self.log(f"Validator dependency test failed: {e}")
            return False

    # ========== ENHANCER TESTS ==========

    async def test_perplexity_enhancer(self) -> bool:
        """Test PerplexityCoTEnhancer functionality."""
        try:
            enhancer = PerplexityCoTEnhancer()

            # Test enhancement
            result = await enhancer.enhance({
                "query": "test perplexity query",
                "search_type": "web",
                "max_results": 5
            })

            if "search_results" not in result:
                return False

            if "reasoning" not in result:
                return False

            if "metadata" not in result:
                return False

            # Check reasoning quality
            reasoning = result["reasoning"]
            if "execution_success" not in reasoning:
                return False

            return True

        except Exception as e:
            self.log(f"Perplexity enhancer test failed: {e}")
            return False

    async def test_agent_enhancer(self) -> bool:
        """Test AgentCoTEnhancer functionality."""
        try:
            enhancer = AgentCoTEnhancer()

            # Test enhancement
            result = await enhancer.enhance({
                "task": "test agent task",
                "agent_type": "general",
                "context": {"test_context": "agent_test"}
            })

            if "agent_response" not in result:
                return False

            if "reasoning" not in result:
                return False

            if "metadata" not in result:
                return False

            return True

        except Exception as e:
            self.log(f"Agent enhancer test failed: {e}")
            return False

    async def test_speckit_enhancer(self) -> bool:
        """Test SpecKitCoTEnhancer functionality."""
        try:
            enhancer = SpecKitCoTEnhancer()

            # Test enhancement
            result = await enhancer.enhance({
                "operation": "create",
                "type": "specification",
                "content": {"test_spec": "content"}
            })

            if "spec_result" not in result:
                return False

            if "reasoning" not in result:
                return False

            if "metadata" not in result:
                return False

            return True

        except Exception as e:
            self.log(f"SpecKit enhancer test failed: {e}")
            return False

    async def test_enhancer_utility_functions(self) -> bool:
        """Test enhancer utility functions."""
        try:
            # Test Perplexity utility
            perplexity_result = await enhance_perplexity_search(
                query="test utility query",
                search_type="web",
                max_results=3
            )

            if "search_results" not in perplexity_result:
                return False

            # Test Agent utility
            agent_result = await enhance_agent_task(
                task="test utility task",
                agent_type="general"
            )

            if "agent_response" not in agent_result:
                return False

            # Test SpecKit utility
            speckit_result = await enhance_spec_kit_operation(
                operation="analyze",
                spec_type="specification"
            )

            if "spec_result" not in speckit_result:
                return False

            return True

        except Exception as e:
            self.log(f"Enhancer utility functions test failed: {e}")
            return False

    # ========== INTEGRATION TESTS ==========

    async def test_full_workflow_integration(self) -> bool:
        """Test complete CoT workflow integration."""
        try:
            # Create a full workflow using multiple components
            cot = CoTReasoning()
            validator = CoTValidator()

            # Use research template
            template = ResearchTemplate()
            chain = await template.create_chain(
                cot_framework=cot,
                chain_id="integration_test_001",
                context={
                    "query": "integration test query",
                    "max_sources": 10
                }
            )

            # Execute chain
            success = await chain.execute()
            if not success:
                return False

            # Validate results
            validation_result = await validator.validate_chain(chain)
            if not validation_result.is_valid:
                self.log(f"Integration validation failed: {validation_result.issues}")
                return False

            # Test with enhancer
            enhancer = PerplexityCoTEnhancer()
            enhanced_result = await enhancer.enhance({
                "query": "integration test query",
                "search_type": "web",
                "max_results": 5
            })

            if "search_results" not in enhanced_result:
                return False

            return True

        except Exception as e:
            self.log(f"Full workflow integration test failed: {e}")
            return False

    async def test_error_handling(self) -> bool:
        """Test error handling in CoT components."""
        try:
            # Test step with failing action
            async def failing_action(**kwargs):
                raise ValueError("Intentional test failure")

            step = ReasoningStep(
                step_id="failing_step",
                description="Step that fails",
                reasoning="This step is designed to fail",
                action=failing_action
            )

            success = await step.execute()

            # Should return False but not raise exception
            if success:
                return False

            if step.status != StepStatus.FAILED:
                return False

            if not step.error_message:
                return False

            return True

        except Exception as e:
            self.log(f"Error handling test failed: {e}")
            return False

    # ========== TEST EXECUTION ==========

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all CoT tests."""
        self.start_time = time.time()
        self.log("=" * 80)
        self.log("TORQ CONSOLE CHAIN-OF-THOUGHT (CoT) COMPREHENSIVE TEST SUITE")
        self.log("=" * 80)

        # Core framework tests
        self.log("\n[CORE] CORE FRAMEWORK TESTS")
        await self.run_test("Core ReasoningStep", self.test_core_reasoning_step)
        await self.run_test("Core ReasoningChain", self.test_core_reasoning_chain)
        await self.run_test("Core CoT Framework", self.test_core_cot_framework)

        # Template tests
        self.log("\n[TEMPLATE] TEMPLATE TESTS")
        await self.run_test("Research Template", self.test_research_template)
        await self.run_test("Analysis Template", self.test_analysis_template)
        await self.run_test("Decision Template", self.test_decision_template)
        await self.run_test("Phase Templates", self.test_phase_templates)

        # Validator tests
        self.log("\n[VALIDATOR] VALIDATOR TESTS")
        await self.run_test("Validator Basic", self.test_validator_basic)
        await self.run_test("Validator Dependencies", self.test_validator_dependency_validation)

        # Enhancer tests
        self.log("\n[ENHANCER] ENHANCER TESTS")
        await self.run_test("Perplexity Enhancer", self.test_perplexity_enhancer)
        await self.run_test("Agent Enhancer", self.test_agent_enhancer)
        await self.run_test("SpecKit Enhancer", self.test_speckit_enhancer)
        await self.run_test("Enhancer Utilities", self.test_enhancer_utility_functions)

        # Integration tests
        self.log("\n[INTEGRATION] INTEGRATION TESTS")
        await self.run_test("Full Workflow Integration", self.test_full_workflow_integration)
        await self.run_test("Error Handling", self.test_error_handling)

        # Generate summary
        total_time = time.time() - self.start_time
        total_tests = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0

        self.log("\n" + "=" * 80)
        self.log("TEST SUMMARY")
        self.log("=" * 80)
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {self.tests_passed}")
        self.log(f"Failed: {self.tests_failed}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        self.log(f"Total Time: {total_time:.3f}s")

        if self.tests_failed > 0:
            self.log("\n[FAILED] FAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    error_info = f" - {result['error']}" if result['error'] else ""
                    self.log(f"  * {result['name']}{error_info}")

        overall_success = self.tests_failed == 0
        self.log(f"\n[RESULT] OVERALL RESULT: {'SUCCESS' if overall_success else 'FAILURE'}")

        return {
            "success": overall_success,
            "total_tests": total_tests,
            "passed": self.tests_passed,
            "failed": self.tests_failed,
            "success_rate": success_rate,
            "execution_time": total_time,
            "results": self.test_results
        }


async def main():
    """Main test function."""
    test_suite = CoTTestSuite()
    results = await test_suite.run_all_tests()

    # Exit with proper code
    exit_code = 0 if results["success"] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())